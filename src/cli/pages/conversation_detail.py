# src/cli/pages/conversation_detail.py

import os
from datetime import datetime
from typing import List

from cli.ui import (
    session,
    ask_int,
    ask_nonempty,
    ask_optional,
    ask_yes_no,
    BackCommand,
    QuitCommand,
    ensure_logged_in,
)
from cli.context import (
    conv_service,
    msg_service,
    collab_service,
    llm_service,
    export_service,
    user_service,
)
from cli.pages import feedback as feedback_pages


# ------------------------------------------------------------------
# Affichage principal de la page conversation
# ------------------------------------------------------------------
def page_conversation(conv_id: int) -> None:
    if not ensure_logged_in():
        return

    session.current_conv_id = conv_id

    # Vérification bannissement
    try:
        is_banni = collab_service.is_banni(session.current_user_id, conv_id)
    except Exception:
        is_banni = False

    if is_banni:
        print("Vous êtes banni de cette conversation. Accès refusé.")
        return

    while True:
        # Charger conversation
        try:
            conversation = conv_service.get_conversation_by_id(
                conv_id, session.current_user_id
            )
        except Exception as exc:
            print(f"Impossible de charger la conversation : {exc}")
            return

        if not conversation:
            print("Conversation introuvable.")
            return

        print("\n=== Conversation ===")
        print(f"ID: {conversation.id_conversation}")
        print(f"Titre: {conversation.titre}")
        print(f"Active: {'Oui' if conversation.is_active else 'Non'}")

        # Permissions
        try:
            is_admin = collab_service.is_admin(session.current_user_id, conv_id)
        except Exception:
            is_admin = False

        try:
            is_banni = collab_service.is_banni(session.current_user_id, conv_id)
        except Exception:
            is_banni = False

        try:
            is_viewer = collab_service.is_viewer(session.current_user_id, conv_id)
        except Exception:
            is_viewer = False

        try:
            is_writer = collab_service.is_writer(session.current_user_id, conv_id)
        except Exception:
            is_writer = False

        # Affichage messages
        try:
            messages = msg_service.get_messages_paginated(conv_id, page=1, per_page=20)
            display_messages(messages)
        except Exception as exc:
            print(f"Impossible de récupérer les messages : {exc}")

        # Menu si banni
        if is_banni:
            print("Vous êtes banni — en lecture seule.")
            print("9) Retour")
            print("0) Quitter")
            try:
                choice = ask_int("Votre choix", [9, 0])
            except BackCommand:
                return
            if choice == 9:
                return
            elif choice == 0:
                raise QuitCommand()
            continue

        # Menu principal
        if is_writer or is_admin:
            print("1) Envoyer un message")
        else:
            print("1) Envoyer un message (accès refusé)")

        print("2) Donner un feedback")
        print("3) Paramétrage (indisponible)")
        print("4) Collaborateurs")

        if is_admin:
            print("5) Partager la conversation")
        else:
            print("5) Partager la conversation (admin requis)")

        print("6) Actions (exporter / quitter / supprimer)")
        print("9) Retour")
        print("0) Quitter")

        try:
            choice = ask_int("Votre choix", [1, 2, 3, 4, 5, 6, 9, 0])
        except BackCommand:
            return

        # Routing des actions
        if choice == 1:
            if is_writer or is_admin:
                send_user_message(conv_id)
            else:
                print("Accès refusé.")
        elif choice == 2:
            feedback_pages.add_feedback_flow(conv_id, messages)
        elif choice == 3:
            print("Paramétrage non implémenté.")
        elif choice == 4:
            from cli.pages import collaboration
            collaboration.show_collaborators(conv_id)
        elif choice == 5:
            if is_admin:
                from cli.pages import collaboration
                collaboration.share_conversation(conv_id)
            else:
                print("Action réservée aux administrateurs.")
        elif choice == 6:
            if conversation_actions(conv_id):
                return
        elif choice == 9:
            return
        elif choice == 0:
            raise QuitCommand()


# ------------------------------------------------------------------
# Affichage messages
# ------------------------------------------------------------------
def display_messages(messages: List) -> None:
    if not messages:
        print("Aucun message pour le moment.")
        return

    print("\n--- Derniers messages ---")
    username_cache = {}

    for message in reversed(messages):
        timestamp = (
            message.datetime.strftime("%Y-%m-%d %H:%M")
            if hasattr(message, "datetime") and isinstance(message.datetime, datetime)
            else ""
        )
        author = _format_author(message, username_cache)
        print(f"[{timestamp}] ({message.id_message}) {author}: {message.message}")


def _format_author(message, cache):
    user_id = getattr(message, "id_user", None)

    if getattr(message, "is_from_agent", False):
        return f"Agent ({user_id})" if user_id else "Agent"

    if user_id in cache:
        username = cache[user_id]
    else:
        try:
            user = user_service.get_user_by_id(user_id)
            username = user.username if user else f"Utilisateur {user_id}"
        except Exception:
            username = f"Utilisateur {user_id}"
        cache[user_id] = username

    return f"{username} ({user_id})"


# ------------------------------------------------------------------
# Envoi message utilisateur
# ------------------------------------------------------------------
def send_user_message(conv_id: int) -> None:
    try:
        content = ask_nonempty("Votre message")
    except BackCommand:
        return

    try:
        msg_service.send_message(conv_id, session.current_user_id, content)
    except Exception as exc:
        print(f"Échec d'envoi : {exc}")
        return

    # Réponse LLM
    try:
        llm_service.generate_agent_reply(
            conversation_id=conv_id,
            user_id=session.current_user_id,
        )
    except Exception as e:
        msg_service.send_agent_message(conv_id, f"[LLM indisponible] {e}")

    print("Message envoyé.")


# ------------------------------------------------------------------
# Actions conversation : exporter / quitter / supprimer
# ------------------------------------------------------------------
def conversation_actions(conv_id: int) -> bool:
    try:

        # Fonction interne factorisant l'export
        def _export_conv() -> None:
            try:
                # 1) Génération du contenu brut
                content = export_service.export_conversation(
                    conv_id, session.current_user_id, fmt="plain"
                )
            except Exception as exc:
                print(f"Erreur durant l'export : {exc}")
                return

            # 2) Nom de fichier basé sur le titre
            try:
                filename = export_service.suggest_filename(conv_id, ext="txt")
            except Exception:
                filename = f"conversation_{conv_id}.txt"

            # 3) Dossier exports
            exports_dir = "exports"
            os.makedirs(exports_dir, exist_ok=True)

            full_path = os.path.join(exports_dir, filename)

            # 4) Écriture fichier
            try:
                with open(full_path, "w", encoding="utf-8") as handle:
                    handle.write(content)
            except OSError as exc:
                print(f"Impossible d'écrire le fichier : {exc}")
            else:
                print(f"✅ Conversation exportée dans : {full_path}")

        # -----------------------------------------------------
        # Menu NON admin
        # -----------------------------------------------------
        if not collab_service.is_admin(session.current_user_id, conv_id):
            print("1) Exporter la conversation")
            print("2) Quitter la conversation")
            print("9) Annuler")

            try:
                choice = ask_int("Action", [1, 2, 9])
            except BackCommand:
                return False

            if choice == 9:
                return False

            if choice == 1:
                _export_conv()
            elif choice == 2:
                if collab_service._count_admins(conv_id) <= 1 and collab_service.is_admin(session.current_user_id, conv_id):
                    print("Vous êtes le seul administrateur — vous ne pouvez pas quitter.")
                    return False
                if ask_yes_no("Quitter la conversation ?"):
                    collab_service.remove_collaboration(conv_id, session.current_user_id)
                    print("Vous avez quitté la conversation.")
                    from cli.pages import user
                    user.page_user_home()
                    return True

            return False

        # -----------------------------------------------------
        # Menu ADMIN
        # -----------------------------------------------------
        else:
            print("1) Exporter la conversation")
            print("2) Quitter la conversation")
            print("3) Supprimer la conversation")
            print("9) Annuler")

            try:
                choice = ask_int("Action", [1, 2, 3, 9])
            except BackCommand:
                return False

            if choice == 9:
                return False

            if choice == 1:
                _export_conv()

            elif choice == 2:
                if collab_service._count_admins(conv_id) <= 1:
                    print("Impossible : vous êtes le seul admin.")
                    return False
                if ask_yes_no("Quitter la conversation ?"):
                    collab_service.remove_collaboration(conv_id, session.current_user_id)
                    print("Vous avez quitté la conversation.")
                    from cli.pages import user
                    user.page_user_home()
                    return True

            elif choice == 3:
                conv_service.archive_conversation(conv_id, session.current_user_id)
                print("Conversation supprimée.")
                from cli.pages import user
                user.page_user_home()
                return True

            return False

    except Exception:
        print("Impossible de vérifier vos droits.")
        return False
