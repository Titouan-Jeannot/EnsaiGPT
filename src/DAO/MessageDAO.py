import logging
from datetime import datetime, time
from typing import List, Optional

from src.DAO.DBConnector import DBConnection
# Assurez-vous que l'importation de Message est correcte dans votre environnement
try:
    from src.ObjetMetier.Message import Message
except Exception:
    from ObjetMetier.Message import Message


class MessageDAO:
    """DAO pour Message : CRUD + méthodes spécifiques aux conversations.
    Utilise la connexion partagée (DBConnection) et retourne des objets Message.
    """

    # --- CREATE -------------------------------------------------------------

    def create(self, message: Message) -> Message:
        """Crée un message en base et retourne l'objet avec son id."""
        query = """
        INSERT INTO message (id_conversation, id_user, "timestamp", message, is_from_agent)
        VALUES (%(id_conversation)s, %(id_user)s, %(timestamp)s, %(message)s, %(is_from_agent)s)
        RETURNING id_message;
        """
        try:
            with DBConnection().connection as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        query,
                        {
                            "id_conversation": message.id_conversation,
                            "id_user": message.id_user,
                            "timestamp": message.datetime,  # ton objet Python a .datetime
                            "message": message.message,
                            "is_from_agent": message.is_from_agent,
                        },
                    )
                    row = cursor.fetchone()
                    message.id_message = row["id_message"] if row else None
            return message
        except Exception as e:
            logging.error(f"Erreur création message: {e}")
            raise ValueError(f"Erreur création message: {e}") from e

    # --- READ ---------------------------------------------------------------

    def get_by_id(self, message_id: int) -> Optional[Message]:
        """Lit un message par son id."""
        query = "SELECT * FROM message WHERE id_message = %(id_message)s;"
        with DBConnection().connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, {"id_message": message_id})
                row = cursor.fetchone()
                if not row:
                    return None
                return Message(
                    id_message=row["id_message"],
                    id_conversation=row["id_conversation"],
                    id_user=row["id_user"],
                    datetime=row["timestamp"],  # colonne SQL "timestamp"
                    message=row["message"],
                    is_from_agent=row["is_from_agent"],
                )

    # --- LISTING ------------------------------------------------------------

    def get_messages_by_conversation(self, conversation_id: int) -> List[Message]:
        """Retourne tous les messages d'une conversation, ordonnés par date."""
        query = """
        SELECT * FROM message
        WHERE id_conversation = %(id_conversation)s
        ORDER BY "timestamp";
        """
        messages: List[Message] = []
        with DBConnection().connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, {"id_conversation": conversation_id})
                for row in cursor.fetchall() or []:
                    messages.append(
                        Message(
                            id_message=row["id_message"],
                            id_conversation=row["id_conversation"],
                            id_user=row["id_user"],
                            datetime=row["timestamp"],
                            message=row["message"],
                            is_from_agent=row["is_from_agent"],
                        )
                    )
        return messages

    def get_messages_by_conversation_paginated(
        self, conversation_id: int, page: int, per_page: int
    ) -> List[Message]:
        """Retourne une page de messages d'une conversation (ordre récent d'abord)."""
        offset = max(0, (page - 1) * per_page)
        query = """
        SELECT * FROM message
        WHERE id_conversation = %(id_conversation)s
        ORDER BY "timestamp" DESC
        LIMIT %(limit)s OFFSET %(offset)s;
        """
        messages: List[Message] = []
        with DBConnection().connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    {"id_conversation": conversation_id, "limit": per_page, "offset": offset},
                )
                for row in cursor.fetchall() or []:
                    messages.append(
                        Message(
                            id_message=row["id_message"],
                            id_conversation=row["id_conversation"],
                            id_user=row["id_user"],
                            datetime=row["timestamp"],
                            message=row["message"],
                            is_from_agent=row["is_from_agent"],
                        )
                    )
        return messages

    def count_messages_by_conversation(self, conversation_id: int) -> int:
        """Compte le nombre de messages dans une conversation."""
        query = "SELECT COUNT(*) AS n FROM message WHERE id_conversation = %(id_conversation)s;"
        with DBConnection().connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, {"id_conversation": conversation_id})
                row = cursor.fetchone()
                return int(row["n"]) if row and "n" in row else 0

    def search_messages(self, conversation_id: int, keyword: str) -> List[Message]:
        """Recherche des messages contenant un mot-clé (ILIKE = insensible à la casse)."""
        query = """
        SELECT * FROM message
        WHERE id_conversation = %(id_conversation)s
          AND message ILIKE %(kw)s
        ORDER BY "timestamp" DESC;
        """
        messages: List[Message] = []
        with DBConnection().connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, {"id_conversation": conversation_id, "kw": f"%{keyword}%"})
                for row in cursor.fetchall() or []:
                    messages.append(
                        Message(
                            id_message=row["id_message"],
                            id_conversation=row["id_conversation"],
                            id_user=row["id_user"],
                            datetime=row["timestamp"],
                            message=row["message"],
                            is_from_agent=row["is_from_agent"],
                        )
                    )
        return messages

    # =========================================================================
    # NOUVELLE MÉTHODE POUR SearchService : Recherche par mot-clé (multi-conv)
    # =========================================================================
    def search_by_keyword(self, keyword: str, conversation_ids: List[int]) -> List[Message]:
        """
        Recherche des messages contenant un mot-clé, limités aux conversations spécifiées.

        Parameters
        ----------
        keyword : str
            Le mot-clé à rechercher (recherche insensible à la casse).
        conversation_ids : List[int]
            Liste des IDs de conversation autorisées pour la recherche.

        Returns
        -------
        List[Message]
        """
        if not conversation_ids:
            return []

        query = """
        SELECT * FROM message
        WHERE id_conversation IN %(ids)s
          AND message ILIKE %(kw)s
        ORDER BY "timestamp" DESC;
        """
        messages: List[Message] = []
        try:
            with DBConnection().connection as conn:
                with conn.cursor() as cursor:
                    # psycopg2 gère la conversion de tuple en liste pour la clause IN
                    cursor.execute(query, {
                        "ids": tuple(conversation_ids),
                        "kw": f"%{keyword}%"
                    })
                    for row in cursor.fetchall() or []:
                        messages.append(
                            Message(
                                id_message=row["id_message"],
                                id_conversation=row["id_conversation"],
                                id_user=row["id_user"],
                                datetime=row["timestamp"],
                                message=row["message"],
                                is_from_agent=row["is_from_agent"],
                            )
                        )
            return messages
        except Exception as e:
            logging.error(f"Erreur recherche messages par mot-clé (multi-conv): {e}")
            return []

    # =======================================================================
    # NOUVELLE MÉTHODE POUR SearchService : Recherche par date (multi-conv)
    # =======================================================================
    def search_by_date(self, target_date: datetime, conversation_ids: List[int]) -> List[Message]:
        """
        Recherche des messages créés à une date donnée (journée entière),
        limités aux conversations spécifiées.
        """
        if not conversation_ids:
            return []

        # Définir le début et la fin de la journée pour la recherche
        start_of_day = datetime.combine(target_date.date(), time.min)
        end_of_day = datetime.combine(target_date.date(), time.max)

        query = """
        SELECT * FROM message
        WHERE id_conversation IN %(ids)s
          AND "timestamp" BETWEEN %(start)s AND %(end)s
        ORDER BY "timestamp" DESC;
        """
        messages: List[Message] = []
        try:
            with DBConnection().connection as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, {
                        "ids": tuple(conversation_ids),
                        "start": start_of_day,
                        "end": end_of_day
                    })
                    for row in cursor.fetchall() or []:
                        messages.append(
                            Message(
                                id_message=row["id_message"],
                                id_conversation=row["id_conversation"],
                                id_user=row["id_user"],
                                datetime=row["timestamp"],
                                message=row["message"],
                                is_from_agent=row["is_from_agent"],
                            )
                        )
            return messages
        except Exception as e:
            logging.error(f"Erreur recherche messages par date (multi-conv): {e}")
            return []


    def get_messages_by_date_range(
        self, conversation_id: int, start_date: datetime, end_date: datetime
    ) -> List[Message]:
        """Récupère les messages dans une période donnée (inclusif)."""
        query = """
        SELECT * FROM message
        WHERE id_conversation = %(id_conversation)s
          AND "timestamp" BETWEEN %(start)s AND %(end)s
        ORDER BY "timestamp";
        """
        messages: List[Message] = []
        with DBConnection().connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    {"id_conversation": conversation_id, "start": start_date, "end": end_date},
                )
                for row in cursor.fetchall() or []:
                    messages.append(
                        Message(
                            id_message=row["id_message"],
                            id_conversation=row["id_conversation"],
                            id_user=row["id_user"],
                            datetime=row["timestamp"],
                            message=row["message"],
                            is_from_agent=row["is_from_agent"],
                        )
                    )
        return messages

    # --- UPDATE / DELETE ----------------------------------------------------

    def update(self, message: Message) -> bool:
        """Met à jour le contenu d’un message."""
        query = """
        UPDATE message
           SET message = %(message)s
         WHERE id_message = %(id_message)s;
        """
        with DBConnection().connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query, {"message": message.message, "id_message": message.id_message}
                )
                return cursor.rowcount == 1

    def delete_by_id(self, message_id: int) -> bool:
        """Supprime un message par son id."""
        query = "DELETE FROM message WHERE id_message = %(id_message)s;"
        with DBConnection().connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, {"id_message": message_id})
                return cursor.rowcount > 0

    def get_last_message(self, conversation_id: int) -> Optional[Message]:
        """Récupère le dernier message d'une conversation."""
        query = """
        SELECT * FROM message
        WHERE id_conversation = %(id_conversation)s
        ORDER BY "timestamp" DESC
        LIMIT 1;
        """
        with DBConnection().connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, {"id_conversation": conversation_id})
                row = cursor.fetchone()
                if not row:
                    return None
                return Message(
                    id_message=row["id_message"],
                    id_conversation=row["id_conversation"],
                    id_user=row["id_user"],
                    datetime=row["timestamp"],
                    message=row["message"],
                    is_from_agent=row["is_from_agent"],
                )
