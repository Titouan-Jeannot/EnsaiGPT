# src/cli/pages/conversation_detail.py

from datetime import datetime
from typing import List

from cli.ui import (
    session,
    ask_int,
    ask_nonempty,
    BackCommand,
    QuitCommand,
    ensure_logged_in,
)
from cli.context import conv_service, msg_service, collab_service, collab_dao, llm_service
from cli.pages import feedback as feedback_pages
from cli.ui import print_table


def page_conversation(conv_id: int) -> None:
    if not ensure_logged_in():
        return
    session.current_conv_id = conv_id
    while True:
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
        print("\n=== Conversation ===")
        print(f"ID: {conversation.id_conversation}")
        print(f"Titre: {conversation.titre}")
        print(f"Active: {'Oui' if conversation.is_active else 'Non'}")
        print(f"Token lecture: {conversation.token_viewer}")
        print(f"Token ecriture: {conversation.token_writter}")

        messages = []
        try:
            messages = msg_service.get_messages_paginated(conv_id, page=1, per_page=20)
        except Exception as exc:
            print(f"Impossible de recuperer les messages: {exc}")
        else:
            display_messages(messages)

        print("1) Envoyer un message")
        print("2) Donner un feedback")
        print("3) Ajouter un message par ID (non disponible)")
        print("4) Parametrage conversation (non disponible)")
        print("5) Collaborateurs")
        print("6) Partager la conversation")
        print("7) Actions (supprimer/archiver/restaurer)")
        print("9) Retour")
        print("0) Quitter")
        try:
            choice = ask_int("Votre choix", [1, 2, 3, 4, 5, 6, 7, 9, 0])
        except BackCommand:
            return
        if choice == 1:
            send_user_message(conv_id)
        elif choice == 2:
            feedback_pages.add_feedback_flow(conv_id, messages)
        elif choice == 3:
            print("Fonction non implementee.")
        elif choice == 4:
            print("Parametrage non implemente.")
        elif choice == 5:
            from cli.pages import collaboration
            collaboration.show_collaborators(conv_id)
        elif choice == 6:
            from cli.pages import collaboration
            collaboration.share_conversation(conv_id)
        elif choice == 7:
            conversation_actions(conv_id)
        elif choice == 9:
            return
        elif choice == 0:
            raise QuitCommand()


def display_messages(messages: List) -> None:
    if not messages:
        print("Aucun message pour le moment.")
        return
    print("\n--- Derniers messages ---")
    for message in reversed(messages):
        timestamp = (
            message.datetime.strftime("%Y-%m-%d %H:%M")
            if hasattr(message, "datetime") and isinstance(message.datetime, datetime)
            else ""
        )
        author = (
            "Agent" if getattr(message, "is_from_agent", False) else f"User {message.id_user}"
        )
        print(f"[{timestamp}] ({message.id_message}) {author}: {message.message}")


def send_user_message(conv_id: int) -> None:
    try:
        content = ask_nonempty("Votre message")
    except BackCommand:
        return

    try:
        msg_service.send_message(conv_id, session.current_user_id, content)
    except Exception as exc:
        print(f"Echec d'envoi: {exc}")
        return

    # réponse LLM
    try:
        llm_service.generate_agent_reply(
            conversation_id=conv_id,
            user_id=session.current_user_id,
        )
    except Exception as e:
        # fallback : message agent minimal si l’appel HTTP fail
        msg_service.send_agent_message(conv_id, f"[LLM indisponible] {e}")
    print("Message envoye.")


def conversation_actions(conv_id: int) -> None:
    print("1) Supprimer")
    print("2) Archiver")
    print("3) Restaurer")
    print("9) Annuler")
    try:
        choice = ask_int("Action", [1, 2, 3, 9])
    except BackCommand:
        return
    if choice == 9:
        return
    try:
        if choice == 1:
            conv_service.delete_conversation(conv_id, session.current_user_id)
            print("Conversation supprimee.")
        elif choice == 2:
            conv_service.archive_conversation(conv_id, session.current_user_id)
            print("Conversation archivee.")
        elif choice == 3:
            conv_service.restore_conversation(conv_id, session.current_user_id)
            print("Conversation restauree.")
    except Exception as exc:
        print(f"Action impossible: {exc}")
