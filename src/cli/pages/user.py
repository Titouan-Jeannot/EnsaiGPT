# src/cli/pages/user.py

from cli.ui import (
    session,
    ask_optional,
    ask_yes_no,
    BackCommand,
    QuitCommand,
    reset_session,
    ensure_logged_in,
)
from cli.context import user_service

import questionary
from questionary import Choice, Separator


def page_user_home() -> None:
    if not ensure_logged_in():
        return

    while True:
        action = questionary.select(
            f"\n=== Espace utilisateur ===\nConnecté en tant que : {session.current_username}",
            choices=[
                Choice("👤 Mon compte", "account"),
                Choice("💬 Gestion des conversations", "manage_convs"),
                Choice("🆕 Nouvelle conversation", "new_conv"),
                Choice("🤝 Rejoindre une collaboration", "join_collab"),
                Separator(),
                Choice("🔓 Déconnexion", "logout"),
                Choice("❌ Quitter", "quit"),
            ],
        ).ask()

        if action is None:
            # On considère un Ctrl+C comme un retour en arrière
            return

        if action == "account":
            page_account()

        elif action == "manage_convs":
            from cli.pages import conversations
            conversations.page_manage()

        elif action == "new_conv":
            from cli.pages import conversations
            conversations.create_conversation()

        elif action == "join_collab":
            from cli.pages import collaboration
            collaboration.page_join_collab()

        elif action == "logout":
            print("✅ Déconnexion effectuée.")
            reset_session()
            return

        elif action == "quit":
            raise QuitCommand()


def page_account() -> None:
    if not ensure_logged_in():
        return

    while True:
        try:
            user = user_service.get_user_by_id(session.current_user_id)
        except Exception as exc:
            print(f"❌ Impossible de charger le compte : {exc}")
            return

        if not user:
            print("❌ Utilisateur introuvable.")
            reset_session()
            return

        # Affichage des infos du compte
        print("\n=== Mon compte ===")
        print(f"🆔 ID        : {user.id}")
        print(f"📧 Email     : {user.mail}")
        print(f"👤 Nom       : {user.nom}")
        print(f"🧍 Prénom    : {user.prenom}")
        print(f"🏷️ Pseudo    : {user.username}")
        print(f"📌 Statut    : {user.status}")
        print(f"⚙️ Paramètre : {user.setting_param}")

        action = questionary.select(
            "\nQue souhaites-tu faire ?",
            choices=[
                Choice("✏️ Modifier mes informations", "edit"),
                Choice("🗑️ Supprimer mon compte", "delete"),
                Separator(),
                Choice("⬅️ Retour", "back"),
                Choice("❌ Quitter", "quit"),
            ],
        ).ask()

        if action is None or action == "back":
            return

        if action == "edit":
            update_account(user.id)

        elif action == "delete":
            try:
                if ask_yes_no("Confirmer la suppression du compte ?"):
                    try:
                        user_service.delete_user(user.id)
                    except Exception as exc:
                        print(f"❌ Échec de suppression : {exc}")
                    else:
                        print("✅ Compte supprimé. Retour à l'accueil.")
                        reset_session()
                        return
            except BackCommand:
                # Annulation de la confirmation
                continue

        elif action == "quit":
            raise QuitCommand()


def update_account(user_id: int) -> None:
    print("\n--- Modification du profil ---")
    print("Laisser vide pour conserver la valeur actuelle.")
    try:
        mail = ask_optional("Nouvel email")
        username = ask_optional("Nouveau pseudo")
        nom = ask_optional("Nouveau nom")
        prenom = ask_optional("Nouveau prénom")
        setting_param = ask_optional("Nouveau paramètre assistant")
        from cli.ui import ask_nonempty
        change_password = ask_yes_no("Modifier le mot de passe ?")
        password = None
        if change_password:
            password = ask_nonempty("Nouveau mot de passe")
    except BackCommand:
        return

    try:
        user_service.update_user(
            user_id=user_id,
            mail=mail,
            username=username,
            nom=nom,
            prenom=prenom,
            setting_param=setting_param,
            password_plain=password,
        )
    except Exception as exc:
        print(f"❌ Échec de mise à jour : {exc}")
        return

    print("✅ Profil mis à jour.")
