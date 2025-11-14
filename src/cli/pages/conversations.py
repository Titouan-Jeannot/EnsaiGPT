# src/cli/pages/conversations.py

from datetime import datetime
from typing import List

from src.cli.ui import (
    ask_int,
    ask_nonempty,
    ask_date,
    BackCommand,
    QuitCommand,
    print_table,
    ensure_logged_in,
    session,
    ask_optional,
)
from src.cli.context import conv_service, search_service


def page_manage() -> None:
    if not ensure_logged_in():
        return
    while True:
        print("\n=== Gestion des conversations ===")
        print("1) Trouver une conversation")
        print("9) Retour")
        print("0) Quitter")
        try:
            choice = ask_int("Votre choix", [1, 9, 0])
        except BackCommand:
            return
        if choice == 1:
            page_search_conversations()
        elif choice == 9:
            return
        elif choice == 0:
            raise QuitCommand()


def page_search_conversations() -> None:
    if not ensure_logged_in():
        return
    while True:
        print("\n--- Recherche de conversations ---")
        print("1) Par mot cle (titre)")
        print("2) Par date de creation")
        print("3) Lister toutes mes conversations")
        print("9) Retour")
        print("0) Quitter")
        try:
            choice = ask_int("Votre choix", [1, 2, 3, 9, 0])
        except BackCommand:
            return
        user_id = session.current_user_id
        conversations: List = []
        if choice == 1:
            try:
                keyword = ask_nonempty("Mot cle")
            except BackCommand:
                continue
            try:
                conversations = search_service.search_conversations_by_keyword(
                    user_id, keyword
                )
            except Exception as exc:
                print(f"Echec de recherche: {exc}")
                continue
        elif choice == 2:
            try:
                target_date = ask_date("Date cible")
            except BackCommand:
                continue
            try:
                conversations = search_service.search_conversations_by_date(
                    user_id, target_date
                )
            except Exception as exc:
                print(f"Echec de recherche: {exc}")
                continue
        elif choice == 3:
            try:
                conversations = conv_service.get_list_conv(user_id)
            except Exception as exc:
                print(f"Echec de lecture: {exc}")
                continue
        elif choice == 9:
            return
        elif choice == 0:
            raise QuitCommand()

        if choice in {1, 2, 3}:
            open_conversation_from_list(conversations)


def open_conversation_from_list(conversations: List) -> None:
    rows = []
    ids: List[int] = []
    for conv in conversations:
        conv_id = getattr(conv, "id_conversation", None)
        if conv_id is None:
            continue
        ids.append(conv_id)
        created_at = getattr(conv, "created_at", None)
        created_str = (
            created_at.strftime("%Y-%m-%d %H:%M")
            if isinstance(created_at, datetime)
            else ""
        )
        rows.append(
            {
                "ID": conv_id,
                "Titre": getattr(conv, "titre", ""),
                "Actif": "Oui" if getattr(conv, "is_active", True) else "Non",
                "Cree": created_str,
            }
        )
    if not ids:
        print("Aucune conversation.")
        return
    print_table(rows, ["ID", "Titre", "Actif", "Cree"])
    print("Entrez l'identifiant de la conversation a ouvrir ou /back.")
    try:
        conv_id = ask_int("ID conversation", ids)
    except BackCommand:
        return
    if conv_id in ids:
        from src.cli.pages import conversation_detail
        conversation_detail.page_conversation(conv_id)


def create_conversation() -> None:
    if not ensure_logged_in():
        return
    print("\n--- Nouvelle conversation ---")
    try:
        title = ask_optional("Titre (defaut: Sans titre)") or "Sans titre"
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
        print(f"Echec de creation: {exc}")
        return
    print(f"Conversation creee (id={conversation.id_conversation}).")
    from src.cli.pages import conversation_detail
    conversation_detail.page_conversation(conversation.id_conversation)
