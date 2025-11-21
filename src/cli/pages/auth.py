# src/cli/pages/auth.py

from cli.ui import (
    ask_nonempty,
    ask_optional,
    ask_menu,
    BackCommand,
    QuitCommand,
    session,
)
from cli.context import user_service, auth_service


# ---------------------------------------------------------------------------
# Navigation interne (imports locaux pour éviter les cycles)
# ---------------------------------------------------------------------------

def _go_home() -> None:
    """Retour au menu d'accueil."""
    from cli.pages.home import page_home
    page_home()


def _go_user_home() -> None:
    """Aller à l'espace utilisateur."""
    from cli.pages.user import page_user_home
    page_user_home()


def _go_join_collab() -> None:
    """Aller à la page de join collaboration."""
    from cli.pages.collaboration import page_join_collab
    page_join_collab()


# ---------------------------------------------------------------------------
# Connexion
# ---------------------------------------------------------------------------

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
            _go_home()
            return

        status = getattr(user, "status", "active")
        if status == "banni":
            print("Votre compte a été banni. Connexion impossible.")
            _go_home()
            return
        if status == "deleted":
            print("Votre compte a été supprimé. Connexion impossible.")
            _go_home()
            return

    except Exception as e:
        print(f"Erreur interne lors de la connexion : {e}")
        _go_home()
        return

    # Mise à jour de la session
    session.current_user_id = getattr(user, "id", None)
    session.current_username = getattr(user, "username", "Utilisateur")
    session.current_conv_id = None
    session.is_guest = False

    print(f"Connexion reussie. Bonjour {session.current_username}!")
    _go_user_home()


# ---------------------------------------------------------------------------
# Inscription
# ---------------------------------------------------------------------------

def page_register() -> None:
    """Page de création de compte utilisateur."""
    print("\n=== Creation de compte ===")

    # Username
    while True:
        try:
            username = ask_nonempty("Nom d'utilisateur").strip()
            try:
                auth_service.check_user_username(None, username)
                break
            except ValueError as ve:
                print(f"Nom d'utilisateur invalide: {ve}")
        except BackCommand:
            return

    # Nom
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

    # Prénom
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

    # Email
    while True:
        try:
            mail = ask_nonempty("Email").strip().lower()
            try:
                auth_service.check_user_email(None, mail)
                break
            except ValueError as ve:
                print(f"Email invalide: {ve}")
        except BackCommand:
            return

    # Mot de passe
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

    # Création en base
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


# ---------------------------------------------------------------------------
# Mode invité
# ---------------------------------------------------------------------------

def page_guest_home() -> None:
    """Page d'accueil en mode invité."""
    session.is_guest = True

    try:
        choix = ask_menu(
            title="Mode invite",
            subtitle="Certaines actions exigent un compte utilisateur.",
            options=[
                ("Rejoindre une collaboration", "join_collab"),
                ("Retour accueil", "home"),
                ("Quitter l'application", "quit"),
            ],
        )
    except BackCommand:
        # Retour au menu appelant
        session.is_guest = False
        return

    if choix == "join_collab":
        _go_join_collab()

    elif choix == "home":
        session.is_guest = False
        _go_home()

    elif choix == "quit":
        raise QuitCommand()
