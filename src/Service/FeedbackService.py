# src/Service/FeedbackService.py

import logging
from datetime import datetime
from typing import List

from psycopg2.extras import RealDictCursor

from src.DAO.DBConnector import DBConnection
from src.DAO.FeedbackDAO import FeedbackDAO
from src.ObjetMetier.Feedback import Feedback
from src.Utils.Singleton import Singleton
from src.Utils.log_decorator import log


class FeedbackService(metaclass=Singleton):
    """
    Service pour gérer les feedbacks (likes / dislikes + commentaire optionnel).

    Méthodes conformes au diagramme UML :
      - add_feedback(user_id, message_id, is_like, comment) -> Feedback
      - get_feedback_by_message(message_id) -> List[Feedback]
      - get_feedback_by_user(user_id) -> List[Feedback]
      - count_likes(message_id) -> int
      - count_dislikes(message_id) -> int
    """

    def __init__(self):
        self.dao = FeedbackDAO()

    # ------------------------------------------------------------------ #
    # Create                                                             #
    # ------------------------------------------------------------------ #
    @log
    def add_feedback(self, user_id: int, message_id: int, is_like: bool, comment: str | None) -> Feedback:
        """
        Ajoute un feedback et renvoie l'objet persisté (avec id_feedback et created_at remplis).

        Notes d’implémentation :
        - La classe ObjetMetier.Feedback exige un id_feedback >= 0 et un created_at non nul.
          On passe donc id_feedback=0 et created_at=datetime.now() (l’INSERT utilise NOW() côté SQL,
          puis on récupère les vraies valeurs via RETURNING).
        """
        # (Petits) garde-fous typés, pour des messages d'erreur plus explicites
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
                id_feedback=0,
                id_user=user_id,
                id_message=message_id,
                is_like=is_like,
                comment=comment,
                created_at=datetime.now(),
            )
            created = self.dao.create(to_create)
            return created
        except Exception as e:
            logging.error(f"FeedbackService.add_feedback: échec création feedback (user={user_id}, "
                          f"message={message_id}) : {e}")
            raise

    # ------------------------------------------------------------------ #
    # Reads / Lists                                                      #
    # ------------------------------------------------------------------ #
    @log
    def get_feedback_by_message(self, message_id: int) -> List[Feedback]:
        """
        Retourne la liste des feedbacks d’un message (ordre chronologique croissant).
        """
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id doit être un entier positif")

        query = """
            SELECT id_feedback, id_user, id_message, is_like, comment, created_at
              FROM feedback
             WHERE id_message = %(m)s
             ORDER BY created_at ASC, id_feedback ASC;
        """
        try:
            with DBConnection().connection as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, {"m": message_id})
                    rows = cur.fetchall() or []
            return [
                Feedback(
                    id_feedback=r["id_feedback"],
                    id_user=r["id_user"],
                    id_message=r["id_message"],
                    is_like=r["is_like"],
                    comment=r["comment"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]
        except Exception as e:
            logging.error(f"FeedbackService.get_feedback_by_message: erreur (message_id={message_id}) : {e}")
            raise

    @log
    def get_feedback_by_user(self, user_id: int) -> List[Feedback]:
        """
        Retourne la liste des feedbacks d’un utilisateur (ordre chronologique croissant).
        """
        if not isinstance(user_id, int) or user_id < 0:
            raise ValueError("user_id doit être un entier positif")

        query = """
            SELECT id_feedback, id_user, id_message, is_like, comment, created_at
              FROM feedback
             WHERE id_user = %(u)s
             ORDER BY created_at ASC, id_feedback ASC;
        """
        try:
            with DBConnection().connection as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, {"u": user_id})
                    rows = cur.fetchall() or []
            return [
                Feedback(
                    id_feedback=r["id_feedback"],
                    id_user=r["id_user"],
                    id_message=r["id_message"],
                    is_like=r["is_like"],
                    comment=r["comment"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]
        except Exception as e:
            logging.error(f"FeedbackService.get_feedback_by_user: erreur (user_id={user_id}) : {e}")
            raise

    # ------------------------------------------------------------------ #
    # Aggregations                                                       #
    # ------------------------------------------------------------------ #
    @log
    def count_likes(self, message_id: int) -> int:
        """Nombre de likes pour un message."""
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id doit être un entier positif")

        query = "SELECT COUNT(*) AS n FROM feedback WHERE id_message = %(m)s AND is_like = TRUE;"
        try:
            with DBConnection().connection as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, {"m": message_id})
                    row = cur.fetchone()
            return int(row["n"]) if row and row.get("n") is not None else 0
        except Exception as e:
            logging.error(f"FeedbackService.count_likes: erreur (message_id={message_id}) : {e}")
            raise

    @log
    def count_dislikes(self, message_id: int) -> int:
        """Nombre de dislikes pour un message."""
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id doit être un entier positif")

        query = "SELECT COUNT(*) AS n FROM feedback WHERE id_message = %(m)s AND is_like = FALSE;"
        try:
            with DBConnection().connection as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, {"m": message_id})
                    row = cur.fetchone()
            return int(row["n"]) if row and row.get("n") is not None else 0
        except Exception as e:
            logging.error(f"FeedbackService.count_dislikes: erreur (message_id={message_id}) : {e}")
            raise
