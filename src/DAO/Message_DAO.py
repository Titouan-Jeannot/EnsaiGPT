"""DAO en mémoire pour les messages."""
from __future__ import annotations

from typing import List, Optional

from src.DAO.base import BaseInMemoryDAO
from src.ObjetMetier.Message import Message


class MessageDAO(BaseInMemoryDAO[Message]):
    """Gère les messages des conversations."""

    def __init__(self) -> None:
        super().__init__("id_message")

    def create(self, message: Message) -> Message:  # type: ignore[override]
        return super().create(message)

    def read(self, message_id: int) -> Optional[Message]:  # type: ignore[override]
        return super().read(message_id)

    def update(self, message: Message) -> bool:  # type: ignore[override]
        return super().update(message)

    def delete(self, message_id: int) -> bool:  # type: ignore[override]
        return super().delete(message_id)

    def list_by_conversation(self, conversation_id: int) -> List[Message]:
        return [
            msg
            for msg in self.list_all()
            if msg.id_conversation == conversation_id
        ]

    def list_by_user(self, user_id: int) -> List[Message]:
        return [msg for msg in self.list_all() if msg.id_user == user_id]

    def delete_by_conversation(self, conversation_id: int) -> int:
        to_delete = [
            msg.id_message
            for msg in self.list_all()
            if msg.id_conversation == conversation_id
        ]
        for message_id in to_delete:
            super().delete(message_id)
        return len(to_delete)
