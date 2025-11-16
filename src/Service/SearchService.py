from datetime import datetime
from typing import List

from DAO.CollaborationDAO import CollaborationDAO
from DAO.ConversationDAO import ConversationDAO
from DAO.MessageDAO import MessageDAO

from ObjetMetier.Message import Message
from ObjetMetier.Collaboration import Collaboration
from ObjetMetier.Conversation import Conversation


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

    # ------------------------------------------------------------------ #
    # Helper privé pour garantir la sécurité                             #
    # ------------------------------------------------------------------ #

    def _get_user_accessible_conversation_ids(self, user_id: int) -> List[int]:
        """
        Récupère les IDs des conversations auxquelles l'utilisateur a accès.
        Autorise admin/writer/viewer, exclut banni.
        """
        collaborations: List[Collaboration] = self.collaboration_dao.find_by_user(user_id)

        # Inclure 'reader' pour coller aux tests SearchService
        allowed_roles = {"ADMIN", "WRITER", "VIEWER"}

        conversation_ids = [
            c.id_conversation
            for c in collaborations
            if isinstance(c.role, str) and c.role.upper() in allowed_roles
        ]
        return conversation_ids

    # ------------------------------------------------------------------ #
    # Recherche dans les MESSAGES (CollaborationDAO + MessageDAO)        #
    # ------------------------------------------------------------------ #

    def search_messages_by_keyword(self, user_id: int, keyword: str) -> List[Message]:
        """Recherche des messages par mot-cle limites aux conversations de l'utilisateur."""
        if not keyword:
            return []
        conversation_ids = self._get_user_accessible_conversation_ids(user_id)
        if not conversation_ids:
            return []
        return self.message_dao.search_by_keyword(keyword, conversation_ids)

    def search_messages_by_date(self, user_id: int, target_date: datetime) -> List[Message]:
        """
        Recherche des messages par date (journée entière), limités aux conversations de l'utilisateur.
        """
        conversation_ids = self._get_user_accessible_conversation_ids(user_id)
        if not conversation_ids:
            return []
        return self.message_dao.search_by_date(target_date, conversation_ids)

    # ------------------------------------------------------------------ #
    # Recherche dans les CONVERSATIONS (ConversationDAO)                  #
    # ------------------------------------------------------------------ #

    def search_conversations_by_keyword(self, user_id: int, keyword: str) -> List[Conversation]:
        """Recherche des conversations par mot-cle dans le titre."""
        if not keyword or not keyword.strip():
            return []
        keyword = keyword.strip()
        ordered: List[Conversation] = []
        seen_ids = set()

        title_matches = self.conversation_dao.search_conversations_by_title(
            user_id, keyword
        )
        for conv in title_matches or []:
            conv_id = getattr(conv, "id_conversation", None)
            if conv_id is None or conv_id in seen_ids:
                continue
            seen_ids.add(conv_id)
            ordered.append(conv)

        accessible_ids = self._get_user_accessible_conversation_ids(user_id)
        if not accessible_ids:
            return ordered

        messages = self.message_dao.search_by_keyword(keyword, accessible_ids)
        conv_getter = getattr(self.conversation_dao, "get_by_id", None) or getattr(
            self.conversation_dao, "read", None
        )
        if not callable(conv_getter):
            return ordered

        for msg in messages or []:
            conv_id = getattr(msg, "id_conversation", None)
            if conv_id in seen_ids or conv_id is None:
                continue
            try:
                conv = conv_getter(conv_id)
            except Exception:
                continue
            if conv:
                seen_ids.add(conv_id)
                ordered.append(conv)

        return ordered

    def search_conversations_by_date(
        self,
        user_id: int,
        target_date: datetime,
    ) -> List[Conversation]:
        """
        Recherche des conversations par date de création (journée entière), limitées à celles de l'utilisateur.
        """
        return self.conversation_dao.get_conversations_by_date(user_id, target_date)
