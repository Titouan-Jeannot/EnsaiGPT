"""DAO en mémoire pour les conversations."""
from __future__ import annotations

from datetime import date
from typing import Iterable, List, Optional

from src.DAO.base import BaseInMemoryDAO
from src.ObjetMetier.Conversation import Conversation


class ConversationDAO(BaseInMemoryDAO[Conversation]):
    """Gestion simple des conversations en mémoire."""

    def __init__(self) -> None:
        super().__init__("id_conversation")

    def create(self, conversation: Conversation) -> Conversation:  # type: ignore[override]
        return super().create(conversation)

    def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        return self.read(conversation_id)

    def update(self, conversation: Conversation) -> bool:  # type: ignore[override]
        return super().update(conversation)

    def delete(self, conversation_id: int) -> bool:  # type: ignore[override]
        return super().delete(conversation_id)

    def list_by_ids(self, conversation_ids: Iterable[int]) -> List[Conversation]:
        ids = set(conversation_ids)
        return [conv for conv in self.list_all() if conv.id_conversation in ids]

    def list_by_date(self, target_date: date) -> List[Conversation]:
        return [
            conv
            for conv in self.list_all()
            if conv.created_at.date() == target_date
        ]

    def list_by_title(self, keyword: str) -> List[Conversation]:
        keyword_lower = keyword.lower()
        return [
            conv
            for conv in self.list_all()
            if keyword_lower in conv.titre.lower()
        ]
