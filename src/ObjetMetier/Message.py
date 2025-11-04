"""Objet métier Message."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Message:
    """Représente un message envoyé dans une conversation."""

    id_message: Optional[int] = None
    id_conversation: int = field(default=0)
    id_user: int = field(default=0)
    datetime_sent: datetime = field(default_factory=datetime.utcnow)
    message: str = field(default="")
    is_from_agent: bool = field(default=False)

    def __post_init__(self) -> None:
        if self.id_conversation <= 0:
            raise ValueError("id_conversation doit être positif")
        if self.id_user <= 0:
            raise ValueError("id_user doit être positif")
        if not isinstance(self.datetime_sent, datetime):
            raise ValueError("datetime_sent doit être un datetime")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("message doit être une chaîne non vide")

    def is_from_user(self) -> bool:
        """Retourne True si le message provient d'un utilisateur."""

        return not self.is_from_agent
