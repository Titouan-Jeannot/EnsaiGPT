import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any

from src.DAO.DBConnector import DBConnection
from src.ObjetMetier.Conversation import Conversation
from src.Utils.Singleton import Singleton
from src.Utils.log_decorator import log


class ConversationDAO(metaclass=Singleton):
    """
    Data access layer for the `conversation` table.
    Mirrors the style used in CollaborationDAO to keep the stack consistent.
    """

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #
    def _row_to_conversation(self, row: Optional[Dict[str, Any]]) -> Optional[Conversation]:
        """Convert a SQL row (RealDictCursor) into a Conversation instance."""
        if not row:
            return None
        return Conversation(
            id_conversation=row["id_conversation"],
            titre=row["titre"],
            created_at=row["created_at"],
            setting_conversation=row.get("settings_conversation") or "",
            token_viewer=row.get("token_viewer") or "",
            token_writter=row.get("token_writter") or "",
            is_active=row.get("is_active", True),
        )

    def _fetch_many(self, query: str, params: Dict[str, Any]) -> List[Conversation]:
        conversations: List[Conversation] = []
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall() or []
        for row in rows:
            conv = self._row_to_conversation(row)
            if conv:
                conversations.append(conv)
        return conversations

    def _execute(self, query: str, params: Dict[str, Any]) -> None:
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)
        except Exception as exc:
            logging.error("ConversationDAO query failed: %s", exc)
            raise

    def _exists(self, query: str, params: Dict[str, Any]) -> bool:
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
        Insert a conversation in database and return the same instance populated with its id.
        The `creator_user_id` argument is accepted for API compatibility but not used here.
        """
        query = """
            INSERT INTO conversation (titre, created_at, settings_conversation,
                                      token_viewer, token_writter, is_active)
            VALUES (%(titre)s, %(created_at)s, %(settings)s,
                    %(token_viewer)s, %(token_writter)s, %(is_active)s)
            RETURNING id_conversation;
        """
        params = {
            "titre": conversation.titre,
            "created_at": conversation.created_at or datetime.now(),
            "settings": conversation.setting_conversation,
            "token_viewer": conversation.token_viewer,
            "token_writter": conversation.token_writter,
            "is_active": conversation.is_active,
        }
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)
                    row = cursor.fetchone()
            if not row or "id_conversation" not in row:
                raise ValueError("Conversation insertion failed: missing id in RETURNING clause.")
            conversation.id_conversation = row["id_conversation"]
            return conversation
        except Exception as exc:
            logging.error("Error while creating conversation: %s", exc)
            raise

    def read(self, conversation_id: int) -> Optional[Conversation]:
        """Backward compatible alias used by CollaborationService."""
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
    # Lists                                                              #
    # ------------------------------------------------------------------ #
    @log
    def get_conversations_by_user(self, user_id: int) -> List[Conversation]:
        """Return every active conversation joined with the collaborations of the user."""
        query = """
            SELECT c.*
              FROM conversation c
              JOIN collaborations col ON col.id_conversation = c.id_conversation
             WHERE col.id_user = %(user_id)s
               AND c.is_active = TRUE
             ORDER BY c.created_at DESC;
        """
        return self._fetch_many(query, {"user_id": user_id})

    @log
    def get_conversations_by_date(self, user_id: int, target_date: datetime) -> List[Conversation]:
        query = """
            SELECT c.*
              FROM conversation c
              JOIN collaborations col ON col.id_conversation = c.id_conversation
             WHERE col.id_user = %(user_id)s
               AND DATE(c.created_at) = %(target_date)s
             ORDER BY c.created_at DESC;
        """
        day: date = target_date.date()
        return self._fetch_many(query, {"user_id": user_id, "target_date": day})

    @log
    def search_conversations_by_title(self, user_id: int, title: str) -> List[Conversation]:
        query = """
            SELECT c.*
              FROM conversation c
              JOIN collaborations col ON col.id_conversation = c.id_conversation
             WHERE col.id_user = %(user_id)s
               AND c.titre ILIKE %(title)s
             ORDER BY c.created_at DESC;
        """
        return self._fetch_many(query, {"user_id": user_id, "title": f"%{title}%"})

    # ------------------------------------------------------------------ #
    # Updates / deletion                                                  #
    # ------------------------------------------------------------------ #
    @log
    def update_title(self, conversation_id: int, new_title: str) -> None:
        query = """
            UPDATE conversation
               SET titre = %(titre)s
             WHERE id_conversation = %(id_conversation)s;
        """
        self._execute(query, {"titre": new_title, "id_conversation": conversation_id})

    @log
    def delete(self, conversation_id: int) -> None:
        query = "DELETE FROM conversation WHERE id_conversation = %(id_conversation)s;"
        self._execute(query, {"id_conversation": conversation_id})

    @log
    def set_active(self, conversation_id: int, is_active: bool) -> None:
        query = """
            UPDATE conversation
               SET is_active = %(is_active)s
             WHERE id_conversation = %(id_conversation)s;
        """
        self._execute(query, {"is_active": is_active, "id_conversation": conversation_id})

    # ------------------------------------------------------------------ #
    # Access checks                                                       #
    # ------------------------------------------------------------------ #
    @log
    def has_access(self, conversation_id: int, user_id: int) -> bool:
        query = """
            SELECT 1
              FROM collaborations
             WHERE id_conversation = %(id_conversation)s
               AND id_user = %(user_id)s
             LIMIT 1;
        """
        return self._exists(query, {"id_conversation": conversation_id, "user_id": user_id})

    @log
    def has_write_access(self, conversation_id: int, user_id: int) -> bool:
        query = """
            SELECT 1
              FROM collaborations
             WHERE id_conversation = %(id_conversation)s
               AND id_user = %(user_id)s
               AND role IN ('admin', 'writer')
             LIMIT 1;
        """
        return self._exists(query, {"id_conversation": conversation_id, "user_id": user_id})

    @log
    def add_user_access(self, conversation_id: int, user_id: int, can_write: bool) -> None:
        role = "writer" if can_write else "viewer"
        query = """
            INSERT INTO collaborations (id_conversation, id_user, role)
            VALUES (%(id_conversation)s, %(id_user)s, %(role)s)
            ON CONFLICT (id_conversation, id_user)
            DO UPDATE SET role = EXCLUDED.role;
        """
        self._execute(
            query,
            {"id_conversation": conversation_id, "id_user": user_id, "role": role},
        )
