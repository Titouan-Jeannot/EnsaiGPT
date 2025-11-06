import logging
from typing import List, Optional
from psycopg2.extras import RealDictCursor

from src.DAO.DBConnector import DBConnection
from src.ObjetMetier.Feedback import Feedback


class FeedbackDAO:
    """DAO pour Feedback — CRUD + recherches + agrégats."""

    # --- CREATE -------------------------------------------------------------

    def create(self, feedback: Feedback) -> Feedback:
        """
        Crée un feedback et renvoie l'objet persisté.
        Utilise NOW() côté SQL si created_at fourni est None (par sécurité).
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
            if not row:
                raise RuntimeError("Insertion feedback: RETURNING vide.")
            return created
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
            return self._row_to_feedback(row)
        except Exception as e:
            logging.error(f"Erreur lecture feedback {id_feedback} : {e}")
            raise

    # --- UPDATE -------------------------------------------------------------

    def update(self, feedback: Feedback) -> bool:
        """Met à jour un feedback existant."""
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

    # --- LISTES / RECHERCHES -----------------------------------------------

    def find_by_message(self, message_id: int) -> List[Feedback]:
        """Retourne tous les feedbacks d’un message (ordre chronologique)."""
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
            logging.error(f"Erreur find_by_message(message_id={message_id}) : {e}")
            raise

    def find_by_user(self, user_id: int) -> List[Feedback]:
        """Retourne tous les feedbacks d’un utilisateur (ordre chronologique)."""
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
            logging.error(f"Erreur find_by_user(user_id={user_id}) : {e}")
            raise

    # --- AGRÉGATS -----------------------------------------------------------

    def count_likes(self, message_id: int) -> int:
        """Compte les likes d’un message."""
        query = "SELECT COUNT(*) AS n FROM feedback WHERE id_message = %(m)s AND is_like = TRUE;"
        try:
            with DBConnection().connection as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, {"m": message_id})
                    row = cur.fetchone()
            return int(row["n"]) if row and row.get("n") is not None else 0
        except Exception as e:
            logging.error(f"Erreur count_likes(message_id={message_id}) : {e}")
            raise

    def count_dislikes(self, message_id: int) -> int:
        """Compte les dislikes d’un message."""
        query = "SELECT COUNT(*) AS n FROM feedback WHERE id_message = %(m)s AND is_like = FALSE;"
        try:
            with DBConnection().connection as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, {"m": message_id})
                    row = cur.fetchone()
            return int(row["n"]) if row and row.get("n") is not None else 0
        except Exception as e:
            logging.error(f"Erreur count_dislikes(message_id={message_id}) : {e}")
            raise
