"""Objet métier Conversation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Conversation:
    """Représente une conversation enregistrée."""

    id_conversation: Optional[int] = None
    titre: str = field(default="")
    created_at: datetime = field(default_factory=datetime.utcnow)
    setting_conversation: str = field(default="")
    token_viewer: str = field(default="")
    token_writter: str = field(default="")
    is_active: bool = field(default=True)

    def __post_init__(self) -> None:
        if not isinstance(self.titre, str) or not self.titre:
            raise ValueError("Le titre doit être une chaîne non vide")
        if not isinstance(self.setting_conversation, str):
            raise ValueError("Le prompt de conversation doit être une chaîne")
        if not isinstance(self.token_viewer, str) or not self.token_viewer:
            raise ValueError("token_viewer doit être une chaîne non vide")
        if not isinstance(self.token_writter, str) or not self.token_writter:
            raise ValueError("token_writter doit être une chaîne non vide")
        if not isinstance(self.is_active, bool):
            raise ValueError("is_active doit être booléen")

    def deactivate(self) -> None:
        """Marque la conversation comme inactive."""

        self.is_active = False
