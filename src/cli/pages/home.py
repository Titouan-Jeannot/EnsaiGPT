# src/cli/pages/home.py

from __future__ import annotations

import questionary
from questionary import Choice, Separator

from cli.ui import BackCommand, QuitCommand, session  # ask_int supprimé
from cli.pages import auth  # OK : sous-module auth, pas de cycle ici


def page_home() -> None:
    """
    Menu d'accueil avec un select (flèches + Entrée) au lieu d'un input numérique.
    """

    while True:
        try:
            action = questionary.select(
                "\n=== Accueil EnsaiGPT ===\nQue souhaites-tu faire ?",
                choices=[
                    Choice("🔐 Connexion", "login"),
                    Choice("📝 Création de compte", "register"),
                    Choice("🎭 Mode invité", "guest"),
                    Separator(),
                    Choice("❌ Quitter", "quit"),
                ],
            ).ask()

            # Si l'utilisateur fait Ctrl+C ou ferme le prompt
            if action is None:
                # Ici on considère que ça équivaut à "Quitter"
                raise QuitCommand()

            if action == "login":
                auth.page_login()

            elif action == "register":
                auth.page_register()

            elif action == "guest":
                # Import local pour éviter les imports circulaires
                from cli.pages.invitee import page_invitee

                try:
                    page_invitee()
                except BackCommand:
                    # Retour au menu d'accueil
                    continue

            elif action == "quit":
                raise QuitCommand()

        except BackCommand:
            # Si un sous-menu décide de remonter d'un niveau
            return