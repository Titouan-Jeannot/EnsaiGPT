# src/cli/ui.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


class BackCommand(Exception):
    """Commande /back pour revenir en arriere."""
    pass


class QuitCommand(Exception):
    """Commande /quit pour quitter l'application."""
    pass


@dataclass
class Session:
    current_user_id: Optional[int] = None
    current_username: Optional[str] = None
    current_conv_id: Optional[int] = None
    is_guest: bool = False


# Session globale de l'application CLI
session = Session()


def safe_input(prompt: str) -> str:
    """Encapsule input en capturant les interruptions."""
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print()
        raise QuitCommand()
    except EOFError:
        print()
        raise QuitCommand()


def check_special_command(raw: str) -> None:
    """Interprete les commandes speciales /back et /quit."""
    value = raw.strip().lower()
    if value == "/back":
        raise BackCommand()
    if value == "/quit":
        raise QuitCommand()


def ask_int(prompt: str, choices: List[int]) -> int:
    """Demande un entier appartenant a choices (ou sans restriction si liste vide)."""
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
            options = ", ".join(str(c) for c in sorted(allowed))
            print(f"Choix non valide. Options: {options}.")
            continue
        return value


def ask_nonempty(prompt: str) -> str:
    """Demande une chaine non vide."""
    while True:
        raw = safe_input(f"{prompt} ").strip()
        check_special_command(raw)
        if raw:
            return raw
        print("Ce champ est obligatoire.")


def ask_optional(prompt: str) -> Optional[str]:
    """Demande une chaine optionnelle (vide -> None)."""
    raw = safe_input(f"{prompt} ").strip()
    check_special_command(raw)
    return raw or None


def ask_yes_no(prompt: str) -> bool:
    """Demande une reponse oui/non."""
    while True:
        raw = safe_input(f"{prompt} (y/n) ").strip().lower()
        check_special_command(raw)
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Merci de repondre par y ou n.")


def ask_date(prompt: str) -> datetime:
    """Demande une date au format AAAA-MM-JJ."""
    while True:
        raw = safe_input(f"{prompt} (AAAA-MM-JJ) ").strip()
        check_special_command(raw)
        try:
            return datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            print("Format invalide. Exemple: 2024-05-12.")


def print_table(rows: List[dict], headers: List[str]) -> None:
    """Affiche un tableau en monospace simple."""
    if not rows:
        print("Aucune donnee.")
        return
    widths = {header: len(header) for header in headers}
    for row in rows:
        for header in headers:
            widths[header] = max(widths[header], len(str(row.get(header, ""))))
    header_line = " | ".join(header.ljust(widths[header]) for header in headers)
    separator = "-+-".join("-" * widths[header] for header in headers)
    print(header_line)
    print(separator)
    for row in rows:
        print(
            " | ".join(str(row.get(header, "")).ljust(widths[header]) for header in headers)
        )


def reset_session() -> None:
    """Reinitialise la session utilisateur."""
    session.current_user_id = None
    session.current_username = None
    session.current_conv_id = None
    session.is_guest = False


def ensure_logged_in() -> bool:
    """Verifie qu'un utilisateur est connecte."""
    if session.current_user_id is None:
        print("Veuillez vous connecter pour acceder a cette fonctionnalite.")
        return False
    return True
