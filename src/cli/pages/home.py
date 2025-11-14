# src/cli/pages/home.py

from cli.ui import ask_int, BackCommand, QuitCommand, session
from cli.pages import auth  # OK : sous-module auth, pas de cycle ici

def page_home() -> None:
    print("\n=== Accueil ===")
    print("1) Connexion")
    print("2) Creation de compte")
    print("3) Mode invite")
    print("0) Quitter")
    try:
        choice = ask_int("Votre choix", [1, 2, 3, 0])
    except BackCommand:
        return

    if choice == 1:
        auth.page_login()
    elif choice == 2:
        auth.page_register()
    elif choice == 3:
        # import LOCAL pour éviter l'import circulaire
        from cli.pages.invitee import page_invitee
        page_invitee()
    elif choice == 0:
        raise QuitCommand()
