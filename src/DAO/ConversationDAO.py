"""Module DAO pour la gestion des conversations."""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import List, Optional

from src.DAO.DBConnector import DBConnection
from src.Utils.Singleton import Singleton
from src.Utils.log_decorator import log

try:
    from ObjetMetier.Conversation import Conversation
except Exception:  # pragma: no cover - compatibilité exécution
    from src.ObjetMetier.Conversation import Conversation


class ConversationDAO(metaclass=Singleton):
    """Accès aux données pour les conversations."""

    # ------------------------------------------------------------------
    # Méthodes privées utilitaires
    # ------------------------------------------------------------------
    @staticmethod
    def _build_conversation(row: dict) -> Conversation:
        """Construit un objet :class:`Conversation` à partir d'un dictionnaire."""
        return Conversation(
            id_conversation=row.get("id_conversation"),
            titre=row.get("titre"),
            created_at=row.get("created_at"),
            setting_conversation=row.get("setting_conversation", ""),
            token_viewer=row.get("token_viewer"),
            token_writter=row.get("token_writter"),
            is_active=row.get("is_active", True),
        )

    # ------------------------------------------------------------------
    # CRUD et opérations principales
    # ------------------------------------------------------------------
    @log
    def create(self, conversation: Conversation, user_id: int) -> Conversation:
        """Insère une nouvelle conversation en base."""
        # NB : user_id est conservé pour pouvoir, à terme, créer automatiquement
        # la collaboration associée. Cette fonctionnalité est déléguée au service.
        payload = {
            "titre": conversation.titre,
            "created_at": conversation.created_at,
            "setting_conversation": conversation.setting_conversation,
            "token_viewer": conversation.token_viewer,
            "token_writter": conversation.token_writter,
            "is_active": conversation.is_active,
        }
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO conversations
                            (titre, created_at, setting_conversation, token_viewer, token_writter, is_active)
                        VALUES
                            (%(titre)s, %(created_at)s, %(setting_conversation)s, %(token_viewer)s, %(token_writter)s, %(is_active)s)
                        RETURNING id_conversation;
                        """,
                        payload,
                    )
                    res = cursor.fetchone()
            if not res or "id_conversation" not in res:
                raise ValueError("Création de la conversation impossible (id manquant)")
            conversation.id_conversation = res["id_conversation"]
            return conversation
        except Exception as exc:  # pragma: no cover - log + re-raise testé via ValueError
            logging.error("Erreur lors de la création d'une conversation : %s", exc)
            raise ValueError("Erreur lors de la création de la conversation") from exc

    @log
    def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """Retourne une conversation par son identifiant."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * FROM conversations
                        WHERE id_conversation = %(id_conversation)s;
                        """,
                        {"id_conversation": conversation_id},
                    )
                    row = cursor.fetchone()
            if not row:
                return None
            return self._build_conversation(row)
        except Exception as exc:  # pragma: no cover - comportement identique quel que soit exc
            logging.error(
                "Erreur lors de la récupération de la conversation %s : %s",
                conversation_id,
                exc,
            )
            return None

    @log
    def update_title(self, conversation_id: int, new_title: str) -> bool:
        """Met à jour le titre d'une conversation."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE conversations
                           SET titre = %(titre)s
                         WHERE id_conversation = %(id_conversation)s;
                        """,
                        {"titre": new_title, "id_conversation": conversation_id},
                    )
                    return cursor.rowcount == 1
        except Exception as exc:
            logging.error(
                "Erreur lors de la mise à jour du titre de la conversation %s : %s",
                conversation_id,
                exc,
            )
            return False

    @log
    def delete(self, conversation_id: int) -> bool:
        """Supprime une conversation."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM conversations
                         WHERE id_conversation = %(id_conversation)s;
                        """,
                        {"id_conversation": conversation_id},
                    )
                    return cursor.rowcount == 1
        except Exception as exc:
            logging.error(
                "Erreur lors de la suppression de la conversation %s : %s",
                conversation_id,
                exc,
            )
            return False

    # ------------------------------------------------------------------
    # Gestion des accès utilisateurs
    # ------------------------------------------------------------------
    @log
    def has_access(self, conversation_id: int, user_id: int) -> bool:
        """Vérifie si un utilisateur possède au moins un accès à la conversation."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT 1 FROM collaborations
                         WHERE id_conversation = %(id_conversation)s
                           AND id_user = %(id_user)s
                         LIMIT 1;
                        """,
                        {"id_conversation": conversation_id, "id_user": user_id},
                    )
                    return cursor.fetchone() is not None
        except Exception as exc:
            logging.error(
                "Erreur lors du contrôle d'accès de l'utilisateur %s à la conversation %s : %s",
                user_id,
                conversation_id,
                exc,
            )
            return False

    @log
    def has_write_access(self, conversation_id: int, user_id: int) -> bool:
        """Vérifie si l'utilisateur dispose d'un rôle autorisant l'écriture."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT role FROM collaborations
                         WHERE id_conversation = %(id_conversation)s
                           AND id_user = %(id_user)s
                         LIMIT 1;
                        """,
                        {"id_conversation": conversation_id, "id_user": user_id},
                    )
                    row = cursor.fetchone()
            if not row:
                return False
            role = str(row.get("role", "")).upper()
            return role in {"ADMIN", "WRITER"}
        except Exception as exc:
            logging.error(
                "Erreur lors du contrôle des droits d'écriture pour l'utilisateur %s (conversation %s) : %s",
                user_id,
                conversation_id,
                exc,
            )
            return False

    @log
    def add_user_access(self, conversation_id: int, user_id: int, can_write: bool) -> bool:
        """Ajoute ou met à jour les droits d'un utilisateur sur une conversation."""
        role = "WRITER" if can_write else "VIEWER"
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id_collaboration FROM collaborations
                         WHERE id_conversation = %(id_conversation)s
                           AND id_user = %(id_user)s;
                        """,
                        {"id_conversation": conversation_id, "id_user": user_id},
                    )
                    existing = cursor.fetchone()
                    if existing:
                        cursor.execute(
                            """
                            UPDATE collaborations
                               SET role = %(role)s
                             WHERE id_collaboration = %(id_collaboration)s;
                            """,
                            {"role": role, "id_collaboration": existing.get("id_collaboration")},
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO collaborations (id_conversation, id_user, role)
                            VALUES (%(id_conversation)s, %(id_user)s, %(role)s);
                            """,
                            {
                                "id_conversation": conversation_id,
                                "id_user": user_id,
                                "role": role,
                            },
                        )
                    return True
        except Exception as exc:
            logging.error(
                "Erreur lors de l'ajout des droits pour l'utilisateur %s sur la conversation %s : %s",
                user_id,
                conversation_id,
                exc,
            )
            return False

    # ------------------------------------------------------------------
    # Listes et recherches
    # ------------------------------------------------------------------
    @log
    def get_conversations_by_user(self, user_id: int) -> List[Conversation]:
        """Retourne les conversations actives d'un utilisateur."""
        conversations: List[Conversation] = []
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT c.* FROM conversations c
                        JOIN collaborations col ON col.id_conversation = c.id_conversation
                        WHERE col.id_user = %(id_user)s
                          AND c.is_active = TRUE
                        ORDER BY c.created_at DESC;
                        """,
                        {"id_user": user_id},
                    )
                    rows = cursor.fetchall() or []
            for row in rows:
                conversations.append(self._build_conversation(row))
        except Exception as exc:
            logging.error(
                "Erreur lors de la récupération des conversations de l'utilisateur %s : %s",
                user_id,
                exc,
            )
        return conversations

    @log
    def get_conversations_by_date(
        self, user_id: int, target_date: datetime
    ) -> List[Conversation]:
        """Retourne les conversations créées à la date donnée."""
        conversations: List[Conversation] = []
        target_day: date = target_date.date() if isinstance(target_date, datetime) else target_date
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT c.* FROM conversations c
                        JOIN collaborations col ON col.id_conversation = c.id_conversation
                        WHERE col.id_user = %(id_user)s
                          AND DATE(c.created_at) = %(target_date)s
                        ORDER BY c.created_at DESC;
                        """,
                        {"id_user": user_id, "target_date": target_day},
                    )
                    rows = cursor.fetchall() or []
            for row in rows:
                conversations.append(self._build_conversation(row))
        except Exception as exc:
            logging.error(
                "Erreur lors de la recherche par date des conversations de l'utilisateur %s : %s",
                user_id,
                exc,
            )
        return conversations

    @log
    def search_conversations_by_title(
        self, user_id: int, title: str
    ) -> List[Conversation]:
        """Recherche les conversations via une partie du titre."""
        conversations: List[Conversation] = []
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT c.* FROM conversations c
                        JOIN collaborations col ON col.id_conversation = c.id_conversation
                        WHERE col.id_user = %(id_user)s
                          AND c.titre ILIKE %(pattern)s
                        ORDER BY c.created_at DESC;
                        """,
                        {"id_user": user_id, "pattern": f"%{title}%"},
                    )
                    rows = cursor.fetchall() or []
            for row in rows:
                conversations.append(self._build_conversation(row))
        except Exception as exc:
            logging.error(
                "Erreur lors de la recherche par titre des conversations de l'utilisateur %s : %s",
                user_id,
                exc,
            )
        return conversations

    @log
    def set_active(self, conversation_id: int, is_active: bool) -> bool:
        """Active ou désactive une conversation."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE conversations
                           SET is_active = %(is_active)s
                         WHERE id_conversation = %(id_conversation)s;
                        """,
                        {"is_active": is_active, "id_conversation": conversation_id},
                    )
                    return cursor.rowcount == 1
        except Exception as exc:
            logging.error(
                "Erreur lors du changement d'état de la conversation %s : %s",
                conversation_id,
                exc,
            )
            return False
