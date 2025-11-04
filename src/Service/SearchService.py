"""Service de recherche de conversations et messages."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from src.DAO.CollaborationDAO import CollaborationDAO
from src.DAO.ConversationDAO import ConversationDAO
from src.DAO.Message_DAO import MessageDAO
from src.ObjetMetier.Conversation import Conversation
from src.ObjetMetier.Message import Message


@dataclass(slots=True)
class SearchService:
    """Recherche plein-texte simplifiée en mémoire."""

    message_dao: MessageDAO
    conversation_dao: ConversationDAO
    collaboration_dao: CollaborationDAO

    def _user_conversation_ids(self, user_id: int) -> List[int]:
        return [
            collab.id_conversation
            for collab in self.collaboration_dao.list_by_user(user_id)
            if collab.role != "BANNED"
        ]

    def search_messages_by_keyword(self, user_id: int, keyword: str) -> List[Message]:
        keyword_lower = keyword.lower()
        authorized_ids = set(self._user_conversation_ids(user_id))
        return [
            message
            for message in self.message_dao.list_by_user(user_id)
            if keyword_lower in message.message.lower()
        ] + [
            message
            for message in self.message_dao.list_all()
            if message.id_conversation in authorized_ids
            and keyword_lower in message.message.lower()
            and message.id_user != user_id
        ]

    def search_messages_by_date(self, user_id: int, target_date: datetime) -> List[Message]:
        authorized_ids = set(self._user_conversation_ids(user_id))
        return [
            message
            for message in self.message_dao.list_all()
            if message.id_conversation in authorized_ids
            and message.datetime_sent.date() == target_date.date()
        ]

    def search_conversations_by_keyword(self, user_id: int, keyword: str) -> List[Conversation]:
        keyword_lower = keyword.lower()
        authorized_ids = self._user_conversation_ids(user_id)
        conversations = self.conversation_dao.list_by_ids(authorized_ids)
        return [conv for conv in conversations if keyword_lower in conv.titre.lower()]
