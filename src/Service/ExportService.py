"""Service d'export des conversations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.DAO.ConversationDAO import ConversationDAO
from src.DAO.Message_DAO import MessageDAO
from src.ObjetMetier.Conversation import Conversation
from src.ObjetMetier.Message import Message


@dataclass(slots=True)
class ExportService:
    """Produit une représentation textuelle d'une conversation."""

    conversation_dao: ConversationDAO
    message_dao: MessageDAO

    def export_conversation(self, conversation_id: int, user_id: int) -> str:
        conversation = self.conversation_dao.get_by_id(conversation_id)
        if conversation is None:
            raise ValueError("Conversation introuvable")
        messages = self.message_dao.list_by_conversation(conversation_id)
        return self.format_conversation(conversation, messages)

    def format_conversation(
        self, conversation: Conversation, messages: List[Message]
    ) -> str:
        header = f"Conversation: {conversation.titre}\n"
        header += f"Créée le: {conversation.created_at.isoformat()}\n"
        lines = [header, "Messages:"]
        for message in sorted(messages, key=lambda msg: msg.datetime_sent):
            author = "Agent" if message.is_from_agent else f"User#{message.id_user}"
            lines.append(
                f"[{message.datetime_sent.isoformat()}] {author}: {message.message}"
            )
        return "\n".join(lines)
