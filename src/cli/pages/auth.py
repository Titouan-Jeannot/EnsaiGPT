# src/cli/pages/auth.py

from cli.ui import (
    ask_nonempty,
    ask_optional,
    ask_int,
    ask_yes_no,
    BackCommand,
    QuitCommand,
    session,
    reset_session,
    ensure_logged_in,
)
from cli.context import user_service


def page_login() -> None:
    print("\n=== Connexion ===")
    try:
        mail = ask_nonempty("Email")
        password = ask_nonempty("Mot de passe")
    except BackCommand:
        return

    try:
        user = user_service.authenticate_user(mail, password)
        if not user:
            print("Identifiants invalides.")
            return
    except Exception as e:
        print(f"Erreur interne lors de la connexion : {e}")
        return

    session.current_user_id = getattr(user, "id", None)
    session.current_username = getattr(user, "username", "Utilisateur")
    session.current_conv_id = None
    session.is_guest = False
    print(f"Connexion reussie. Bonjour {session.current_username}!")

    from cli.pages import user as user_pages
    user_pages.page_user_home()


def page_register() -> None:
    print("\n=== Creation de compte ===")
    try:
        username = ask_nonempty("Nom d'utilisateur")
        nom = ask_optional("Nom (optionnel)")
        prenom = ask_optional("Prenom (optionnel)")
        mail = ask_nonempty("Email")
        password = ask_nonempty("Mot de passe")
    except BackCommand:
        return
    try:
        user_service.create_user(
            mail=mail,
            password_plain=password,
            username=username,
            nom=nom or "",
            prenom=prenom or "",
        )
    except Exception as exc:
        print(f"Echec de creation: {exc}")
        return
    print("Compte cree avec succes. Vous pouvez maintenant vous connecter.")


def page_guest_home() -> None:
    print("\n=== Mode invite ===")
    print("Certaines actions exigent un compte utilisateur.")
    print("1) Rejoindre une collaboration")
    print("9) Retour accueil")
    print("0) Quitter")
    try:
        choice = ask_int("Votre choix", [1, 9, 0])
    except BackCommand:
        return
    if choice == 1:
        from cli.pages import collaboration
        collaboration.page_join_collab()
    elif choice == 9:
        session.is_guest = False
        return
    elif choice == 0:
        raise QuitCommand()
