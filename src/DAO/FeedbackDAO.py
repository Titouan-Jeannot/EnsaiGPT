import logging
from datetime import datetime
from typing import Optional

from src.DAO.DBConnector import DBConnection
from src.ObjetMetier.Feedback import Feedback


class FeedbackDAO:
    """DAO minimal pour Feedback — CRUD complet."""

    # --- CREATE -------------------------------------------------------------

    def create(self, feedback: Feedback) -> Feedback:
        """
        Crée un feedback dans la base de données.
        Remplit feedback.id_feedback avec l'identifiant généré.
        """
        query = """
        INSERT INTO feedback (id_user, id_message, is_like, comment, created_at)
        VALUES (%(id_user)s, %(id_message)s, %(is_like)s, %(comment)s, %(created_at)s)
        RETURNING id_feedback;
        """
        try:
            with DBConnection().connection as conn:
                with conn.cursor() as cur:
                    cur.execute(query, {
                        "id_user": feedback.id_user,
                        "id_message": feedback.id_message,
                        "is_like": feedback.is_like,
                        "comment": feedback.comment,
                        "created_at": feedback.created_at or datetime.utcnow(),
                    })
                    row = cur.fetchone()
                    feedback.id_feedback = row["id_feedback"] if row else None
            return feedback
        except Exception as e:
            logging.error(f"Erreur lors de la création du feedback : {e}")
            raise

    # --- READ ---------------------------------------------------------------

    def read(self, id_feedback: int) -> Optional[Feedback]:
        """Récupère un feedback par son identifiant."""
        query = "SELECT * FROM feedback WHERE id_feedback = %(id_feedback)s;"
        try:
            with DBConnection().connection as conn:
                with conn.cursor() as cur:
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
            logging.error(f"Erreur lecture feedback : {e}")
            raise

    # --- UPDATE -------------------------------------------------------------

    def update(self, feedback: Feedback) -> bool:
        """
        Met à jour un feedback existant.
        Retourne True si la mise à jour a modifié une ligne.
        """
        query = """
        UPDATE feedback
           SET id_user = %(id_user)s,
               id_message = %(id_message)s,
               is_like = %(is_like)s,
               comment = %(comment)s
         WHERE id_feedback = %(id_feedback)s;
        """
        try:
            with DBConnection().connection as conn:
                with conn.cursor() as cur:
                    cur.execute(query, {
                        "id_feedback": feedback.id_feedback,
                        "id_user": feedback.id_user,
                        "id_message": feedback.id_message,
                        "is_like": feedback.is_like,
                        "comment": feedback.comment,
                    })
                    return cur.rowcount == 1
        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour du feedback {feedback.id_feedback} : {e}")
            raise

    # --- DELETE -------------------------------------------------------------

    def delete(self, id_feedback: int) -> bool:
        """Supprime un feedback par son identifiant."""
        query = "DELETE FROM feedback WHERE id_feedback = %(id_feedback)s;"
        try:
            with DBConnection().connection as conn:
                with conn.cursor() as cur:
                    cur.execute(query, {"id_feedback": id_feedback})
                    return cur.rowcount > 0
        except Exception as e:
            logging.error(f"Erreur lors de la suppression du feedback {id_feedback} : {e}")
            raise
