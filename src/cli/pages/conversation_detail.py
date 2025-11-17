# src/cli/pages/conversation_detail.py

from datetime import datetime
from typing import List

from cli.ui import (
    session,
    ask_nonempty,
    BackCommand,
    QuitCommand,
    ensure_logged_in,
)
from cli.context import conv_service, msg_service, collab_service, collab_dao, llm_service
from cli.pages import feedback as feedback_pages
from cli.ui import print_table

import questionary
from questionary import Choice, Separator


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
            print(f"❌ Impossible de charger la conversation : {exc}")
            return

        if not conversation:
            print("❌ Conversation introuvable.")
            return

        # En-tête conversation
        print("\n=== Conversation ===")
        print(f"🆔 ID          : {conversation.id_conversation}")
        print(f"🏷️  Titre       : {conversation.titre}")
        print(f"✅ Active      : {'Oui' if conversation.is_active else 'Non'}")
        print(f"👁️  Token lecture : {conversation.token_viewer}")
        print(f"✍️  Token écriture: {conversation.token_writter}")

        # Messages
        messages: List = []
        try:
            messages = msg_service.get_messages_paginated(conv_id, page=1, per_page=20)
        except Exception as exc:
            print(f"❌ Impossible de récupérer les messages : {exc}")
        else:
            display_messages(messages)

        # Menu principal (remplace les choix numériques)
        action = questionary.select(
            "\nQue souhaites-tu faire ?",
            choices=[
                Choice("✉️  Envoyer un message", "send_msg"),
                Choice("⭐ Donner un feedback", "feedback"),
                Choice("➕ Ajouter un message par ID (non disponible)", "add_msg_id"),
                Choice("⚙️  Paramétrage conversation (non disponible)", "settings"),
                Separator(),
                Choice("👥 Voir / gérer les collaborateurs", "collabs"),
                Choice("🔗 Partager la conversation", "share"),
                Choice("🗂️  Actions (supprimer / archiver / restaurer)", "actions"),
                Separator(),
                Choice("⬅️ Retour", "back"),
                Choice("❌ Quitter", "quit"),
            ],
        ).ask()

        # Si l’utilisateur annule (Ctrl+C, fermeture du prompt)
        if action is None:
            # On interprète ça comme un retour en arrière
            return

        if action == "send_msg":
            send_user_message(conv_id)

        elif action == "feedback":
            feedback_pages.add_feedback_flow(conv_id, messages)

        elif action == "add_msg_id":
            print("ℹ️ Fonction non implémentée.")

        elif action == "settings":
            print("ℹ️ Paramétrage non implémenté.")

        elif action == "collabs":
            from cli.pages import collaboration
            collaboration.show_collaborators(conv_id)

        elif action == "share":
            from cli.pages import collaboration
            collaboration.share_conversation(conv_id)

        elif action == "actions":
            conversation_actions(conv_id)

        elif action == "back":
            return

        elif action == "quit":
            raise QuitCommand()


def display_messages(messages: List) -> None:
    if not messages:
        print("\n--- Derniers messages ---")
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
            "Agent"
            if getattr(message, "is_from_agent", False)
            else f"User {message.id_user}"
        )
        print(f"[{timestamp}] ({message.id_message}) {author} : {message.message}")


def send_user_message(conv_id: int) -> None:
    try:
        content = ask_nonempty("Votre message")
    except BackCommand:
        return

    try:
        msg_service.send_message(conv_id, session.current_user_id, content)
    except Exception as exc:
        print(f"❌ Échec d'envoi : {exc}")
        return

    # Réponse LLM
    try:
        llm_service.generate_agent_reply(
            conversation_id=conv_id,
            user_id=session.current_user_id,
        )
    except Exception as e:
        # fallback : message agent minimal si l’appel HTTP échoue
        msg_service.send_agent_message(conv_id, f"[LLM indisponible] {e}")

    print("✅ Message envoyé.")


def conversation_actions(conv_id: int) -> None:
    """
    Sous-menu pour les actions sur la conversation :
    supprimer / archiver / restaurer.
    """

    action = questionary.select(
        "Que souhaites-tu faire sur cette conversation ?",
        choices=[
            Choice("🗑️ Supprimer", "delete"),
            Choice("📦 Archiver", "archive"),
            Choice("♻️ Restaurer", "restore"),
            Separator(),
            Choice("❌ Annuler", "cancel"),
        ],
    ).ask()

    if action is None or action == "cancel":
        return

    try:
        if action == "delete":
            conv_service.delete_conversation(conv_id, session.current_user_id)
            print("✅ Conversation supprimée.")
        elif action == "archive":
            conv_service.archive_conversation(conv_id, session.current_user_id)
            print("✅ Conversation archivée.")
        elif action == "restore":
            conv_service.restore_conversation(conv_id, session.current_user_id)
            print("✅ Conversation restaurée.")
    except Exception as exc:
        print(f"❌ Action impossible : {exc}")
