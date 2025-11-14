from typing import List, Optional
from datetime import datetime, timezone
# from config import AGENT_USER_ID*
AGENT_USER_ID = 6

try:
    from ObjetMetier.Message import Message
    from DAO.MessageDAO import MessageDAO
    from Service.UserService import UserService
    from Service.AuthService import AuthService
except Exception:
    from src.ObjetMetier.Message import Message
    from src.DAO.MessageDAO import MessageDAO
    from src.Service.UserService import UserService
    from src.Service.AuthService import AuthService


class MessageService:
    """
    Service pour gérer les messages d'une conversation.
    Fournit : send_message, get_messages, get_message_by_id, delete_all_messages_by_conversation.
    """

    def __init__(
        self,
        message_dao: MessageDAO,
        user_service: Optional[UserService] = None,
        auth_service: Optional[AuthService] = None,
    ):
        self.message_dao = message_dao
        self.user_service = user_service
        self.auth_service = auth_service

    # helper to resolve dao methods by possible names
    def _get_dao_callable(self, *names):
        for n in names:
            fn = getattr(self.message_dao, n, None)
            if callable(fn):
                return fn
        return None

    def send_message(self, conversation_id: int, user_id: int, message: str) -> Message:
        """Crée et persiste un message envoyé par un utilisateur (is_from_agent=False)."""
        if not isinstance(conversation_id, int) or conversation_id < 0:
            raise ValueError("conversation_id invalide")
        if not isinstance(user_id, int) or user_id < 0:
            raise ValueError("user_id invalide")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message non fourni")
        # limite raisonnable
        if len(message) > 5000:
            raise ValueError("message trop long")

        # vérifier que l'utilisateur existe (si possible)
        if self.user_service and hasattr(self.user_service, "get_user_by_id"):
            try:
                u = self.user_service.get_user_by_id(user_id)
            except Exception:
                u = None
            if not u:
                raise ValueError("Utilisateur introuvable")
        elif self.auth_service:
            try:
                self.auth_service.check_user_exists(user_id)
            except Exception as e:
                raise ValueError("Utilisateur introuvable") from e
        # construire l'objet Message
        now = datetime.now(timezone.utc)
        msg_obj = Message(
            id_message=None,
            id_conversation=conversation_id,
            id_user=user_id,
            datetime=now,
            message=message,
            is_from_agent=False,
        )

        # Utiliser directement la méthode create du DAO
        return self.message_dao.create(msg_obj)

    def get_messages(self, conversation_id: int) -> List[Message]:
        """Retourne la liste des messages d'une conversation."""
        if not isinstance(conversation_id, int) or conversation_id < 0:
            raise ValueError("conversation_id invalide")

        # Utiliser directement la méthode du DAO
        return self.message_dao.get_messages_by_conversation(conversation_id)

    def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """Retourne un message par son id."""
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id invalide")

        return self.message_dao.get_by_id(message_id)

    def delete_all_messages_by_conversation(self, conversation_id: int) -> None:
        """Supprime tous les messages d'une conversation."""
        if not isinstance(conversation_id, int) or conversation_id < 0:
            raise ValueError("conversation_id invalide")

        self.message_dao.delete_by_conversation(conversation_id)

    def check_conversation_exists(self, conversation_id: int) -> bool:
        """Vérifie si une conversation existe."""
        return self.message_dao.count_messages_by_conversation(conversation_id) >= 0

    def get_last_message(self, conversation_id: int) -> Optional[Message]:
        """Récupère le dernier message d'une conversation."""
        if not isinstance(conversation_id, int) or conversation_id < 0:
            raise ValueError("conversation_id invalide")
        return self.message_dao.get_last_message(conversation_id)

    def validate_message_content(self, message: str) -> bool:
        """Valide le contenu d'un message de manière plus robuste."""
        if not message or not message.strip():
            raise ValueError("Message vide")
        if len(message) > 5000:
            raise ValueError("Message trop long (max 5000 caractères)")

        # Vérifications de sécurité supplémentaires
        forbidden_patterns = [
            "<script>", "javascript:", "data:",
            "vbscript:", "onclick=", "onerror=",
            "--", "/*", "*/", "@@"
        ]
        message_lower = message.lower()
        for pattern in forbidden_patterns:
            if pattern in message_lower:
                raise ValueError(f"Contenu non autorisé détecté: {pattern}")

        # Vérifier les caractères spéciaux
        if "\x00" in message:
            raise ValueError("Caractères nuls non autorisés")

        return True

    def send_agent_message(self, conversation_id: int, message: str) -> Message:
        """Envoie un message depuis l'agent."""
        self.validate_message_content(message)
        now = datetime.now(timezone.utc)
        msg_obj = Message(
            id_message=None,
            id_conversation=conversation_id,
            id_user=AGENT_USER_ID,  # id spécial pour l'agent
            datetime=now,
            message=message,
            is_from_agent=True,
        )
        return self.message_dao.create(msg_obj)

    def get_messages_paginated(
        self, conversation_id: int, page: int = 1, per_page: int = 50
    ) -> List[Message]:
        """Retourne une page de messages d'une conversation."""
        if page < 1:
            raise ValueError("Page invalide")
        return self.message_dao.get_messages_by_conversation_paginated(
            conversation_id, page, per_page
        )

    def count_messages(self, conversation_id: int) -> int:
        """Compte le nombre de messages dans une conversation."""
        return self.message_dao.count_messages_by_conversation(conversation_id)

    def search_messages(self, conversation_id: int, keyword: str) -> List[Message]:
        """Recherche des messages contenant un mot-clé."""
        if not keyword.strip():
            raise ValueError("Mot-clé de recherche requis")
        return self.message_dao.search_messages(conversation_id, keyword.strip())

    def get_messages_by_date_range(
        self, conversation_id: int, start_date: datetime, end_date: datetime
    ) -> List[Message]:
        """Récupère les messages dans une période donnée."""
        return self.message_dao.get_messages_by_date_range(
            conversation_id, start_date, end_date
        )

    def update_message(self, message_id: int, new_content: str) -> bool:
        """Met à jour le contenu d'un message existant."""
        message = self.get_message_by_id(message_id)
        if not message:
            raise ValueError("Message introuvable")

        self.validate_message_content(new_content)
        message.message = new_content
        return self.message_dao.update(message)

    def delete_message(self, message_id: int) -> bool:
        """Supprime un message unique."""
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id invalide")
        return self.message_dao.delete_by_id(message_id)
