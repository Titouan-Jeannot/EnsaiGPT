from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
import secrets

try:  # pragma: no cover
    from ObjetMetier.Conversation import Conversation
    from DAO.ConversationDAO import ConversationDAO
    from Service.UserService import UserService
    from Service.MessageService import MessageService
except ImportError:  # pragma: no cover
    from ObjetMetier.Conversation import Conversation  # pragma: no cover
    from DAO.ConversationDAO import ConversationDAO  # pragma: no cover
    from Service.UserService import UserService  # pragma: no cover
    from Service.MessageService import MessageService  # pragma: no cover

if TYPE_CHECKING:  # pragma: no cover
    try:  # pragma: no cover
        from Service.CollaborationService import CollaborationService  # pragma: no cover
    except ImportError:  # pragma: no cover
        from Service.CollaborationService import CollaborationService  # pragma: no cover


class ConversationService:
    """Service pour gérer les conversations."""

    def __init__(
        self,
        conversation_dao: ConversationDAO,
        collaboration_service: Optional[CollaborationService] = None,
        user_service: Optional[UserService] = None,
        message_service: Optional[MessageService] = None,
    ):
        self.conversation_dao = conversation_dao
        self.collaboration_service = collaboration_service
        self.user_service = user_service
        self.message_service = message_service

    def create_conversation(
        self, title: str, user_id: int, setting_conversation: str = "Tu es un assistant utile."
    ) -> Conversation:
        """Crée une nouvelle conversation et ajoute le créateur comme admin."""
        # Vérifier que l'utilisateur existe
        if self.user_service:
            user = self.user_service.get_user_by_id(user_id)
            if not user:
                raise ValueError("Utilisateur introuvable")

        # Valider le titre
        if not title or not title.strip():
            raise ValueError("Titre invalide")
        title = title.strip()

        # Générer les tokens d'accès
        token_viewer = secrets.token_urlsafe(32)
        token_writter = secrets.token_urlsafe(32)

        # Créer l'objet conversation
        conversation = Conversation(
            id_conversation=None,  # Sera généré par la BD
            titre=title,
            created_at=datetime.now(),
            setting_conversation=setting_conversation,
            token_viewer=token_viewer,
            token_writter=token_writter,
            is_active=True,
        )

        # Persister et retourner
        conversation = self.conversation_dao.create(conversation, user_id)

        # Ajouter le créateur comme admin
        if self.collaboration_service:
            self.collaboration_service.create_collab(
                user_id, conversation.id_conversation, "admin"
            )

        return conversation

    def get_conversation_by_id(
        self, conversation_id: int, user_id: int
    ) -> Optional[Conversation]:
        """Récupère une conversation par son ID si l'utilisateur y a accès."""
        if not isinstance(conversation_id, int) or conversation_id < 0:
            raise ValueError("ID de conversation invalide")

        conversation = self.conversation_dao.get_by_id(conversation_id)
        if not conversation:
            return None

        # Vérifier que l'utilisateur a accès
        if not self.conversation_dao.has_access(conversation_id, user_id):
            raise ValueError("Accès non autorisé à cette conversation")

        return conversation

    def get_list_conv(self, user_id: int) -> List[Conversation]:
        """Liste toutes les conversations actives d'un utilisateur."""
        return self.conversation_dao.get_conversations_by_user(user_id)

    def get_list_conv_by_date(self, user_id: int, date: datetime) -> List[Conversation]:
        """Liste les conversations d'un utilisateur créées à une date donnée."""
        return self.conversation_dao.get_conversations_by_date(user_id, date)

    def get_list_conv_by_title(self, user_id: int, title: str) -> List[Conversation]:
        """Recherche les conversations d'un utilisateur par titre."""
        if not title.strip():
            raise ValueError("Critère de recherche invalide")
        return self.conversation_dao.search_conversations_by_title(
            user_id, title.strip()
        )

    def modify_title(self, conversation_id: int, user_id: int, new_title: str) -> None:
        """Modifie le titre d'une conversation si l'utilisateur est admin."""
        if self.collaboration_service and not self.collaboration_service.is_admin(
            user_id, conversation_id
        ):
            raise ValueError("Droits d'administration requis pour modifier le titre")

        if not new_title or not new_title.strip():
            raise ValueError("Nouveau titre invalide")

        # Vérifier les droits d'écriture
        if not self.conversation_dao.has_write_access(conversation_id, user_id):
            raise ValueError("Droits d'écriture requis pour modifier le titre")

        self.conversation_dao.update_title(conversation_id, new_title.strip())

    def delete_conversation(self, conversation_id: int, user_id: int) -> None:
        """Supprime une conversation si l'utilisateur est admin."""
        if self.collaboration_service and not self.collaboration_service.is_admin(
            user_id, conversation_id
        ):
            raise ValueError(
                "Droits d'administration requis pour supprimer la conversation"
            )

        # Vérifier les droits d'écriture
        if not self.conversation_dao.has_write_access(conversation_id, user_id):
            raise ValueError("Droits d'écriture requis pour supprimer la conversation")

        # Supprimer d'abord les messages si un MessageService est disponible
        if self.message_service:
            self.message_service.delete_all_messages_by_conversation(conversation_id)

        # Supprimer la conversation
        self.conversation_dao.delete(conversation_id)

    # Méthodes supplémentaires suggérées

    def archive_conversation(self, conversation_id: int, user_id: int) -> None:
        """Archive une conversation (is_active = False)."""
        if not self.conversation_dao.has_write_access(conversation_id, user_id):
            raise ValueError("Droits d'écriture requis pour archiver la conversation")
        self.conversation_dao.set_active(conversation_id, False)

    def restore_conversation(self, conversation_id: int, user_id: int) -> None:
        """Restaure une conversation archivée."""
        if not self.conversation_dao.has_write_access(conversation_id, user_id):
            raise ValueError("Droits d'écriture requis pour restaurer la conversation")
        self.conversation_dao.set_active(conversation_id, True)

    def share_conversation(
        self,
        conversation_id: int,
        user_id: int,
        target_user_id: int,
        can_write: bool = False,
    ) -> None:
        """Partage une conversation avec un autre utilisateur."""
        if not self.conversation_dao.has_write_access(conversation_id, user_id):
            raise ValueError("Droits d'écriture requis pour partager la conversation")

        if self.user_service:
            target_user = self.user_service.get_user_by_id(target_user_id)
            if not target_user:
                raise ValueError("Utilisateur cible introuvable")

        self.conversation_dao.add_user_access(
            conversation_id, target_user_id, can_write
        )
