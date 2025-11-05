import logging
from datetime import datetime
from typing import Optional

from psycopg2.extras import RealDictCursor

from src.DAO.DBConnector import DBConnection
from src.ObjetMetier.Feedback import Feedback


class FeedbackDAO:
    """DAO minimal pour Feedback — CRUD complet."""

    # --- CREATE -------------------------------------------------------------

    def create(self, feedback: Feedback) -> Feedback:
        """
        Crée un feedback dans la base et renvoie l'objet (id rempli).
        Si feedback.created_at est None, on utilise NOW() côté SQL.
        """
        query = """
            INSERT INTO feedback (id_user, id_message, is_like, comment, created_at)
            VALUES (%(id_user)s, %(id_message)s, %(is_like)s, %(comment)s,
                    COALESCE(%(created_at)s, NOW()))
            RETURNING id_feedback, id_user, id_message, is_like, comment, created_at;
        """
        try:
            with DBConnection().connection as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        query,
                        {
                            "id_user": feedback.id_user,
                            "id_message": feedback.id_message,
                            "is_like": feedback.is_like,
                            "comment": feedback.comment,
                            "created_at": feedback.created_at,
                        },
                    )
                    row = cur.fetchone()
                    # le context manager commit automatiquement si pas d'exception
            if not row:
                raise RuntimeError("Insertion feedback: RETURNING vide.")
            return Feedback(
                id_feedback=row["id_feedback"],
                id_user=row["id_user"],
                id_message=row["id_message"],
                is_like=row["is_like"],
                comment=row["comment"],
                created_at=row["created_at"],
            )
        except Exception as e:
            logging.error(f"Erreur lors de la création du feedback : {e}")
            raise

    # --- READ ---------------------------------------------------------------

    def read(self, id_feedback: int) -> Optional[Feedback]:
        """Récupère un feedback par son identifiant."""
        query = """
            SELECT id_feedback, id_user, id_message, is_like, comment, created_at
              FROM feedback
             WHERE id_feedback = %(id_feedback)s;
        """
        try:
            with DBConnection().connection as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, {"id_feedback": id_feedback})
                    row = cur.fetchone()
            if not row:
                return None
            return Feedback(
                id_feedback=row["id_feedback"],
                id_user=row["id_user"],
                id_message=row["id_message"],
                is_like=row["is_like"],
                comment=row["comment"],
                created_at=row["created_at"],
            )
        except Exception as e:
            logging.error(f"Erreur lecture feedback {id_feedback} : {e}")
            raise

    # --- UPDATE -------------------------------------------------------------

    def update(self, feedback: Feedback) -> bool:
        """
        Met à jour un feedback existant (tous les champs éditables).
        Retourne True si une ligne a été modifiée.
        """
        query = """
            UPDATE feedback
               SET id_user   = %(id_user)s,
                   id_message= %(id_message)s,
                   is_like   = %(is_like)s,
                   comment   = %(comment)s
             WHERE id_feedback = %(id_feedback)s;
        """
        try:
            with DBConnection().connection as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        query,
                        {
                            "id_feedback": feedback.id_feedback,
                            "id_user": feedback.id_user,
                            "id_message": feedback.id_message,
                            "is_like": feedback.is_like,
                            "comment": feedback.comment,
                        },
                    )
                    return cur.rowcount == 1
        except Exception as e:
            logging.error(
                f"Erreur lors de la mise à jour du feedback {feedback.id_feedback} : {e}"
            )
            raise

    # --- DELETE -------------------------------------------------------------

    def delete(self, id_feedback: int) -> bool:
        """Supprime un feedback par son identifiant."""
        query = "DELETE FROM feedback WHERE id_feedback = %(id_feedback)s;"
        try:
            with DBConnection().connection as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, {"id_feedback": id_feedback})
                    return cur.rowcount > 0
        except Exception as e:
            logging.error(f"Erreur lors de la suppression du feedback {id_feedback} : {e}")
            raise
