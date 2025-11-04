"""DAO en mémoire pour les collaborations."""
from __future__ import annotations

from typing import List, Optional

from src.DAO.base import BaseInMemoryDAO
from src.ObjetMetier.Collaboration import Collaboration


class CollaborationDAO(BaseInMemoryDAO[Collaboration]):
    """Gère les collaborations entre utilisateurs et conversations."""

    def __init__(self) -> None:
        super().__init__("id_collaboration")

    def create(self, collaboration: Collaboration) -> Collaboration:  # type: ignore[override]
        existing = self.find_by_user_and_conversation(
            collaboration.id_user, collaboration.id_conversation
        )
        if existing is not None:
            raise ValueError("Collaboration déjà existante")
        return super().create(collaboration)

    def update(self, collaboration: Collaboration) -> bool:  # type: ignore[override]
        return super().update(collaboration)

    def delete(self, collab_id: int) -> bool:  # type: ignore[override]
        return super().delete(collab_id)

    def find_by_user_and_conversation(
        self, user_id: int, conversation_id: int
    ) -> Optional[Collaboration]:
        for collab in self.list_all():
            if collab.id_user == user_id and collab.id_conversation == conversation_id:
                return collab
        return None

    def list_by_conversation(self, conversation_id: int) -> List[Collaboration]:
        return [
            collab
            for collab in self.list_all()
            if collab.id_conversation == conversation_id
        ]

    def list_by_user(self, user_id: int) -> List[Collaboration]:
        return [collab for collab in self.list_all() if collab.id_user == user_id]
