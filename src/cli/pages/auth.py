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
from cli.context import user_service, user_dao, auth_service
from cli.pages import home
from cli.pages import collaboration
from cli.pages import user as user_pages


def page_login() -> None:
    """Page de connexion utilisateur."""
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
            home.page_home()
            return
        if getattr(user, "status", "active") == "banni":
            print("Votre compte a été banni. Connexion impossible.")
            home.page_home()
            return
        if getattr(user, "status", "active") == "deleted":
            print("Votre compte a été supprimé. Connexion impossible.")
            home.page_home()
            return
    except Exception as e:
        print(f"Erreur interne lors de la connexion : {e}")
        home.page_home()
        return

    session.current_user_id = getattr(user, "id", None)
    session.current_username = getattr(user, "username", "Utilisateur")
    session.current_conv_id = None
    session.is_guest = False
    print(f"Connexion reussie. Bonjour {session.current_username}!")
    user_pages.page_user_home()


def page_register() -> None:
    """Page de création de compte utilisateur."""
    print("\n=== Creation de compte ===")

    while True:
        try:
            username = ask_nonempty("Nom d'utilisateur")
            username = username.strip()
            try:
                auth_service.check_user_username(None, username)
                break
            except ValueError as ve:
                print(f"Nom d'utilisateur invalide: {ve}")

        except BackCommand:
            return
    while True:
        try:
            nom = ask_optional("Nom (optionnel)")
            try:
                auth_service.check_user_nom(None, nom)
                break
            except ValueError as ve:
                print(f"Nom invalide: {ve}")
        except BackCommand:
            return
    while True:
        try:
            prenom = ask_optional("Prenom (optionnel)")
            try:
                auth_service.check_user_prenom(None, prenom)
                break
            except ValueError as ve:
                print(f"Prenom invalide: {ve}")
        except BackCommand:
            return
    while True:
        try:
            mail = ask_nonempty("Email")
            mail = mail.strip().lower()
            try:
                auth_service.check_user_email(None, mail)
                break
            except ValueError as ve:
                print(f"Email invalide: {ve}")
        except BackCommand:
            return
    while True:
        try:
            password = ask_nonempty("Mot de passe")
            try:
                auth_service.check_user_password_strength(password)
                break
            except ValueError as ve:
                print(f"Mot de passe invalide: {ve}")
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
    """Page d'accueil en mode invité."""
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
        collaboration.page_join_collab()
    elif choice == 9:
        session.is_guest = False
        return
    elif choice == 0:
        raise QuitCommand()
