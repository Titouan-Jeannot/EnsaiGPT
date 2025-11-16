# src/cli/pages/collaboration.py

from cli.ui import (
    ask_int,
    ask_nonempty,
    ask_yes_no,
    BackCommand,
)
from cli.context import collab_service, collab_dao, user_service
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
    try:
        collaborators = collab_dao.find_by_conversation(conv_id)
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
    from cli.context import collab_service as cs
    if choice == 1:
        try:
            new_role = ask_nonempty("Nouveau role (admin/writer/viewer/banni)")
        except BackCommand:
            return
        try:
            ok = cs.change_role(conv_id, target_user, new_role)
        except Exception as exc:
            print(f"Echec du changement de role: {exc}")
            return
        print("Role mis a jour." if ok else "Mise a jour non effectuee.")
    elif choice == 2:
        try:
            ok = cs.delete_collaborator(conv_id, target_user)
        except Exception as exc:
            print(f"Echec de suppression: {exc}")
            return
        print("Collaborateur supprime." if ok else "Suppression non effectuee.")
    elif choice == 9:
        return


def share_conversation(conv_id: int) -> None:
    try:
        target_user = ask_int("ID utilisateur a inviter", [])
        can_write = ask_yes_no("Autoriser l'ecriture ?")
    except BackCommand:
        return
    from cli.context import conv_service
    try:
        conv_service.share_conversation(
            conv_id, session.current_user_id, target_user, can_write
        )
    except Exception as exc:
        print(f"Partage impossible: {exc}")
        return
    print("Conversation partagee.")
