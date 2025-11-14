# src/cli/pages/home.py

from src.cli.ui import ask_int, BackCommand, QuitCommand, session
from src.cli.pages import auth  # import non-circulaire car auth n'importe pas home


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
        session.is_guest = True
        session.current_user_id = None
        session.current_username = "Invite"
        auth.page_guest_home()
    elif choice == 0:
        raise QuitCommand()
