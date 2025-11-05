"""
Service métier pour la gestion des feedbacks.

Cette couche encapsule la validation légère et délègue la persistance
au FeedbackDAO fourni.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from src.DAO.FeedbackDAO import FeedbackDAO
from src.ObjetMetier.Feedback import Feedback


class FeedbackService:
    """Service thin-wrapper autour de FeedbackDAO."""

    def __init__(self, feedback_dao: Optional[FeedbackDAO] = None) -> None:
        self.feedback_dao = feedback_dao or FeedbackDAO()

    def add_feedback(
        self,
        user_id: int,
        message_id: int,
        is_like: bool,
        comment: str = "",
    ) -> Feedback:
        """
        Crée un nouveau feedback et le persiste.

        Valide les entrées minimales avant d'appeler le DAO.
        """
        if not isinstance(user_id, int) or user_id < 0:
            raise ValueError("user_id invalide")
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id invalide")
        if not isinstance(is_like, bool):
            raise ValueError("is_like doit être booléen")

        comment = (comment or "").strip()

        # Feedback demande un identifiant non négatif : on utilise 0 comme placeholder.
        feedback = Feedback(
            id_feedback=0,
            id_user=user_id,
            id_message=message_id,
            is_like=is_like,
            comment=comment,
            created_at=datetime.now(),
        )
        return self.feedback_dao.create(feedback)

    def get_feedback_by_message(self, message_id: int) -> List[Feedback]:
        """Retourne tous les feedbacks liés à un message."""
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id invalide")
        return self.feedback_dao.list_by_message(message_id)

    def get_feedback_by_user(self, user_id: int) -> List[Feedback]:
        """Retourne tous les feedbacks laissés par un utilisateur."""
        if not isinstance(user_id, int) or user_id < 0:
            raise ValueError("user_id invalide")
        return self.feedback_dao.list_by_user(user_id)

    def count_likes(self, message_id: int) -> int:
        """Compte les likes associés à un message."""
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id invalide")
        return self.feedback_dao.count_by_message(message_id, True)

    def count_dislikes(self, message_id: int) -> int:
        """Compte les dislikes associés à un message."""
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id invalide")
        return self.feedback_dao.count_by_message(message_id, False)
