"""Service métier pour les messages."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.DAO.CollaborationDAO import CollaborationDAO
from src.DAO.ConversationDAO import ConversationDAO
from src.DAO.Message_DAO import MessageDAO
from src.ObjetMetier.Message import Message


@dataclass(slots=True)
class MessageService:
    """Gère l'envoi et la récupération des messages."""

    message_dao: MessageDAO
    conversation_dao: ConversationDAO
    collaboration_dao: CollaborationDAO

    def send_message(
        self,
        conversation_id: int,
        user_id: int,
        content: str,
        *,
        is_from_agent: bool = False,
    ) -> Message:
        conversation = self.conversation_dao.get_by_id(conversation_id)
        if conversation is None or not conversation.is_active:
            raise ValueError("Conversation introuvable ou inactive")
        collab = self.collaboration_dao.find_by_user_and_conversation(user_id, conversation_id)
        if not is_from_agent and (collab is None or not collab.can_write()):
            raise PermissionError("L'utilisateur n'a pas le droit d'écrire")
        content = content.strip()
        if not content:
            raise ValueError("Le message ne peut pas être vide")
        message = Message(
            id_message=None,
            id_conversation=conversation_id,
            id_user=user_id,
            datetime_sent=datetime.utcnow(),
            message=content,
            is_from_agent=is_from_agent,
        )
        return self.message_dao.create(message)

    def get_messages(self, conversation_id: int) -> List[Message]:
        messages = self.message_dao.list_by_conversation(conversation_id)
        return sorted(messages, key=lambda msg: msg.datetime_sent)

    def get_message_by_id(self, message_id: int) -> Optional[Message]:
        return self.message_dao.read(message_id)

    def delete_all_messages_by_conversation(self, conversation_id: int) -> int:
        return self.message_dao.delete_by_conversation(conversation_id)
