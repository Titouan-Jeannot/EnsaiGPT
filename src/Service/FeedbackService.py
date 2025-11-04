"""Service métier pour les feedbacks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.DAO.FeedbackDAO import FeedbackDAO
from src.DAO.Message_DAO import MessageDAO
from src.ObjetMetier.Feedback import Feedback


@dataclass(slots=True)
class FeedbackService:
    """Applique les règles métier sur les feedbacks."""

    feedback_dao: FeedbackDAO
    message_dao: MessageDAO

    def add_feedback(
        self,
        user_id: int,
        message_id: int,
        is_like: bool,
        comment: str | None = None,
    ) -> Feedback:
        if self.message_dao.read(message_id) is None:
            raise ValueError("Message introuvable")
        feedback = Feedback(
            id_feedback=None,
            id_user=user_id,
            id_message=message_id,
            is_like=is_like,
            comment=comment,
        )
        return self.feedback_dao.create(feedback)

    def get_feedback_by_message(self, message_id: int) -> List[Feedback]:
        return self.feedback_dao.list_by_message(message_id)

    def get_feedback_by_user(self, user_id: int) -> List[Feedback]:
        return self.feedback_dao.list_by_user(user_id)

    def count_likes(self, message_id: int) -> int:
        return self.feedback_dao.count_for_message(message_id, True)

    def count_dislikes(self, message_id: int) -> int:
        return self.feedback_dao.count_for_message(message_id, False)
