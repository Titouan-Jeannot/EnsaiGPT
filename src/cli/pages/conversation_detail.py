# src/cli/pages/conversation_detail.py

import os
from datetime import datetime
from typing import List, Optional

from cli.ui import (
    session,
    ask_nonempty,
    ask_optional,
    ask_yes_no,
    BackCommand,
    QuitCommand,
    ensure_logged_in,
    ask_menu,
)
from cli.context import (
    conv_service,
    msg_service,
    collab_service,
    llm_service,
    export_service,
    user_service,
    stats_service,
)
from cli.pages import feedback as feedback_pages


# ------------------------------------------------------------------
# Page principale de la conversation (avec header + menu déroulant)
# ------------------------------------------------------------------
def page_conversation(conv_id: int) -> None:
    """Page de détail d'une conversation."""
    if not ensure_logged_in():
        return

    session.current_conv_id = conv_id
    last_notification: Optional[str] = None  # message affiché dans le header au prochain tour

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

        # Rôles / droits
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

        # Messages (20 derniers)
        try:
            messages = msg_service.get_messages_paginated(
                conv_id, page=1, per_page=20
            )
        except Exception as exc:
            print(f"Impossible de récupérer les messages : {exc}")
            messages = []

        # Construire le header complet (incluant éventuellement la dernière notification)
        header = _build_header(conversation, messages, conv_id, last_notification)
        # La notification est "consommée" après ce tour :
        last_notification = None

        # ------------------ CAS BANNI : lecture seule + menu réduit ------------------
        if is_banni:
            options = [
                ("Retour", "back"),
                ("Quitter l'application", "quit"),
            ]
            try:
                choice = ask_menu(
                    title="Conversation (accès restreint)",
                    subtitle="Vous êtes banni : accès en lecture seule.",
                    options=options,
                    header=header,
                )
            except BackCommand:
                return
            except QuitCommand:
                raise

            if choice == "back":
                return
            if choice == "quit":
                raise QuitCommand()

            # On reboucle (header re-généré automatiquement)
            continue

        # ------------------ CAS NORMAL : menu complet ------------------
        options = []

        if is_writer or is_admin:
            options.append(("Envoyer un message", "send"))
        else:
            options.append(("Envoyer un message (lecture seule)", "send_readonly"))

        options.append(("Donner un feedback sur un message agent", "feedback"))
        options.append(("Voir / gérer les collaborateurs", "collabs"))

        if is_admin:
            options.append(("Partager la conversation", "share"))
            options.append(
                ("Actions (exporter / paramétrage / quitter / supprimer)", "actions")
            )
        else:
            options.append(("Partager la conversation (admin requis)", "share_ro"))
            options.append(("Actions (exporter / quitter)", "actions"))

        options.append(("Retour", "back"))
        options.append(("Quitter l'application", "quit"))

        try:
            choice = ask_menu(
                title="Menu conversation",
                subtitle=None,
                options=options,
                header=header,
            )
        except BackCommand:
            return
        except QuitCommand:
            raise

        # Routing
        if choice == "send":
            if is_writer or is_admin:
                success, notif = send_user_message(conv_id)
                if notif:
                    last_notification = notif
            else:
                msg = "Vous n'avez pas les droits d'écriture dans cette conversation."
                print(msg)
                last_notification = msg

        elif choice == "send_readonly":
            msg = "Vous n'avez pas les droits d'écriture dans cette conversation."
            print(msg)
            last_notification = msg

        elif choice == "feedback":
            success, notif = feedback_pages.add_feedback_flow(conv_id, messages)
            if notif:
                last_notification = notif

        elif choice == "collabs":
            from cli.pages import collaboration
            collaboration.show_collaborators(conv_id)

        elif choice == "share":
            if is_admin:
                from cli.pages import collaboration
                collaboration.share_conversation(conv_id)
            else:
                msg = "Action réservée aux administrateurs."
                print(msg)
                last_notification = msg

        elif choice == "share_ro":
            msg = "Action réservée aux administrateurs."
            print(msg)
            last_notification = msg

        elif choice == "actions":
            done = conversation_actions(conv_id)
            # Les prints de conversation_actions seront visibles au moment où tu es dedans,
            # mais si tu veux, on pourra aussi remonter certaines infos ici plus tard.
            if done:
                return

        elif choice == "back":
            return

        elif choice == "quit":
            raise QuitCommand()


# ------------------------------------------------------------------
# Construction du header : infos + stats + 20 derniers messages + notif
# ------------------------------------------------------------------
def _build_header(conversation, messages: List, conv_id: int, notification: Optional[str]) -> str:
    """Construit la bannière affichée avant le menu.

    Ordre :
    - infos conversation
    - stats
    - 20 derniers messages
    - éventuelle notification (succès/erreur) en BAS, juste avant le menu
    """
    lines: List[str] = []

    # Infos de base
    lines.append("=== Conversation ===")
    lines.append(f"ID    : {conversation.id_conversation}")
    lines.append(f"Titre : {conversation.titre}")
    lines.append(f"Active: {'Oui' if conversation.is_active else 'Non'}")

    # Stats
    try:
        total_msgs = stats_service.nb_message_conv(conv_id)
    except Exception:
        total_msgs = "?"

    try:
        user_msgs = stats_service.nb_messages_de_user_par_conv(
            session.current_user_id, conv_id
        )
    except Exception:
        user_msgs = "?"

    try:
        nb_collabs = stats_service.count_collaborators_by_conv(conv_id)
    except Exception:
        nb_collabs = "?"

    lines.append("")
    lines.append("=== Statistiques ===")
    lines.append(f"Messages totaux          : {total_msgs}")
    lines.append(f"Messages envoyés par vous: {user_msgs}")
    lines.append(f"Collaborateurs           : {nb_collabs}")
    lines.append("---------------------")

    # Messages (on les affiche du plus ancien au plus récent, sur les 20 derniers)
    if messages:
        lines.append("")
        lines.append("--- Derniers messages (max 20) ---")
        username_cache = {}
        for msg in reversed(messages):
            timestamp = (
                msg.datetime.strftime("%Y-%m-%d %H:%M")
                if hasattr(msg, "datetime") and isinstance(msg.datetime, datetime)
                else ""
            )
            author = _format_author(msg, username_cache)
            lines.append(f"[{timestamp}] ({msg.id_message}) {author}: {msg.message}")
    else:
        lines.append("")
        lines.append("Aucun message pour le moment.")

    # Notification en BAS, après les messages
    if notification:
        lines.append("")
        lines.append(f"⚡ {notification}")

    return "\n".join(lines)


def _format_author(message, cache: dict) -> str:
    """Formater l'auteur d'un message pour l'affichage."""
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
# Envoi message utilisateur (renvoie succès + notif)
# ------------------------------------------------------------------
def send_user_message(conv_id: int) -> (bool, Optional[str]):
    """Envoyer un message utilisateur dans une conversation.

    Retourne (success, message_notification).
    """
    try:
        content = ask_nonempty("Votre message")
    except BackCommand:
        return False, None

    try:
        msg_service.send_message(conv_id, session.current_user_id, content)
    except Exception as exc:
        msg = f"Échec d'envoi du message : {exc}"
        print(msg)
        return False, msg

    # Réponse LLM
    try:
        llm_service.generate_agent_reply(
            conversation_id=conv_id,
            user_id=session.current_user_id,
        )
    except Exception as e:
        fallback = f"[LLM indisponible] {e}"
        msg_service.send_agent_message(conv_id, fallback)
        msg = "Message envoyé, mais l'agent a rencontré une erreur."
        print(msg)
        return True, msg

    msg = "Message envoyé."
    print(msg)
    return True, msg


# ------------------------------------------------------------------
# Actions conversation : exporter / paramétrage / quitter / supprimer
# (inchangé, menus numériques + prints classiques)
# ------------------------------------------------------------------
def conversation_actions(conv_id: int) -> bool:
    """Gérer les actions avancées d'une conversation.

    Retourne True si l'utilisateur quitte/supprime la conversation.
    Retourne False si l'utilisateur revient sans quitter.
    """
    try:
        # Petite fonction interne pour factoriser l'export
        def _export_conv() -> None:
            """Export et écriture sur disque de la conversation."""
            try:
                content = export_service.export_conversation(
                    conv_id, session.current_user_id, fmt="plain"
                )
            except Exception as exc:
                print(f"Erreur durant l'export : {exc}")
                return

            try:
                filename = export_service.suggest_filename(conv_id, ext="txt")
            except Exception:
                filename = f"conversation_{conv_id}.txt"

            exports_dir = "exports"
            os.makedirs(exports_dir, exist_ok=True)
            full_path = os.path.join(exports_dir, filename)

            try:
                with open(full_path, "w", encoding="utf-8") as handle:
                    handle.write(content)
            except OSError as exc:
                print(f"Impossible d'écrire le fichier : {exc}")
            else:
                print(f"✅ Conversation exportée dans : {full_path}")

        # Vérifier si admin
        try:
            is_admin = collab_service.is_admin(session.current_user_id, conv_id)
        except Exception:
            is_admin = False

        while True:
            # --- Construction du menu déroulant ---
            if not is_admin:
                options = [
                    ("Exporter la conversation", "export"),
                    ("Quitter la conversation", "quit_conv"),
                    ("Retour", "back"),
                ]
            else:
                options = [
                    ("Exporter la conversation", "export"),
                    ("Paramétrage (prompt système)", "settings"),
                    ("Quitter la conversation", "quit_conv"),
                    ("Supprimer la conversation", "delete_conv"),
                    ("Retour", "back"),
                ]

            from cli.ui import ask_menu  # import local pour éviter des cycles

            try:
                choice = ask_menu(
                    title="Actions sur la conversation",
                    subtitle=None,
                    options=options,
                    header=None,        # pas de header ici, juste un écran propre
                    clear_screen=True,  # on veut un écran d'actions bien séparé
                )
            except BackCommand:
                return False
            except QuitCommand:
                raise

            # --- Routage des choix ---
            if choice == "export":
                _export_conv()
                # on reste dans le sous-menu actions
                continue

            if choice == "settings" and is_admin:
                # Paramétrage du prompt système
                print("Voici le prompt système actuel de la conversation :")
                conversation = conv_service.get_conversation_by_id(
                    conv_id, session.current_user_id
                )

                if not conversation.setting_conversation:
                    print(
                        "Aucun prompt système défini pour la conversation. "
                        "Chaque utilisateur utilise son propre prompt système."
                    )
                else:
                    print(conversation.setting_conversation)

                try:
                    is_modifier_prompt = ask_yes_no("Voulez-vous le modifier ?")
                except BackCommand:
                    # retour au menu des actions
                    continue

                if not is_modifier_prompt:
                    continue

                try:
                    new_setting = ask_optional(
                        "Nouveau prompt système (laisser vide pour garder le prompt système de chaque utilisateur)"
                    )
                    conv_service.update_conversation_setting(
                        conv_id, session.current_user_id, new_setting
                    )
                    print("Prompt système changé avec succès.")
                except BackCommand:
                    # retour au menu des actions
                    continue

                # on reste dans le sous-menu actions
                continue

            if choice == "quit_conv":
                # Cas non admin : même logique qu'avant (avec la petite sécurité déjà présente)
                if is_admin:
                    # Admin : vérifier qu'il n'est pas le dernier admin
                    if collab_service._count_admins(conv_id) <= 1:
                        print("Impossible : vous êtes le seul administrateur.")
                        continue

                if ask_yes_no("Quitter la conversation ?"):
                    collab_service.remove_collaboration(
                        conv_id, session.current_user_id
                    )
                    print("Vous avez quitté la conversation.")
                    from cli.pages import user
                    user.page_user_home()
                    return True
                # sinon on reste dans le sous-menu
                continue

            if choice == "delete_conv" and is_admin:
                # Suppression (archive) de la conversation
                if ask_yes_no(
                    "Supprimer (archiver) définitivement cette conversation ?"
                ):
                    conv_service.archive_conversation(
                        conv_id, session.current_user_id
                    )
                    print("Conversation supprimée.")
                    from cli.pages import user
                    user.page_user_home()
                    return True
                # sinon on reste dans le menu
                continue

            if choice == "back":
                return False

    except Exception:
        print("Impossible de vérifier vos droits.")
        return False
