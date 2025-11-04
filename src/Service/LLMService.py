"""Service simulant un modèle de langage."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.DAO.ConversationDAO import ConversationDAO
from src.DAO.Message_DAO import MessageDAO
from src.ObjetMetier.Message import Message


@dataclass(slots=True)
class LLMService:
    """Petite simulation d'un LLM pour les tests."""

    conversation_dao: ConversationDAO
    message_dao: MessageDAO

    def generate_reponse(
        self,
        message_user: str,
        temperature: float = 0.7,
        max_tokens: int = 128,
        model_version: str = "mock-1",
    ) -> str:
        prompt = message_user.strip()
        truncated = prompt[:max_tokens]
        return f"[{model_version} @ {temperature:.1f}] {truncated[::-1]}"

    def summarize_conversation(self, conversation_id: int) -> str:
        messages = self.message_dao.list_by_conversation(conversation_id)
        if not messages:
            return "Conversation vide."
        summary = self._build_summary(messages)
        return f"Résumé ({len(messages)} messages): {summary}"

    def _build_summary(self, messages: List[Message]) -> str:
        last_messages = sorted(messages, key=lambda msg: msg.datetime_sent)[-3:]
        return " | ".join(message.message for message in last_messages)
