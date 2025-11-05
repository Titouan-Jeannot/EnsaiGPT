from datetime import datetime
from typing import List

from src.DAO.CollaborationDAO import CollaborationDAO
from src.DAO.ConversationDAO import ConversationDAO
from src.DAO.MessageDAO import MessageDAO

try:  # pragma: no cover - compatibilite ancien dossier
    from src.ObjetMetier.Message import Message
except ImportError:  # pragma: no cover
    from src.Objet_Metier.Message import Message  # type: ignore
from src.ObjetMetier.Collaboration import Collaboration
from src.ObjetMetier.Conversation import Conversation


class SearchService:
    """
    Service dedie a la recherche dans les messages et les conversations.
    Toutes les recherches sont filtrees pour n'afficher que le contenu
    accessible par l'utilisateur (via CollaborationDAO).
    """

    def __init__(
        self,
        message_dao: MessageDAO,
        conversation_dao: ConversationDAO,
        collaboration_dao: CollaborationDAO,
    ):
        self.message_dao = message_dao
        self.conversation_dao = conversation_dao
        self.collaboration_dao = collaboration_dao

    def _get_user_accessible_conversation_ids(self, user_id: int) -> List[int]:
        """
        Recupere les identifiants des conversations accessibles par l'utilisateur.
        """
        collaborations: List[Collaboration] = self.collaboration_dao.find_by_user(user_id)
        allowed_roles = {"ADMIN", "WRITER", "VIEWER"}
        return [
            collab.id_conversation
            for collab in collaborations
            if collab.role.upper() in allowed_roles
        ]

    def search_messages_by_keyword(self, user_id: int, keyword: str) -> List[Message]:
        """Recherche des messages par mot-cle limites aux conversations de l'utilisateur."""
        if not keyword:
            return []
        conversation_ids = self._get_user_accessible_conversation_ids(user_id)
        if not conversation_ids:
            return []
        return self.message_dao.search_by_keyword(keyword, conversation_ids)

    def search_messages_by_date(self, user_id: int, target_date: datetime) -> List[Message]:
        """Recherche des messages par date (jour complet)."""
        conversation_ids = self._get_user_accessible_conversation_ids(user_id)
        if not conversation_ids:
            return []
        return self.message_dao.search_by_date(target_date, conversation_ids)

    def search_conversations_by_keyword(self, user_id: int, keyword: str) -> List[Conversation]:
        """Recherche des conversations par mot-cle dans le titre."""
        if not keyword:
            return []
        return self.conversation_dao.search_conversations_by_title(user_id, keyword)

    def search_conversations_by_date(
        self,
        user_id: int,
        target_date: datetime,
    ) -> List[Conversation]:
        """Recherche des conversations par date de creation."""
        return self.conversation_dao.get_conversations_by_date(user_id, target_date)
