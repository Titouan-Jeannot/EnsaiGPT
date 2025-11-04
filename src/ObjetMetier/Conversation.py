"""Définition de l'objet métier Conversation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Conversation:
    """Représente une conversation persistée dans la base de données."""

    id_conversation: int | None
    titre: str
    created_at: datetime
    setting_conversation: str
    token_viewer: str
    token_writter: str
    is_active: bool

    @classmethod
    def from_dict(cls, data: dict) -> "Conversation":
        """Fabrique une conversation à partir d'un dictionnaire."""
        return cls(
            id_conversation=data.get("id_conversation"),
            titre=data.get("titre", ""),
            created_at=data.get("created_at"),
            setting_conversation=data.get("setting_conversation", ""),
            token_viewer=data.get("token_viewer", ""),
            token_writter=data.get("token_writter", ""),
            is_active=bool(data.get("is_active", True)),
        )
