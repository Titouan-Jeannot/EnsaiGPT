import logging
from uuid import uuid4
from datetime import datetime, date
from typing import List, Optional, Dict, Any

from DAO.DBConnector import DBConnection
from ObjetMetier.Conversation import Conversation
from Utils.Singleton import Singleton
from Utils.log_decorator import log


class ConversationDAO(metaclass=Singleton):
    """
    DAO (Data Access Object) pour la table `conversation`.
    Gère les opérations CRUD, recherches et contrôles d'accès.
    """

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #
    def _row_to_conversation(self, row: Optional[Dict[str, Any]]) -> Optional[Conversation]:
        """Convertit une ligne SQL (dict-like) en instance Conversation."""
        if not row:
            return None
        return Conversation(
            id_conversation=row["id_conversation"],
            titre=row["titre"],
            created_at=row["created_at"],
            # colonne DB : settings_conversation  ↔︎ attribut objet : setting_conversation
            setting_conversation=row.get("settings_conversation") or "",
            token_viewer=row.get("token_viewer"),
            token_writter=row.get("token_writter"),
            is_active=row.get("is_active", True),
        )

    def _fetch_many(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Conversation]:
        """Exécute une requête SELECT et renvoie une liste d'objets Conversation."""
        conversations: List[Conversation] = []
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params or {})
                rows = cursor.fetchall() or []
        for row in rows:
            conv = self._row_to_conversation(row)
            if conv:
                conversations.append(conv)
        return conversations

    def _execute(self, query: str, params: Dict[str, Any]) -> int:
        """Exécute une requête d'écriture et retourne le rowcount."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)
                connection.commit()  # commit explicite
                return cursor.rowcount
        except Exception as exc:
            logging.error("ConversationDAO query failed: %s", exc)
            raise

    def _exists(self, query: str, params: Dict[str, Any]) -> bool:
        """Retourne True si la requête renvoie au moins une ligne."""
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone() is not None

    # ------------------------------------------------------------------ #
    # CRUD                                                               #
    # ------------------------------------------------------------------ #
    @log
    def create(self, conversation: Conversation, creator_user_id: Optional[int] = None) -> Conversation:
        """
        Insère une conversation et renvoie l’instance complétée.
        - Génère token_viewer/token_writter si absents (uuid4().hex).
        - created_at est renvoyé par PostgreSQL (DEFAULT NOW()).
        """
        # Assurer que les tokens existent (la classe accepte None)
        token_viewer = conversation.token_viewer or uuid4().hex
        token_writter = conversation.token_writter or uuid4().hex

        query = """
            INSERT INTO conversation (titre, settings_conversation, token_viewer, token_writter, is_active)
            VALUES (%(titre)s, %(settings)s, %(token_viewer)s, %(token_writter)s, %(is_active)s)
            RETURNING id_conversation, created_at, token_viewer, token_writter;
        """
        params = {
            "titre": conversation.titre,
            "settings": conversation.setting_conversation,
            "token_viewer": token_viewer,
            "token_writter": token_writter,
            "is_active": conversation.is_active,
        }
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)
                    row = cursor.fetchone()
                connection.commit()  # commit l'INSERT

            if not row:
                raise ValueError("Conversation insertion failed.")

            # Refléter les valeurs finales dans l'objet
            conversation.id_conversation = row["id_conversation"]
            conversation.created_at = row["created_at"]
            conversation.token_viewer = row["token_viewer"]
            conversation.token_writter = row["token_writter"]
            return conversation
        except Exception as exc:
            logging.error("Error while creating conversation: %s", exc)
            raise

    def read(self, conversation_id: int) -> Optional[Conversation]:
        """Alias rétrocompatible vers get_by_id()."""
        return self.get_by_id(conversation_id)

    @log
    def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        query = """
            SELECT *
              FROM conversation
             WHERE id_conversation = %(id_conversation)s;
        """
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, {"id_conversation": conversation_id})
                row = cursor.fetchone()
        return self._row_to_conversation(row)

    # ------------------------------------------------------------------ #
    # Recherches / listes                                                #
    # ------------------------------------------------------------------ #
    @log
    def get_conversations_by_user(self, user_id: int) -> List[Conversation]:
        """Renvoie toutes les conversations actives liées à un utilisateur."""
        query = """
            SELECT c.*
              FROM conversation c
              JOIN collaboration col ON col.id_conversation = c.id_conversation
             WHERE col.id_user = %(user_id)s
               AND c.is_active = TRUE
             ORDER BY c.created_at DESC;
        """
        return self._fetch_many(query, {"user_id": user_id})

    @log
    def get_conversations_by_date(self, user_id: int, target_date: datetime) -> List[Conversation]:
        """Renvoie les conversations d'un utilisateur à une date donnée (DATE(created_at) = target_date)."""
        query = """
            SELECT c.*
              FROM conversation c
              JOIN collaboration col ON col.id_conversation = c.id_conversation
             WHERE col.id_user = %(user_id)s
               AND DATE(c.created_at) = %(target_date)s
             ORDER BY c.created_at DESC;
        """
        day: date = target_date.date()
        return self._fetch_many(query, {"user_id": user_id, "target_date": day})

    @log
    def search_conversations_by_title(self, user_id: int, title: str) -> List[Conversation]:
        """Recherche par titre (ILIKE, insensible à la casse)."""
        query = """
            SELECT c.*
              FROM conversation c
              JOIN collaboration col ON col.id_conversation = c.id_conversation
             WHERE col.id_user = %(user_id)s
               AND c.titre ILIKE %(title)s
             ORDER BY c.created_at DESC;
        """
        return self._fetch_many(query, {"user_id": user_id, "title": f"%{title}%"})

    # ------------------------------------------------------------------ #
    # Mises à jour / suppression                                         #
    # ------------------------------------------------------------------ #
    @log
    def update_title(self, conversation_id: int, new_title: str) -> bool:
        query = """
            UPDATE conversation
               SET titre = %(titre)s
             WHERE id_conversation = %(id_conversation)s;
        """
        return self._execute(query, {"titre": new_title, "id_conversation": conversation_id}) == 1

    @log
    def delete(self, conversation_id: int) -> bool:
        query = "DELETE FROM conversation WHERE id_conversation = %(id_conversation)s;"
        return self._execute(query, {"id_conversation": conversation_id}) == 1

    @log
    def set_active(self, conversation_id: int, is_active: bool) -> bool:
        query = """
            UPDATE conversation
               SET is_active = %(is_active)s
             WHERE id_conversation = %(id_conversation)s;
        """
        return self._execute(query, {"is_active": is_active, "id_conversation": conversation_id}) == 1

    # ------------------------------------------------------------------ #
    # Contrôles d’accès                                                  #
    # ------------------------------------------------------------------ #
    @log
    def has_access(self, conversation_id: int, user_id: int) -> bool:
        query = """
            SELECT 1
              FROM collaboration
             WHERE id_conversation = %(id_conversation)s
               AND id_user = %(user_id)s
             LIMIT 1;
        """
        return self._exists(query, {"id_conversation": conversation_id, "user_id": user_id})

    @log
    def has_write_access(self, conversation_id: int, user_id: int) -> bool:
        query = """
            SELECT 1
              FROM collaboration
             WHERE id_conversation = %(id_conversation)s
               AND id_user = %(user_id)s
               AND role IN ('admin', 'writer')
             LIMIT 1;
        """
        return self._exists(query, {"id_conversation": conversation_id, "user_id": user_id})

    @log
    def add_user_access(self, conversation_id: int, user_id: int, can_write: bool) -> None:
        """Ajoute ou met à jour le rôle d’un utilisateur sur une conversation."""
        role = "writer" if can_write else "viewer"
        query = """
            INSERT INTO collaboration (id_conversation, id_user, role)
            VALUES (%(id_conversation)s, %(id_user)s, %(role)s)
            ON CONFLICT (id_conversation, id_user)
            DO UPDATE SET role = EXCLUDED.role;
        """
        self._execute(query, {"id_conversation": conversation_id, "id_user": user_id, "role": role})
