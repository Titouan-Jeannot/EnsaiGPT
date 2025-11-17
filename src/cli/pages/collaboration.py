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

import questionary
from questionary import Choice, Separator


def page_join_collab() -> None:
    if session.current_user_id is None:
        print("⚠️ Un compte est requis pour rejoindre une collaboration.")
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
        print(f"❌ Échec d'ajout : {exc}")
        return

    if not ok:
        print("❌ Token invalide ou accès refusé.")
        return

    print("✅ Collaboration ajoutée.")
    from cli.pages import conversation_detail
    conversation_detail.page_conversation(conv_id)


def show_collaborators(conv_id: int) -> None:
    try:
        collaborators = collab_dao.find_by_conversation(conv_id)
    except Exception as exc:
        print(f"❌ Impossible de lister les collaborateurs : {exc}")
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

    # Sélection de l'utilisateur cible par ID (reste en ask_int, c'est plus sûr)
    try:
        target_user = ask_int("ID utilisateur cible", [])
    except BackCommand:
        return

    # Menu déroulant pour l'action à effectuer
    action = questionary.select(
        "Que souhaites-tu faire pour ce collaborateur ?",
        choices=[
            Choice("📝 Changer le rôle", "change_role"),
            Choice("🗑️ Supprimer le collaborateur", "delete"),
            Separator(),
            Choice("❌ Annuler", "cancel"),
        ],
    ).ask()

    if action is None or action == "cancel":
        return

    from cli.context import collab_service as cs

    if action == "change_role":
        # Menu déroulant pour choisir le nouveau rôle
        new_role = questionary.select(
            "Nouveau rôle :",
            choices=[
                Choice("👑 admin", "admin"),
                Choice("✍️ writer", "writer"),
                Choice("👀 viewer", "viewer"),
                Choice("🚫 banni", "banni"),
            ],
        ).ask()

        if new_role is None:
            return

        try:
            ok = cs.change_role(conv_id, target_user, new_role)
        except Exception as exc:
            print(f"❌ Échec du changement de rôle : {exc}")
            return

        print("✅ Rôle mis à jour." if ok else "ℹ️ Mise à jour non effectuée.")

    elif action == "delete":
        try:
            ok = cs.delete_collaborator(conv_id, target_user)
        except Exception as exc:
            print(f"❌ Échec de suppression : {exc}")
            return

        print("✅ Collaborateur supprimé." if ok else "ℹ️ Suppression non effectuée.")


def share_conversation(conv_id: int) -> None:
    try:
        target_user = ask_int("ID utilisateur à inviter", [])
        can_write = ask_yes_no("Autoriser l'écriture ?")
    except BackCommand:
        return

    from cli.context import conv_service
    try:
        conv_service.share_conversation(
            conv_id, session.current_user_id, target_user, can_write
        )
    except Exception as exc:
        print(f"❌ Partage impossible : {exc}")
        return

    print("✅ Conversation partagée.")
