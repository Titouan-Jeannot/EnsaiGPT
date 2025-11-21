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
    ask_menu,
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
    stats_service,
)
from cli.pages import feedback as feedback_pages


# ------------------------------------------------------------------
# Affichage principal de la page conversation
# ------------------------------------------------------------------
def page_conversation(conv_id: int) -> None:
    """Page de détail d'une conversation."""
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

        print("\n=== Statistiques de la conversation ===")
        try:
            nb_total = stats_service.nb_message_conv(conv_id)
        except Exception:
            nb_total = "?"
        try:
            nb_user = stats_service.nb_messages_de_user_par_conv(
                session.current_user_id, conv_id
            )
        except Exception:
            nb_user = "?"
        try:
            nb_collabs = stats_service.count_collaborators_by_conv(conv_id)
        except Exception:
            nb_collabs = "?"

        print(f"Messages totaux          : {nb_total}")
        print(f"Messages envoyés par vous: {nb_user}")
        print(f"Collaborateurs           : {nb_collabs}")
        print("---------------------")

        # Droits actuels
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
            messages = []

        # Menu si banni (lecture seule + sortie)
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

        # Menu principal (version menu déroulant)
        options = []
        if is_writer or is_admin:
            options.append(("Envoyer un message", "send_msg"))
        else:
            options.append(("Envoyer un message (lecture seule - refusé)", "send_denied"))

        options.append(("Donner un feedback", "feedback"))
        options.append(("Voir / gérer les collaborateurs", "collabs"))

        if is_admin:
            options.append(("Partager la conversation", "share"))
            options.append(("Actions : exporter / paramétrage / quitter / supprimer", "actions"))
        else:
            options.append(("Partager la conversation (admin requis)", "share_denied"))
            options.append(("Actions : exporter / quitter", "actions"))

        options.append(("Retour", "back"))
        options.append(("Quitter l'application", "quit"))

        try:
            choix = ask_menu(
                title="Menu conversation",
                subtitle=f"Conversation #{conversation.id_conversation}",
                options=options,
            )
        except BackCommand:
            return

        # Routing des actions
        if choix == "send_msg":
            if is_writer or is_admin:
                send_user_message(conv_id)
            else:
                print("Vous n'avez pas les droits d'écriture dans cette conversation.")
        elif choix == "send_denied":
            print("Vous n'avez pas les droits d'écriture dans cette conversation.")
        elif choix == "feedback":
            feedback_pages.add_feedback_flow(conv_id, messages)
        elif choix == "collabs":
            from cli.pages.collaboration import show_collaborators
            show_collaborators(conv_id)
        elif choix == "share":
            if is_admin:
                from cli.pages.collaboration import share_conversation
                share_conversation(conv_id)
            else:
                print("Action réservée aux administrateurs.")
        elif choix == "share_denied":
            print("Action réservée aux administrateurs.")
        elif choix == "actions":
            if conversation_actions(conv_id):
                return
        elif choix == "back":
            return
        elif choix == "quit":
            raise QuitCommand()


# ------------------------------------------------------------------
# Affichage messages
# ------------------------------------------------------------------
def display_messages(messages: List) -> None:
    """Afficher les messages d'une conversation."""
    if not messages:
        print("Aucun message pour le moment.")
        return

    print("\n--- Derniers messages (20 plus récents) ---")
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
# Envoi message utilisateur
# ------------------------------------------------------------------
def send_user_message(conv_id: int) -> None:
    """Envoyer un message utilisateur dans une conversation."""
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
# Actions conversation : exporter / paramétrage / quitter / supprimer
# ------------------------------------------------------------------
def conversation_actions(conv_id: int) -> bool:
    """
    Gérer les actions avancées d'une conversation.

    Retourne True si la page doit se fermer (ex: conversation quittée ou supprimée),
    False sinon.
    """
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

        # On vérifie tout de suite le statut admin
        try:
            is_admin = collab_service.is_admin(session.current_user_id, conv_id)
        except Exception:
            is_admin = False

        # -----------------------------------------------------
        # Menu NON admin
        # -----------------------------------------------------
        if not is_admin:
            # menu simple, pas besoin de ask_menu ici
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
                # cas limite : utilisateur non admin mais _count_admins + is_admin dans code existant
                if collab_service._count_admins(conv_id) <= 1 and collab_service.is_admin(
                    session.current_user_id, conv_id
                ):
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
            print("2) Paramétrage")
            print("3) Quitter la conversation")
            print("4) Supprimer la conversation")
            print("9) Annuler")

            try:
                choice = ask_int("Action", [1, 2, 3, 4, 9])
            except BackCommand:
                return False

            if choice == 9:
                return False

            if choice == 1:
                _export_conv()

            elif choice == 2:
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
                    return False

                if not is_modifier_prompt:
                    return False

                try:
                    new_setting = ask_optional(
                        "Nouveau prompt système (laisser vide pour garder le prompt système de chaque utilisateur)"
                    )
                    conv_service.update_conversation_setting(
                        conv_id, session.current_user_id, new_setting
                    )
                    print("Prompt système changé avec succès.")
                except BackCommand:
                    return False

            elif choice == 3:
                if collab_service._count_admins(conv_id) <= 1:
                    print("Impossible : vous êtes le seul admin.")
                    return False
                if ask_yes_no("Quitter la conversation ?"):
                    collab_service.remove_collaboration(conv_id, session.current_user_id)
                    print("Vous avez quitté la conversation.")
                    from cli.pages import user
                    user.page_user_home()
                    return True

            elif choice == 4:
                conv_service.archive_conversation(conv_id, session.current_user_id)
                print("Conversation supprimée.")
                from cli.pages import user
                user.page_user_home()
                return True

            return False

    except Exception:
        print("Impossible de vérifier vos droits.")
        return False
