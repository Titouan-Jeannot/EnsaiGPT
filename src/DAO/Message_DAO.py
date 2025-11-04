import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError, DatabaseError
from typing import List, Optional
from datetime import datetime

try:
    from ObjetMetier.Message import Message
except Exception:
    from src.ObjetMetier.Message import Message

# ajustement : il faut utiliser un singleton de connexion partagé et harmonisé entre les DAO.


class MessageDAO:
    """DAO pour Message : CRUD + méthodes spécifiques aux conversations."""

    def __init__(self, conn):
        """Initialise avec une connexion psycopg2 ou une DSN."""
        if isinstance(conn, str):
            self.conn = psycopg2.connect(conn)
        else:
            self.conn = conn

    def create(self, message: Message) -> Message:
        """Crée un message en base et retourne l'objet avec son id."""
        query = """
        INSERT INTO messages (id_conversation, id_user, datetime, message, is_from_agent)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id_message;
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        message.id_conversation,
                        message.id_user,
                        message.datetime,
                        message.message,
                        message.is_from_agent,
                    ),
                )
                message.id_message = cursor.fetchone()[0]
                self.conn.commit()
                return message
        except (IntegrityError, DatabaseError) as e:
            self.conn.rollback()
            raise ValueError(f"Erreur création message: {str(e)}") from e

    def get_by_id(self, message_id: int) -> Optional[Message]:
        """Lit un message par son id."""
        query = "SELECT * FROM messages WHERE id_message = %s;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (message_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Message(
                id_message=row["id_message"],
                id_conversation=row["id_conversation"],
                id_user=row["id_user"],
                datetime=row["datetime"],
                message=row["message"],
                is_from_agent=row["is_from_agent"],
            )

    def get_messages_by_conversation(self, conversation_id: int) -> List[Message]:
        """Retourne tous les messages d'une conversation, ordonnés par date."""
        query = """
        SELECT * FROM messages
        WHERE id_conversation = %s
        ORDER BY datetime;
        """
        messages = []
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (conversation_id,))
            for row in cursor:
                messages.append(
                    Message(
                        id_message=row["id_message"],
                        id_conversation=row["id_conversation"],
                        id_user=row["id_user"],
                        datetime=row["datetime"],
                        message=row["message"],
                        is_from_agent=row["is_from_agent"],
                    )
                )
        return messages

    def update(self, message: Message) -> bool:
        """Met à jour un message existant."""
        query = """
        UPDATE messages
        SET message = %s
        WHERE id_message = %s;
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (message.message, message.id_message))
                self.conn.commit()
                return cursor.rowcount > 0
        except DatabaseError:
            self.conn.rollback()
            raise

    def get_messages_by_conversation_paginated(
        self, conversation_id: int, page: int, per_page: int
    ) -> List[Message]:
        """Retourne une page de messages d'une conversation."""
        offset = (page - 1) * per_page
        query = """
        SELECT * FROM messages
        WHERE id_conversation = %s
        ORDER BY datetime DESC
        LIMIT %s OFFSET %s;
        """
        messages = []
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (conversation_id, per_page, offset))
            for row in cursor:
                messages.append(
                    Message(
                        id_message=row["id_message"],
                        id_conversation=row["id_conversation"],
                        id_user=row["id_user"],
                        datetime=row["datetime"],
                        message=row["message"],
                        is_from_agent=row["is_from_agent"],
                    )
                )
        return messages

    def count_messages_by_conversation(self, conversation_id: int) -> int:
        """Compte le nombre de messages dans une conversation."""
        query = "SELECT COUNT(*) FROM messages WHERE id_conversation = %s;"
        with self.conn.cursor() as cursor:
            cursor.execute(query, (conversation_id,))
            return cursor.fetchone()[0]

    def search_messages(self, conversation_id: int, keyword: str) -> List[Message]:
        """Recherche des messages contenant un mot-clé."""
        query = """
        SELECT * FROM messages
        WHERE id_conversation = %s
        AND message ILIKE %s
        ORDER BY datetime DESC;
        """
        messages = []
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (conversation_id, f"%{keyword}%"))
            for row in cursor:
                messages.append(Message.from_dict(row))
        return messages

    def get_messages_by_date_range(
        self, conversation_id: int, start_date: datetime, end_date: datetime
    ) -> List[Message]:
        """Récupère les messages dans une période donnée."""
        query = """
        SELECT * FROM messages
        WHERE id_conversation = %s
        AND datetime BETWEEN %s AND %s
        ORDER BY datetime;
        """
        messages = []
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (conversation_id, start_date, end_date))
            for row in cursor:
                messages.append(Message.from_dict(row))
        return messages

    def delete_by_id(self, message_id: int) -> bool:
        """Supprime un message par son id."""
        query = "DELETE FROM messages WHERE id_message = %s;"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (message_id,))
                self.conn.commit()
                return cursor.rowcount > 0
        except DatabaseError:
            self.conn.rollback()
            raise

    def get_last_message(self, conversation_id: int) -> Optional[Message]:
        """Récupère le dernier message d'une conversation."""
        query = """
        SELECT * FROM messages
        WHERE id_conversation = %s
        ORDER BY datetime DESC
        LIMIT 1;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (conversation_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Message.from_dict(row)

    def __del__(self):
        """Ferme la connexion à la base de données."""
        if hasattr(self, "conn") and self.conn is not None:
            self.conn.close()


# Index suggérés pour la base de données :
# CREATE INDEX messages_conversation_idx ON messages(id_conversation);
# CREATE INDEX messages_datetime_idx ON messages(datetime);
