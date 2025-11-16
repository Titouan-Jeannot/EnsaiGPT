# src/cli/pages/collaboration.py

from cli.ui import (
    ask_int,
    ask_nonempty,
    ask_yes_no,
    BackCommand,
)
from cli.context import collab_service, user_service, conv_service
from cli.ui import print_table
from cli.ui import session


def page_join_collab() -> None:
    if session.current_user_id is None:
        print("Un compte est requis pour rejoindre une collaboration.")
        return
    print("\n--- Rejoindre une collaboration ---")
    try:
        conv_id = ask_int("Identifiant de conversation", [])
        token = ask_nonempty("Token de collaboration")
    except BackCommand:
        return
    try:
        ok = collab_service.add_collab_by_token(conv_id, token, session.current_user_id)
    except Exception as exc:
        print(f"Echec d'ajout: {exc}")
        return
    if not ok:
        print("Token invalide ou acces refuse.")
        return
    print("Collaboration ajoutee.")
    from cli.pages import conversation_detail
    conversation_detail.page_conversation(conv_id)


def show_collaborators(conv_id: int) -> None:
    if session.current_user_id is None:
        print("Veuillez vous connecter pour consulter les collaborateurs.")
        return
    try:
        collaborators = collab_service.list_collaborators_for_user(
            conv_id, session.current_user_id
        )
    except PermissionError as exc:
        print(f"Acces refuse: {exc}")
        return
    except Exception as exc:
        print(f"Impossible de lister les collaborateurs: {exc}")
        return
    rows = []
    for collab in collaborators or []:
        username = ""
        try:
            user = user_service.get_user_by_id(collab.id_user)
            if user:
                username = user.username
        except Exception:
            username = ""
        rows.append(
            {
                "CollabID": getattr(collab, "id_collaboration", ""),
                "UserID": collab.id_user,
                "Pseudo": username,
                "Role": collab.role,
            }
        )
    print_table(rows, ["CollabID", "UserID", "Pseudo", "Role"])

    try:
        is_admin = collab_service.is_admin(session.current_user_id, conv_id)
    except Exception:
        is_admin = False
    if not is_admin:
        print("Seuls les administrateurs peuvent modifier les collaborateurs.")
        return

    try:
        manage = ask_yes_no("Modifier un collaborateur ?")
    except BackCommand:
        return
    if not manage:
        return
    try:
        target_user = ask_int("ID utilisateur cible", [])
    except BackCommand:
        return
    print("1) Changer le role")
    print("2) Supprimer")
    print("9) Annuler")
    try:
        choice = ask_int("Action", [1, 2, 9])
    except BackCommand:
        return
    if choice == 1:
        try:
            new_role = ask_nonempty("Nouveau role (admin/writer/viewer/banni)")
        except BackCommand:
            return
        try:
            updated = collab_service.change_role(
                conv_id, target_user, new_role, session.current_user_id
            )
        except Exception as exc:
            print(f"Echec du changement de role: {exc}")
            return
        print("Role mis a jour." if updated else "Aucun changement effectue.")
    elif choice == 2:
        try:
            deleted = collab_service.delete_collaborator(
                conv_id, target_user, session.current_user_id
            )
        except Exception as exc:
            print(f"Echec de suppression: {exc}")
            return
        print("Collaborateur supprime." if deleted else "Suppression non effectuee.")
    elif choice == 9:
        return


def share_conversation(conv_id: int) -> None:
    if session.current_user_id is None:
        print("Veuillez vous connecter pour partager une conversation.")
        return
    try:
        if not collab_service.is_admin(session.current_user_id, conv_id):
            print("Seuls les administrateurs peuvent partager cette conversation.")
            return
    except Exception as exc:
        print(f"Impossible de verifier vos droits: {exc}")
        return
    try:
        conversation = conv_service.get_conversation_by_id(
            conv_id, session.current_user_id
        )
    except Exception as exc:
        print(f"Impossible de charger la conversation: {exc}")
        return
    if not conversation:
        print("Conversation introuvable.")
        return
    print(f"Token lecture : {conversation.token_viewer}")
    print(f"Token ecriture : {conversation.token_writter}")
    try:
        target_user = ask_int("ID utilisateur a inviter", [])
        can_write = ask_yes_no("Autoriser l'ecriture ?")
    except BackCommand:
        return
    try:
        conv_service.share_conversation(
            conv_id, session.current_user_id, target_user, can_write
        )
    except Exception as exc:
        print(f"Partage impossible: {exc}")
        return
    print("Conversation partagee.")
