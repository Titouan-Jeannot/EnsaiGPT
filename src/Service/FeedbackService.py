import logging
from datetime import datetime
from typing import List

from DAO.FeedbackDAO import FeedbackDAO
from ObjetMetier.Feedback import Feedback
from Utils.Singleton import Singleton
from Utils.log_decorator import log


class FeedbackService(metaclass=Singleton):
    """
    Service pour gérer les feedbacks (likes / dislikes + commentaire optionnel).

    Aucun accès direct à la BDD : tout passe par FeedbackDAO.
    """

    def __init__(self, dao: FeedbackDAO = None):
        self.dao = dao or FeedbackDAO()

    # ------------------------------ Create -------------------------------- #

    @log
    def add_feedback(self, user_id: int, message_id: int, is_like: bool, comment: str | None) -> Feedback:
        """Valide puis délègue la création à la DAO."""
        if not isinstance(user_id, int) or user_id < 0:
            raise ValueError("user_id doit être un entier positif")
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id doit être un entier positif")
        if not isinstance(is_like, bool):
            raise ValueError("is_like doit être un booléen")
        if comment is not None and not isinstance(comment, str):
            raise ValueError("comment doit être une chaîne ou None")

        try:
            to_create = Feedback(
                id_feedback=0,               # conforme à ta classe (>=0)
                id_user=user_id,
                id_message=message_id,
                is_like=is_like,
                comment=comment,
                created_at=datetime.now(),
            )
            return self.dao.create(to_create)
        except Exception as e:
            logging.error(
                f"FeedbackService.add_feedback: échec création (user={user_id}, msg={message_id}) : {e}"
            )
            raise

    # --------------------------- Lists / Reads ----------------------------- #

    @log
    def get_feedback_by_message(self, message_id: int) -> List[Feedback]:
        """Retourne tous les feedbacks liés à un message."""
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id doit être un entier positif")
        return self.dao.find_by_message(message_id)

    @log
    def get_feedback_by_user(self, user_id: int) -> List[Feedback]:
        """Retourne tous les feedbacks laissés par un utilisateur."""
        if not isinstance(user_id, int) or user_id < 0:
            raise ValueError("user_id doit être un entier positif")
        return self.dao.find_by_user(user_id)

    # ------------------------------ Aggregates ----------------------------- #

    @log
    def count_likes(self, message_id: int) -> int:
        """Compte les likes associés à un message."""
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id doit être un entier positif")
        return self.dao.count_likes(message_id)

    @log
    def count_dislikes(self, message_id: int) -> int:
        """Compte les dislikes associés à un message."""
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id doit être un entier positif")
        return self.dao.count_dislikes(message_id)
