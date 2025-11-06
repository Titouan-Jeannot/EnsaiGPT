from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from src.Service.UserService import UserService
from src.Service.AuthService import AuthService
from src.Service.ConversationService import ConversationService
from src.Service.MessageService import MessageService
from src.Service.SearchService import SearchService
from src.Service.CollaborationService import CollaborationService
from src.Service.FeedbackService import FeedbackService

from src.DAO.FeedbackDAO import FeedbackDAO
from src.DAO.CollaborationDAO import CollaborationDAO
from src.DAO.ConversationDAO import ConversationDAO
from src.DAO.MessageDAO import MessageDAO
from src.DAO.UserDAO import UserDAO

from src.ObjetMetier.Feedback import Feedback


class BackCommand(Exception):
    """Commande /back pour revenir en arriere."""

    pass


class QuitCommand(Exception):
    """Commande /quit pour quitter l'application."""

    pass


@dataclass
class Session:
    current_user_id: Optional[int] = None
    current_username: Optional[str] = None
    current_conv_id: Optional[int] = None
    is_guest: bool = False


session = Session()
print("Initialisation des services...")
print(session)
user_dao = UserDAO()
print(user_dao)
auth_service = AuthService(user_dao)
print(auth_service)
print("Verification des instances...")
print(isinstance(user_dao, UserDAO))
print(isinstance(auth_service, AuthService))
print(isinstance(UserService(user_dao, auth_service), UserService))
print("fin de la verification.")
user_service = UserService(user_dao, auth_service)
print(isinstance(user_service, UserService))
print(user_service)

message_dao = MessageDAO()
collab_dao = CollaborationDAO()
conversation_dao = ConversationDAO()
feedback_dao = FeedbackDAO()

collab_service = CollaborationService()
msg_service = MessageService(
    message_dao, user_service=user_service, auth_service=auth_service
)
conv_service = ConversationService(
    conversation_dao, collab_service, user_service, msg_service
)
search_service = SearchService(message_dao, conversation_dao, collab_dao)
print(feedback_dao)
feedback_service = FeedbackService(feedback_dao)


def safe_input(prompt: str) -> str:
    """Encapsule input en capturant les interruptions."""
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print()
        raise QuitCommand()
    except EOFError:
        print()
        raise QuitCommand()


def check_special_command(raw: str) -> None:
    """Interprete les commandes speciales /back et /quit."""
    value = raw.strip().lower()
    if value == "/back":
        raise BackCommand()
    if value == "/quit":
        raise QuitCommand()


def ask_int(prompt: str, choices: List[int]) -> int:
    """Demande un entier appartenant a choices (ou sans restriction si liste vide)."""
    allowed = set(choices)
    while True:
        raw = safe_input(f"{prompt} ").strip()
        check_special_command(raw)
        try:
            value = int(raw)
        except ValueError:
            print("Veuillez saisir un nombre entier valide.")
            continue
        if allowed and value not in allowed:
            options = ", ".join(str(c) for c in sorted(allowed))
            print(f"Choix non valide. Options: {options}.")
            continue
        return value


def ask_nonempty(prompt: str) -> str:
    """Demande une chaine non vide."""
    while True:
        raw = safe_input(f"{prompt} ").strip()
        check_special_command(raw)
        if raw:
            return raw
        print("Ce champ est obligatoire.")


def ask_optional(prompt: str) -> Optional[str]:
    """Demande une chaine optionnelle (vide -> None)."""
    raw = safe_input(f"{prompt} ").strip()
    check_special_command(raw)
    return raw or None


def ask_yes_no(prompt: str) -> bool:
    """Demande une reponse oui/non."""
    while True:
        raw = safe_input(f"{prompt} (y/n) ").strip().lower()
        check_special_command(raw)
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Merci de repondre par y ou n.")


def ask_date(prompt: str) -> datetime:
    """Demande une date au format AAAA-MM-JJ."""
    while True:
        raw = safe_input(f"{prompt} (AAAA-MM-JJ) ").strip()
        check_special_command(raw)
        try:
            return datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            print("Format invalide. Exemple: 2024-05-12.")


def print_table(rows: List[dict], headers: List[str]) -> None:
    """Affiche un tableau en monospace simple."""
    if not rows:
        print("Aucune donnee.")
        return
    widths = {header: len(header) for header in headers}
    for row in rows:
        for header in headers:
            widths[header] = max(widths[header], len(str(row.get(header, ""))))
    header_line = " | ".join(header.ljust(widths[header]) for header in headers)
    separator = "-+-".join("-" * widths[header] for header in headers)
    print(header_line)
    print(separator)
    for row in rows:
        print(
            " | ".join(str(row.get(header, "")).ljust(widths[header]) for header in headers)
        )


def reset_session() -> None:
    """Reinitialise la session utilisateur."""
    session.current_user_id = None
    session.current_username = None
    session.current_conv_id = None
    session.is_guest = False


def ensure_logged_in() -> bool:
    """Verifie qu'un utilisateur est connecte."""
    if session.current_user_id is None:
        print("Veuillez vous connecter pour acceder a cette fonctionnalite.")
        return False
    return True


def build_feedback_object(
    user_id: int, message_id: int, is_like: bool, comment: str
) -> Feedback:
    """Construit un Feedback en gerant la contrainte sur l'identifiant."""
    created_at = datetime.now()
    try:
        return Feedback(
            id_feedback=None,
            id_user=user_id,
            id_message=message_id,
            is_like=is_like,
            comment=comment,
            created_at=created_at,
        )
    except Exception:
        return Feedback(
            id_feedback=0,
            id_user=user_id,
            id_message=message_id,
            is_like=is_like,
            comment=comment,
            created_at=created_at,
        )


def authenticate_credentials(mail: str, password: str):
    """Tente d'authentifier via UserService puis AuthService."""
    user = None
    auth_fn = getattr(user_service, "authenticate_user", None)
    print(f"auth_fn: {auth_fn}")
    # print(isinstance(auth_fn, user))
    print(callable(auth_fn))
    if callable(auth_fn):
        print("appel de user_service.authenticate_user callable")
        try:
            print("avant appel 12")
            user = auth_fn(mail, password)
            print(user)
        except AttributeError as exc:
            print("erreur 11")
            if "verify_mdp" not in str(exc):
                print(f"Erreur d'authentification 1: {exc}")
                return None
        except Exception as exc:
            print("erreur 12")
            print(f"Erreur d'authentification 2: {exc}")
            return None
        if user:
            print("utilisateur trouve via user_service")
            return user
    try:
        print(f"auth_service.authenticate: {auth_service.authenticate(mail, password)}")
        return auth_service.authenticate(mail, password)

    except Exception as exc:
        print(f"Erreur d'authentification 3: {exc}")
        return None


def page_home() -> None:
    print("\n=== Accueil ===")
    print("1) Connexion")
    print("2) Creation de compte")
    print("3) Mode invite")
    print("0) Quitter")
    try:
        choice = ask_int("Votre choix", [1, 2, 3, 0])
    except BackCommand:
        return
    if choice == 1:
        page_login()
    elif choice == 2:
        page_register()
    elif choice == 3:
        session.is_guest = True
        session.current_user_id = None
        session.current_username = "Invite"
        page_guest_home()
    elif choice == 0:
        raise QuitCommand()


def page_login() -> None:
    print("\n=== Connexion ===")
    try:
        mail = ask_nonempty("Email")
        password = ask_nonempty("Mot de passe")
    except BackCommand:
        return

    try:
        user = user_service.authenticate_user(mail, password)
        if not user:
            print("Identifiants invalides.")
            return

    except Exception as e:
        # ici, toute vraie exception -> message interne propre
        print(f"Erreur interne lors de la connexion : {e}")  # ou log + msg générique
        return

    user = authenticate_credentials(mail, password)
    print("Debug apres auth:")
    print(user) # ajustement : user est None ici

    session.current_user_id = getattr(user, "id", None)
    session.current_username = getattr(user, "username", "Utilisateur")
    session.current_conv_id = None
    session.is_guest = False
    print(f"Connexion reussie. Bonjour {session.current_username}!")
    page_user_home()


def page_register() -> None:
    print("\n=== Creation de compte ===")
    try:
        username = ask_nonempty("Nom d'utilisateur")
        nom = ask_optional("Nom (optionnel)")
        prenom = ask_optional("Prenom (optionnel)")
        mail = ask_nonempty("Email")
        password = ask_nonempty("Mot de passe")
    except BackCommand:
        return
    try:
        user_service.create_user(
            mail=mail,
            password_plain=password,
            username=username,
            nom=nom or "",
            prenom=prenom or "",
        )
    except Exception as exc:
        print(f"Echec de creation: {exc}")
        return
    print("Compte cree avec succes. Vous pouvez maintenant vous connecter.")


def page_guest_home() -> None:
    print("\n=== Mode invite ===")
    print("Certaines actions exigent un compte utilisateur.")
    print("1) Rejoindre une collaboration")
    print("9) Retour accueil")
    print("0) Quitter")
    try:
        choice = ask_int("Votre choix", [1, 9, 0])
    except BackCommand:
        return
    if choice == 1:
        page_join_collab()
    elif choice == 9:
        session.is_guest = False
        return
    elif choice == 0:
        raise QuitCommand()


def page_user_home() -> None:
    if not ensure_logged_in():
        return
    while True:
        print("\n=== Espace utilisateur ===")
        print("1) Mon compte")
        print("2) Gestion des conversations")
        print("3) Nouvelle conversation")
        print("4) Rejoindre une collaboration")
        print("9) Deconnexion")
        print("0) Quitter")
        try:
            choice = ask_int("Votre choix", [1, 2, 3, 4, 9, 0])
        except BackCommand:
            return
        if choice == 1:
            page_account()
        elif choice == 2:
            page_manage()
        elif choice == 3:
            create_conversation()
        elif choice == 4:
            page_join_collab()
        elif choice == 9:
            print("Deconnexion effectuee.")
            reset_session()
            return
        elif choice == 0:
            raise QuitCommand()


def page_account() -> None:
    if not ensure_logged_in():
        return
    while True:
        try:
            user = user_service.get_user_by_id(session.current_user_id)
        except Exception as exc:
            print(f"Impossible de charger le compte: {exc}")
            return
        if not user:
            print("Utilisateur introuvable.")
            reset_session()
            return
        print("\n=== Mon compte ===")
        print(f"ID: {user.id}")
        print(f"Email: {user.mail}")
        print(f"Nom: {user.nom}")
        print(f"Prenom: {user.prenom}")
        print(f"Pseudo: {user.username}")
        print(f"Statut: {user.status}")
        print(f"Parametre: {user.setting_param}")
        print("1) Modifier mes informations")
        print("2) Supprimer mon compte")
        print("9) Retour")
        print("0) Quitter")
        try:
            choice = ask_int("Votre choix", [1, 2, 9, 0])
        except BackCommand:
            return
        if choice == 1:
            update_account(user.id)
        elif choice == 2:
            if ask_yes_no("Confirmer la suppression du compte ?"):
                try:
                    user_service.delete_user(user.id)
                except Exception as exc:
                    print(f"Echec de suppression: {exc}")
                else:
                    print("Compte supprime. Retour a l'accueil.")
                    reset_session()
                    return
        elif choice == 9:
            return
        elif choice == 0:
            raise QuitCommand()


def update_account(user_id: int) -> None:
    print("\n--- Modification du profil ---")
    print("Laisser vide pour conserver la valeur actuelle.")
    try:
        mail = ask_optional("Nouvel email")
        username = ask_optional("Nouveau pseudo")
        nom = ask_optional("Nouveau nom")
        prenom = ask_optional("Nouveau prenom")
        setting_param = ask_optional("Nouveau parametre assistant")
        change_password = ask_yes_no("Modifier le mot de passe ?")
        password = None
        if change_password:
            password = ask_nonempty("Nouveau mot de passe")
    except BackCommand:
        return
    try:
        user_service.update_user(
            user_id=user_id,
            mail=mail,
            username=username,
            nom=nom,
            prenom=prenom,
            setting_param=setting_param,
            password_plain=password,
        )
    except Exception as exc:
        print(f"Echec de mise a jour: {exc}")
        return
    print("Profil mis a jour.")


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
        page_conversation(conv_id)


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
    page_conversation(conversation.id_conversation)


def page_join_collab() -> None:
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
        print("Token invalide ou acces refuse.")
        return
    print("Collaboration ajoutee.")
    page_conversation(conv_id)


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
            add_feedback_flow(conv_id, messages)
        elif choice == 3:
            print("Fonction non implementee.")
        elif choice == 4:
            print("Parametrage non implemente.")
        elif choice == 5:
            show_collaborators(conv_id)
        elif choice == 6:
            share_conversation(conv_id)
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
        agent_fn = getattr(msg_service, "add_agent_message", None)
        if callable(agent_fn):
            agent_fn(conv_id, "Reponse generee (placeholder).")
        else:
            msg_service.send_agent_message(
                conv_id, "Reponse generee (placeholder)."
            )
    except Exception as exc:
        print(f"Echec d'envoi: {exc}")
        return
    print("Message envoye.")


def add_feedback_flow(conv_id: int, messages: List) -> None:
    agent_messages = [msg for msg in messages if getattr(msg, "is_from_agent", False)]
    if not agent_messages:
        print("Aucun message agent disponible pour feedback.")
        return
    default = agent_messages[0]
    print(f"Message agent par defaut: ID {default.id_message} -> {default.message}")
    try:
        use_default = ask_yes_no("Utiliser ce message ?")
    except BackCommand:
        return
    if use_default:
        target_id = default.id_message
    else:
        ids = [msg.id_message for msg in agent_messages]
        try:
            target_id = ask_int("Choisir ID du message agent", ids)
        except BackCommand:
            return
    try:
        liked = ask_yes_no("Like ?")
        comment = ask_optional("Commentaire (optionnel)") or ""
    except BackCommand:
        return
    feedback_obj = build_feedback_object(
        user_id=session.current_user_id,
        message_id=target_id,
        is_like=liked,
        comment=comment,
    )
    try:
        result = feedback_dao.create(feedback_obj)
    except Exception as exc:
        print(f"Echec d'enregistrement du feedback: {exc}")
        return
    print(f"Feedback enregistre avec l'id {result.id_feedback}.")


def show_collaborators(conv_id: int) -> None:
    try:
        collaborators = collab_dao.find_by_conversation(conv_id)
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
    print_table(rows, ["CollabID", "UserID", "Pseudo", "Role"])
    try:
        manage = ask_yes_no("Modifier un collaborateur ?")
    except BackCommand:
        return
    if not manage:
        return
    try:
        target_user = ask_int("ID utilisateur cible", [])
    except BackCommand:
        return
    print("1) Changer le role")
    print("2) Supprimer")
    print("9) Annuler")
    try:
        choice = ask_int("Action", [1, 2, 9])
    except BackCommand:
        return
    if choice == 1:
        try:
            new_role = ask_nonempty("Nouveau role (admin/writer/viewer/banned)")
        except BackCommand:
            return
        try:
            ok = collab_service.change_role(conv_id, target_user, new_role)
        except Exception as exc:
            print(f"Echec du changement de role: {exc}")
            return
        print("Role mis a jour." if ok else "Mise a jour non effectuee.")
    elif choice == 2:
        try:
            ok = collab_service.delete_collaborator(conv_id, target_user)
        except Exception as exc:
            print(f"Echec de suppression: {exc}")
            return
        print("Collaborateur supprime." if ok else "Suppression non effectuee.")
    elif choice == 9:
        return


def share_conversation(conv_id: int) -> None:
    try:
        target_user = ask_int("ID utilisateur a inviter", [])
        can_write = ask_yes_no("Autoriser l'ecriture ?")
    except BackCommand:
        return
    try:
        conv_service.share_conversation(
            conv_id, session.current_user_id, target_user, can_write
        )
    except Exception as exc:
        print(f"Partage impossible: {exc}")
        return
    print("Conversation partagee.")


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


if __name__ == "__main__":
    try:
        while True:
            page_home()
    except QuitCommand:
        print("A bientot.")
