"""DAO en mémoire pour les feedbacks."""
from __future__ import annotations

from typing import List, Optional

from src.DAO.base import BaseInMemoryDAO
from src.ObjetMetier.Feedback import Feedback


class FeedbackDAO(BaseInMemoryDAO[Feedback]):
    """Stocke les feedbacks en mémoire."""

    def __init__(self) -> None:
        super().__init__("id_feedback")

    def create(self, feedback: Feedback) -> Feedback:  # type: ignore[override]
        return super().create(feedback)

    def read(self, feedback_id: int) -> Optional[Feedback]:  # type: ignore[override]
        return super().read(feedback_id)

    def update(self, feedback: Feedback) -> bool:  # type: ignore[override]
        return super().update(feedback)

    def delete(self, feedback_id: int) -> bool:  # type: ignore[override]
        return super().delete(feedback_id)

    def list_by_message(self, message_id: int) -> List[Feedback]:
        return [
            fb
            for fb in self.list_all()
            if fb.id_message == message_id
        ]

    def list_by_user(self, user_id: int) -> List[Feedback]:
        return [fb for fb in self.list_all() if fb.id_user == user_id]

    def count_for_message(self, message_id: int, is_like: bool) -> int:
        return sum(
            1
            for fb in self.list_all()
            if fb.id_message == message_id and fb.is_like == is_like
        )
