# src/cli/pages/collaboration.py

from cli.ui import (
    ask_int,
    ask_nonempty,
    ask_yes_no,
    ask_optional,
    ask_menu,
    BackCommand,
    session,
    print_table,
)
from cli.context import collab_service, user_service, conv_service


# ---------------------------------------------------------------------------
# Rejoindre une collaboration
# ---------------------------------------------------------------------------

def page_join_collab() -> None:
    """Page pour rejoindre une collaboration."""
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
        print("Token invalide ou accès refusé.")
        return

    print("Collaboration ajoutée.")
    # import local pour éviter les cycles
    from cli.pages.conversation_detail import page_conversation
    page_conversation(conv_id)


# ---------------------------------------------------------------------------
# Affichage et gestion des collaborateurs
# ---------------------------------------------------------------------------

def show_collaborators(conv_id: int) -> None:
    """Afficher les collaborateurs d'une conversation, et éventuellement les gérer."""
    if session.current_user_id is None:
        print("Veuillez vous connecter pour consulter les collaborateurs.")
        return

    try:
        collaborators = collab_service.list_collaborators_for_user(
            conv_id, session.current_user_id
        )
    except PermissionError as exc:
        print(f"Acces refusé: {exc}")
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

    if not rows:
        print("Aucun collaborateur pour cette conversation.")
    else:
        print("\n--- Collaborateurs ---")
        print_table(rows, ["CollabID", "UserID", "Pseudo", "Role"])

    # Vérifier si l'utilisateur courant est admin
    try:
        is_admin = collab_service.is_admin(session.current_user_id, conv_id)
    except Exception:
        is_admin = False

    if not is_admin:
        print("Seuls les administrateurs peuvent modifier les collaborateurs.")
        try:
            _ = ask_optional("Appuyez sur Entrée pour revenir en arrière.")
        except BackCommand:
            pass
        return

    # Proposer la gestion
    try:
        manage = ask_yes_no("Modifier un collaborateur ?")
    except BackCommand:
        return

    if not manage:
        return

    # Choix du collaborateur cible
    try:
        target_user = ask_int("ID utilisateur cible", [])
        if target_user not in [c.id_user for c in (collaborators or [])]:
            print("Utilisateur non trouvé parmi les collaborateurs.")
            return
    except BackCommand:
        return

    # Menu d'action sur ce collaborateur
    try:
        action = ask_menu(
            title="Gestion des collaborateurs",
            subtitle=f"Conversation {conv_id} – Utilisateur cible {target_user}",
            options=[
                ("Changer le rôle", "change_role"),
                ("Supprimer ce collaborateur", "delete"),
                ("Annuler", "cancel"),
            ],
        )
    except BackCommand:
        return

    if action == "change_role":
        _handle_change_role(conv_id, target_user)
    elif action == "delete":
        _handle_delete_collaborator(conv_id, target_user)
    else:
        return


def _handle_change_role(conv_id: int, target_user: int) -> None:
    """Sous-fonction : changement de rôle d'un collaborateur."""
    try:
        new_role = ask_nonempty("Nouveau rôle (admin/writer/viewer/banni)")
    except BackCommand:
        return

    if new_role not in {"admin", "writer", "viewer", "banni"}:
        print("Rôle invalide. Veuillez choisir parmi admin, writer, viewer, banni.")
        return

    try:
        # Empêcher de se destituer si on est le seul admin
        if (
            target_user == session.current_user_id
            and collab_service._count_admins(conv_id) <= 1
        ):
            print(
                "Vous ne pouvez pas modifier votre propre rôle tant que vous êtes le seul administrateur."
            )
            return

        updated = collab_service.change_role(
            conv_id, target_user, new_role, session.current_user_id
        )
    except Exception as exc:
        print(f"Echec du changement de rôle: {exc}")
        return

    print("Rôle mis à jour." if updated else "Aucun changement effectué.")


def _handle_delete_collaborator(conv_id: int, target_user: int) -> None:
    """Sous-fonction : suppression d'un collaborateur."""
    try:
        # Empêcher de se supprimer soi-même si on est seul collaborateur
        if (
            target_user == session.current_user_id
            and collab_service._count_collaborators(conv_id) <= 1
        ):
            print(
                "Impossible de modifier votre propre rôle tant que vous êtes seul dans cette conversation."
            )
            return

        # Empêcher de se supprimer soi-même si on est le seul admin
        if (
            target_user == session.current_user_id
            and collab_service._count_admins(conv_id) <= 1
        ):
            print(
                "Vous ne pouvez pas vous supprimer vous-même si vous êtes le seul admin.\n"
                "Veuillez d'abord promouvoir un autre utilisateur au rôle d'admin."
            )
            return

        deleted = collab_service.delete_collaborator(
            conv_id, target_user, session.current_user_id
        )
    except Exception as exc:
        print(f"Echec de suppression: {exc}")
        return

    print("Collaborateur supprimé." if deleted else "Suppression non effectuée.")


# ---------------------------------------------------------------------------
# Partage de conversation
# ---------------------------------------------------------------------------

def share_conversation(conv_id: int) -> None:
    """Partager une conversation via des tokens et invitations."""
    if session.current_user_id is None:
        print("Veuillez vous connecter pour partager une conversation.")
        return

    # Vérifier les droits admin
    try:
        if not collab_service.is_admin(session.current_user_id, conv_id):
            print("Seuls les administrateurs peuvent partager cette conversation.")
            return
    except Exception as exc:
        print(f"Impossible de vérifier vos droits: {exc}")
        return

    # Charger la conversation
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

    print("\n--- Partage de la conversation ---")

    # Proposer une invitation directe par id
    try:
        invite_someone = ask_yes_no("Voulez-vous inviter un utilisateur par id ?")
    except BackCommand:
        return

    if not invite_someone:
        return

    try:
        target_user = ask_int("ID utilisateur à inviter", [])
        can_write = ask_yes_no("Autoriser l'écriture ?")
    except BackCommand:
        return

    try:
        if target_user == session.current_user_id:
            print("Vous ne pouvez pas vous inviter vous-même.")
            return
        if target_user == 6:
            print("Vous ne pouvez pas inviter cet utilisateur.")
            return

        conv_service.share_conversation(
            conv_id, session.current_user_id, target_user, can_write
        )
    except Exception as exc:
        print(f"Partage impossible: {exc}")
        return

    print("Conversation partagée.")
