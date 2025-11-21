# src/cli/pages/home.py

from cli.ui import ask_menu, BackCommand, QuitCommand


def _go_login():
    from cli.pages.auth import page_login
    page_login()


def _go_register():
    from cli.pages.auth import page_register
    page_register()


def _go_invitee():
    from cli.pages.invitee import page_invitee
    page_invitee()


def page_home() -> None:
    """Page d'accueil principale."""
    while True:
        try:
            choix = ask_menu(
                title="Accueil",
                subtitle="Bienvenue sur EnsaiGPT",
                options=[
                    ("Connexion", "login"),
                    ("Création de compte", "register"),
                    ("Mode invité", "invite"),
                    ("Quitter l'application", "quit"),
                ],
            )
        except BackCommand:
            # retour impossible → on reste sur la page d'accueil
            continue

        if choix == "login":
            _go_login()

        elif choix == "register":
            _go_register()

        elif choix == "invite":
            _go_invitee()

        elif choix == "quit":
            raise QuitCommand()
