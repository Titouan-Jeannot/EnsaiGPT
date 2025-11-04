"""Objet métier Feedback."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Feedback:
    """Exprime une réaction d'utilisateur à un message."""

    id_feedback: Optional[int] = None
    id_user: int = field(default=0)
    id_message: int = field(default=0)
    is_like: bool = field(default=True)
    comment: Optional[str] = field(default=None)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if self.id_user <= 0:
            raise ValueError("id_user doit être positif")
        if self.id_message <= 0:
            raise ValueError("id_message doit être positif")
        if not isinstance(self.is_like, bool):
            raise ValueError("is_like doit être booléen")
        if self.comment is not None and not isinstance(self.comment, str):
            raise ValueError("comment doit être une chaîne ou None")
        if not isinstance(self.created_at, datetime):
            raise ValueError("created_at doit être un datetime")
