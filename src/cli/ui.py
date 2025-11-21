from __future__ import annotations

import sys
import termios
import tty
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple


# ----------------------------------------------------
# Exceptions de navigation
# ----------------------------------------------------
class BackCommand(Exception):
    """Lancé quand l'utilisateur veut revenir en arrière (/back ou 'b')."""
    pass


class QuitCommand(Exception):
    """Lancé quand l'utilisateur veut quitter l'appli (/quit ou 'q')."""
    pass


# ----------------------------------------------------
# Session globale
# ----------------------------------------------------
@dataclass
class Session:
    current_user_id: Optional[int] = None
    current_username: Optional[str] = None
    current_conv_id: Optional[int] = None
    is_guest: bool = False


session = Session()


# ----------------------------------------------------
# Entrée sécurisée + commandes spéciales
# ----------------------------------------------------
def safe_input(prompt: str) -> str:
    """Encapsule input en capturant Ctrl+C / EOF."""
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print()
        raise QuitCommand()
    except EOFError:
        print()
        raise QuitCommand()


def check_special_command(raw: str) -> None:
    """Interprète /back et /quit partout où on tape du texte."""
    value = raw.strip().lower()
    if value == "/back":
        raise BackCommand()
    if value == "/quit":
        raise QuitCommand()


# ----------------------------------------------------
# Questions typées
# ----------------------------------------------------
def ask_int(prompt: str, choices: List[int]) -> int:
    """
    Demande un entier appartenant à choices
    (ou sans restriction si la liste est vide).
    """
    allowed = set(choices)
    while True:
        raw = safe_input(f"{prompt} ").strip()
        check_special_command(raw)

        try:
            value = int(raw)
        except ValueError:
            print("Veuillez saisir un nombre entier valide.")
            continue

        if allowed and value not in allowed:
            opts = ", ".join(str(c) for c in sorted(allowed))
            print(f"Choix non valide. Options : {opts}.")
            continue

        return value


def ask_nonempty(prompt: str) -> str:
    """Demande une chaîne non vide."""
    while True:
        raw = safe_input(f"{prompt} ").strip()
        check_special_command(raw)

        if raw:
            return raw
        print("Ce champ est obligatoire.")


def ask_optional(prompt: str) -> Optional[str]:
    """Demande une chaîne optionnelle (vide -> None)."""
    raw = safe_input(f"{prompt} ").strip()
    check_special_command(raw)
    return raw or None


def ask_yes_no(prompt: str) -> bool:
    """Demande une réponse oui/non."""
    while True:
        raw = safe_input(f"{prompt} (y/n) ").strip().lower()
        check_special_command(raw)

        if raw in {"y", "yes", "o", "oui"}:
            return True
        if raw in {"n", "no", "non"}:
            return False

        print("Merci de répondre par y/n.")


def ask_date(prompt: str) -> datetime:
    """Demande une date au format AAAA-MM-JJ."""
    while True:
        raw = safe_input(f"{prompt} (AAAA-MM-JJ) ").strip()
        check_special_command(raw)
        try:
            return datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            print("Format invalide. Exemple : 2024-05-12.")


# ----------------------------------------------------
# Bas niveau : lecture d'une touche (pour les flèches)
# ----------------------------------------------------
def _getch() -> str:
    """
    Lit un caractère sur stdin sans attendre Enter.
    Gère également les séquences ESC [ A/B (flèches).
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        # Flèches : ESC [ A/B...
        if ch == "\x1b":
            ch += sys.stdin.read(2)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# ----------------------------------------------------
# Menu déroulant avec flèches (↑/↓ + Entrée)
# ----------------------------------------------------
def ask_menu(
    title: str,
    subtitle: Optional[str],
    options: List[Tuple[str, str]],
    clear_screen: bool = False,   # accepté pour compat, mais ignoré
    header: Optional[str] = None, # texte optionnel affiché avant le menu
) -> str:
    """
    Affiche un menu déroulant avec navigation via ↑/↓ ou k/j et validation avec Entrée.

    - options : liste de (label_affiché, valeur_retournée)
    - retourne : valeur_retournée (la "key") de l'option choisie
    - b -> BackCommand
    - q -> QuitCommand
    - ESC -> BackCommand
    """

    if not options:
        raise ValueError("ask_menu: aucune option fournie")

    index = 0

    while True:
        # IMPORTANT : on NE FAIT PAS de clear()
        # donc tout l'historique (messages, prints, etc.) reste visible/scrollable.

        print()  # petite séparation visuelle

        if header:
            print(header)
            print()

        print(f"=== {title} ===")
        if subtitle:
            print(subtitle)
        print()

        for i, (label, key) in enumerate(options):
            selected = (i == index)
            prefix = "👉" if selected else "  "
            marker = "[*]" if selected else "[ ]"
            print(f"{prefix} {marker} {label}")

        print(
            "\n↑/↓ ou k/j pour naviguer, Entrée pour valider, "
            "b pour revenir, q pour quitter."
        )

        ch = _getch()

        # Flèche haut : ESC [ A ou 'k'
        if ch in ("\x1b[A", "k"):
            index = (index - 1) % len(options)
            continue

        # Flèche bas : ESC [ B ou 'j'
        if ch in ("\x1b[B", "j"):
            index = (index + 1) % len(options)
            continue

        # Entrée
        if ch in ("\n", "\r"):
            _, key = options[index]
            return key

        # Retour
        if ch in ("b", "B"):
            raise BackCommand()

        # Quitter
        if ch in ("q", "Q"):
            raise QuitCommand()

        # ESC simple -> on le traite comme un retour
        if ch == "\x1b":
            raise BackCommand()

        # Autres touches : ignorées, on réaffiche juste un menu plus bas.


# ----------------------------------------------------
# Tableaux
# ----------------------------------------------------
def print_table(rows: List[Dict[str, Any]], headers: List[str]) -> None:
    """Affiche un tableau en monospace simple."""
    if not rows:
        print("Aucune donnée.")
        return

    widths = {h: len(h) for h in headers}
    for row in rows:
        for h in headers:
            widths[h] = max(widths[h], len(str(row.get(h, ""))))

    header_line = " | ".join(h.ljust(widths[h]) for h in headers)
    separator = "-+-".join("-" * widths[h] for h in headers)

    print(header_line)
    print(separator)

    for row in rows:
        print(" | ".join(str(row.get(h, "")).ljust(widths[h]) for h in headers))


# ----------------------------------------------------
# Session helpers
# ----------------------------------------------------
def reset_session() -> None:
    """Réinitialise la session utilisateur."""
    session.current_user_id = None
    session.current_username = None
    session.current_conv_id = None
    session.is_guest = False


def ensure_logged_in() -> bool:
    """Vérifie qu'un utilisateur est connecté."""
    if session.current_user_id is None:
        print("Veuillez vous connecter pour accéder à cette fonctionnalité.")
        return False
    return True
