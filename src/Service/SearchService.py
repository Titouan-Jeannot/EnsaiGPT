from typing import List, Optional
from datetime import datetime

from ObjetMetier.Message import Message
from ObjetMetier.Conversation import Conversation
from DAO.MessageDAO import MessageDAO
from DAO.ConversationDAO import ConversationDAO
from DAO.CollaborationDAO import CollaborationDAO

class SearchService:
    """
    Service dédié à la recherche dans les messages et les conversations,
    en respectant les droits de collaboration de l'utilisateur.
    """

    def __init__(self, message_dao: MessageDAO, conversation_dao: ConversationDAO, collaboration_dao: CollaborationDAO):
        self.message_dao = message_dao
        self.conversation_dao = conversation_dao
        self.collaboration_dao = collaboration_dao

    def _get_user_accessible_conversation_ids(self, user_id: int) -> List[int]:
        """
        Récupère les IDs des conversations auxquelles l'utilisateur (user_id) a accès.
        """
        collaborations = self.collaboration_dao.find_by_user(user_id)

        # Filtre : On considère que 'BANNED' n'a pas accès à la recherche
        allowed_roles = {'ADMIN', 'WRITER', 'VIEWER'}

        conversation_ids = [
            c.id_conversation 
            for c in collaborations 
            if c.role.upper() in allowed_roles
        ]
        return conversation_ids

    def search_messages_by_keyword(self, user_id: int, keyword: str) -> List[Message]:
        conversation_ids = self._get_user_accessible_conversation_ids(user_id)
        if not conversation_ids:
            return []

        # Le DAO doit filtrer les messages de ces conversations par mot-clé
        return self.message_dao.search_by_keyword(keyword, conversation_ids)

    def search_messages_by_date(self, user_id: int, date: datetime) -> List[Message]:
        conversation_ids = self._get_user_accessible_conversation_ids(user_id)
        if not conversation_ids:
            return []

        # Le DAO doit filtrer les messages de ces conversations par date
        return self.message_dao.search_by_date(date, conversation_ids)

    def search_conversations_by_keyword(self, user_id: int, keyword: str) -> List[Conversation]:
        conversation_ids = self._get_user_accessible_conversation_ids(user_id)
        if not conversation_ids:
            return []

        # Le DAO doit filtrer les conversations par titre, mais uniquement parmi ces IDs
        return self.conversation_dao.search_by_title(keyword, conversation_ids)