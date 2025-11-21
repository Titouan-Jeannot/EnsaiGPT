# src/cli/pages/conversations.py

from datetime import datetime
from typing import List

from cli.ui import (
    ask_int,
    ask_nonempty,
    ask_date,
    ask_optional,
    ask_menu,
    BackCommand,
    QuitCommand,
    print_table,
    ensure_logged_in,
    session,
)
from cli.context import conv_service, search_service


def page_manage() -> None:
    """Page de gestion des conversations."""
    if not ensure_logged_in():
        return

    while True:
        try:
            choix = ask_menu(
                title="Gestion des conversations",
                subtitle=None,
                options=[
                    ("Trouver une conversation", "search"),
                    ("Retour", "back"),
                    ("Quitter l'application", "quit"),
                ],
            )
        except BackCommand:
            # Retour au menu appelant
            return

        if choix == "search":
            page_search_conversations()
        elif choix == "back":
            return
        elif choix == "quit":
            raise QuitCommand()


def page_search_conversations() -> None:
    """Page de recherche de conversations."""
    if not ensure_logged_in():
        return

    while True:
        try:
            choix = ask_menu(
                title="Recherche de conversations",
                subtitle="Choisissez un mode de recherche",
                options=[
                    ("Par mot clé", "keyword"),
                    ("Par date de création", "date"),
                    ("Lister toutes mes conversations", "all"),
                    ("Retour", "back"),
                    ("Quitter l'application", "quit"),
                ],
            )
        except BackCommand:
            return

        user_id = session.current_user_id
        conversations: List = []

        if choix == "keyword":
            try:
                keyword = ask_nonempty("Mot clé :")
            except BackCommand:
                continue
            try:
                conversations = search_service.search_conversations_by_keyword(
                    user_id, keyword
                )
            except Exception as exc:
                print(f"Echec de recherche: {exc}")
                continue

        elif choix == "date":
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

        elif choix == "all":
            try:
                conversations = conv_service.get_list_conv(user_id)
            except Exception as exc:
                print(f"Echec de lecture: {exc}")
                continue

        elif choix == "back":
            return

        elif choix == "quit":
            raise QuitCommand()

        if choix in {"keyword", "date", "all"}:
            open_conversation_from_list(conversations)


def open_conversation_from_list(conversations: List) -> None:
    """Ouvrir une conversation à partir d'une liste."""
    rows = []
    options = []

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
        titre = getattr(conv, "titre", "") or "Sans titre"
        actif = "Oui" if getattr(conv, "is_active", True) else "Non"

        rows.append(
            {
                "ID": conv_id,
                "Titre": titre,
                "Actif": actif,
                "Cree": created_str,
            }
        )

        label = f"#{conv_id} – {titre} ({'actif' if actif == 'Oui' else 'inactif'}, {created_str})"
        options.append((label, str(conv_id)))

    if not rows:
        print("Aucune conversation.")
        try:
            _ = ask_optional("Appuyez sur Entrée pour revenir.")
        except BackCommand:
            pass
        return

    print("\n--- Résultats ---")
    print_table(rows, ["ID", "Titre", "Actif", "Cree"])

    # Ajout d'une option "Retour" dans le menu
    options.append(("Retour", "back"))

    try:
        choix = ask_menu(
            title="Ouvrir une conversation",
            subtitle="Sélectionnez une conversation à ouvrir",
            options=options,
        )
    except BackCommand:
        return

    if choix == "back":
        return

    try:
        conv_id = int(choix)
    except ValueError:
        print("Choix invalide.")
        return

    from cli.pages.conversation_detail import page_conversation
    page_conversation(conv_id)


def create_conversation() -> None:
    """Créer une nouvelle conversation."""
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
            setting_conversation=setting or "",
        )
    except Exception as exc:
        print(f"Echec de creation: {exc}")
        return

    print(f"Conversation creee (id={conversation.id_conversation}).")
    from cli.pages.conversation_detail import page_conversation
    page_conversation(conversation.id_conversation)
