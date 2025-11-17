# src/cli/pages/conversations.py

from datetime import datetime
from typing import List

from cli.ui import (
    ask_nonempty,
    ask_date,
    BackCommand,
    QuitCommand,
    print_table,
    ensure_logged_in,
    session,
    ask_optional,
)
from cli.context import conv_service, search_service

import questionary
from questionary import Choice, Separator


def page_manage() -> None:
    if not ensure_logged_in():
        return

    while True:
        action = questionary.select(
            "\n=== Gestion des conversations ===",
            choices=[
                Choice("🔍 Rechercher une conversation", "search"),
                Separator(),
                Choice("⬅️ Retour", "back"),
                Choice("❌ Quitter", "quit"),
            ],
        ).ask()

        if action is None or action == "back":
            return

        if action == "search":
            page_search_conversations()

        elif action == "quit":
            raise QuitCommand()


def page_search_conversations() -> None:
    if not ensure_logged_in():
        return

    while True:
        action = questionary.select(
            "\n--- Recherche de conversations ---",
            choices=[
                Choice("🔤 Par mot-clé (titre)", "by_keyword"),
                Choice("📅 Par date de création", "by_date"),
                Choice("📄 Lister toutes mes conversations", "all"),
                Separator(),
                Choice("⬅️ Retour", "back"),
                Choice("❌ Quitter", "quit"),
            ],
        ).ask()

        if action is None or action == "back":
            return

        user_id = session.current_user_id
        conversations: List = []

        if action == "by_keyword":
            try:
                keyword = ask_nonempty("Mot clé")
            except BackCommand:
                continue
            try:
                conversations = search_service.search_conversations_by_keyword(
                    user_id, keyword
                )
            except Exception as exc:
                print(f"❌ Échec de la recherche : {exc}")
                continue

        elif action == "by_date":
            try:
                target_date = ask_date("Date cible")
            except BackCommand:
                continue
            try:
                conversations = search_service.search_conversations_by_date(
                    user_id, target_date
                )
            except Exception as exc:
                print(f"❌ Échec de la recherche : {exc}")
                continue

        elif action == "all":
            try:
                conversations = conv_service.get_list_conv(user_id)
            except Exception as exc:
                print(f"❌ Échec de lecture : {exc}")
                continue

        elif action == "quit":
            raise QuitCommand()

        # Si on a récupéré une liste, proposer d'en ouvrir une
        if action in {"by_keyword", "by_date", "all"}:
            open_conversation_from_list(conversations)


def open_conversation_from_list(conversations: List) -> None:
    rows = []
    choices: List[Choice] = []

    for conv in conversations:
        conv_id = getattr(conv, "id_conversation", None)
        if conv_id is None:
            continue

        created_at = getattr(conv, "created_at", None)
        created_str = (
            created_at.strftime("%Y-%m-%d %H:%M")
            if isinstance(created_at, datetime)
            else ""
        )
        titre = getattr(conv, "titre", "")
        actif_str = "Actif" if getattr(conv, "is_active", True) else "Inactif"

        rows.append(
            {
                "ID": conv_id,
                "Titre": titre,
                "Actif": "Oui" if getattr(conv, "is_active", True) else "Non",
                "Créé": created_str,
            }
        )

        label = f"[{conv_id}] {titre or '(Sans titre)'}  -  {actif_str}  ({created_str})"
        choices.append(Choice(label, conv_id))

    if not choices:
        print("Aucune conversation.")
        return

    # Affichage tableau + select
    print_table(rows, ["ID", "Titre", "Actif", "Créé"])

    action = questionary.select(
        "\nChoisis une conversation à ouvrir :",
        choices=choices + [
            Separator(),
            Choice("❌ Annuler", "cancel"),
        ],
    ).ask()

    if action is None or action == "cancel":
        return

    conv_id = action
    from cli.pages import conversation_detail
    conversation_detail.page_conversation(conv_id)


def create_conversation() -> None:
    if not ensure_logged_in():
        return

    print("\n--- Nouvelle conversation ---")
    try:
        title = ask_optional("Titre (défaut : Sans titre)") or "Sans titre"
        setting = ask_optional("Prompt assistant (optionnel)")
    except BackCommand:
        return

    try:
        conversation = conv_service.create_conversation(
            title=title,
            user_id=session.current_user_id,
            setting_conversation=setting or "Tu es un assistant utile.",
        )
    except Exception as exc:
        print(f"❌ Échec de création : {exc}")
        return

    print(f"✅ Conversation créée (id={conversation.id_conversation}).")
    from cli.pages import conversation_detail
    conversation_detail.page_conversation(conversation.id_conversation)
