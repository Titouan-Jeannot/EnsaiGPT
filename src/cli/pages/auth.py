# src/cli/pages/auth.py

from cli.ui import (
    ask_nonempty,
    ask_optional,
    ask_yes_no,
    BackCommand,
    QuitCommand,
    session,
    reset_session,
    ensure_logged_in,
)
from cli.context import user_service

import questionary
from questionary import Choice, Separator


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
    print(f"✅ Connexion réussie. Bonjour {session.current_username} !")

    from cli.pages import user as user_pages
    user_pages.page_user_home()


def page_register() -> None:
    print("\n=== Création de compte ===")
    try:
        username = ask_nonempty("Nom d'utilisateur")
        nom = ask_optional("Nom (optionnel)")
        prenom = ask_optional("Prénom (optionnel)")
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
        print(f"❌ Échec de création : {exc}")
        return
    print("✅ Compte créé avec succès. Vous pouvez maintenant vous connecter.")


def page_guest_home() -> None:
    """
    Page d'accueil du mode invité, avec menu déroulant (flèches + Entrée)
    au lieu d'un simple choix numérique.
    """

    session.is_guest = True

    while True:
        action = questionary.select(
            "\n=== Mode invité ===\nCertaines actions exigent un compte utilisateur.",
            choices=[
                Choice("🤝 Rejoindre une collaboration", "join_collab"),
                Separator(),
                Choice("⬅️ Retour à l'accueil", "back_home"),
                Choice("❌ Quitter", "quit"),
            ],
        ).ask()

        # Si l'utilisateur annule (Ctrl+C, fermeture du prompt)
        if action is None:
            # On considère que ça équivaut à un retour à l'accueil
            session.is_guest = False
            return

        if action == "join_collab":
            from cli.pages import collaboration

            try:
                collaboration.page_join_collab()
            except BackCommand:
                # On revient simplement au menu invité
                continue

        elif action == "back_home":
            session.is_guest = False
            return

        elif action == "quit":
            raise QuitCommand()
