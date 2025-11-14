# src/cli/pages/user.py

from cli.ui import (
    session,
    ask_int,
    ask_optional,
    ask_yes_no,
    BackCommand,
    QuitCommand,
    reset_session,
    ensure_logged_in,
)
from cli.context import user_service


def page_user_home() -> None:
    if not ensure_logged_in():
        return
    while True:
        print("\n=== Espace utilisateur ===")
        print("1) Mon compte")
        print("2) Gestion des conversations")
        print("3) Nouvelle conversation")
        print("4) Rejoindre une collaboration")
        print("9) Deconnexion")
        print("0) Quitter")
        try:
            choice = ask_int("Votre choix", [1, 2, 3, 4, 9, 0])
        except BackCommand:
            return
        if choice == 1:
            page_account()
        elif choice == 2:
            from cli.pages import conversations
            conversations.page_manage()
        elif choice == 3:
            from cli.pages import conversations
            conversations.create_conversation()
        elif choice == 4:
            from cli.pages import collaboration
            collaboration.page_join_collab()
        elif choice == 9:
            print("Deconnexion effectuee.")
            reset_session()
            return
        elif choice == 0:
            raise QuitCommand()


def page_account() -> None:
    if not ensure_logged_in():
        return
    while True:
        try:
            user = user_service.get_user_by_id(session.current_user_id)
        except Exception as exc:
            print(f"Impossible de charger le compte: {exc}")
            return
        if not user:
            print("Utilisateur introuvable.")
            reset_session()
            return
        print("\n=== Mon compte ===")
        print(f"ID: {user.id}")
        print(f"Email: {user.mail}")
        print(f"Nom: {user.nom}")
        print(f"Prenom: {user.prenom}")
        print(f"Pseudo: {user.username}")
        print(f"Statut: {user.status}")
        print(f"Parametre: {user.setting_param}")
        print("1) Modifier mes informations")
        print("2) Supprimer mon compte")
        print("9) Retour")
        print("0) Quitter")
        try:
            choice = ask_int("Votre choix", [1, 2, 9, 0])
        except BackCommand:
            return
        if choice == 1:
            update_account(user.id)
        elif choice == 2:
            if ask_yes_no("Confirmer la suppression du compte ?"):
                try:
                    user_service.delete_user(user.id)
                except Exception as exc:
                    print(f"Echec de suppression: {exc}")
                else:
                    print("Compte supprime. Retour a l'accueil.")
                    reset_session()
                    return
        elif choice == 9:
            return
        elif choice == 0:
            raise QuitCommand()


def update_account(user_id: int) -> None:
    print("\n--- Modification du profil ---")
    print("Laisser vide pour conserver la valeur actuelle.")
    try:
        mail = ask_optional("Nouvel email")
        username = ask_optional("Nouveau pseudo")
        nom = ask_optional("Nouveau nom")
        prenom = ask_optional("Nouveau prenom")
        setting_param = ask_optional("Nouveau parametre assistant")
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
        print(f"Echec de mise a jour: {exc}")
        return
    print("Profil mis a jour.")
