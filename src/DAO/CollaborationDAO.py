import logging
from typing import List, Optional
from Utils.log_decorator import log           # si ton fichier utils est à la racine du projet
from DAO.DBConnector import DBConnection
from ObjetMetier.Collaboration import Collaboration
from Utils.Singleton import Singleton

class CollaborationDAO(metaclass=Singleton):
    """
    DAO (Data Access Object) pour la gestion des collaborations en base de données.
    Fournit les opérations CRUD et les méthodes de recherche associées.
    """

    # -------------------------
    # CRUD de base
    # -------------------------

    @log
    def create(self, collaboration: Collaboration) -> bool:
        """
        Crée une collaboration dans la base de données.

        Parameters
        ----------
        collaboration : Collaboration
            Objet Collaboration à insérer.

        Returns
        -------
        bool
            True si la création a réussi, False sinon.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO collaborations (id_conversation, id_user, role)
                        VALUES (%(id_conversation)s, %(id_user)s, %(role)s)
                        RETURNING id_collaboration;
                        """,
                        {
                            "id_conversation": collaboration.id_conversation,
                            "id_user": collaboration.id_user,
                            "role": collaboration.role,
                        },
                    )
                    res = cursor.fetchone()

            if res and "id_collaboration" in res:
                collaboration.id_collaboration = res["id_collaboration"]
                return True
            return False

        except Exception as e:
            logging.error(f"Erreur lors de la création de la collaboration : {e}")
            return False

    @log
    def read(self, id_collaboration: int) -> Optional[Collaboration]:
        """
        Récupère une collaboration par son identifiant.

        Parameters
        ----------
        id_collaboration : int

        Returns
        -------
        Optional[Collaboration]
            La collaboration trouvée, ou None si absente.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * FROM collaborations
                        WHERE id_collaboration = %(id_collaboration)s;
                        """,
                        {"id_collaboration": id_collaboration},
                    )
                    res = cursor.fetchone()

            if res:
                return Collaboration(
                    id_collaboration=res["id_collaboration"],
                    id_conversation=res["id_conversation"],
                    id_user=res["id_user"],
                    role=res["role"].lower(),  # Normalize role to lowercase
                )
            return None

        except Exception as e:
            logging.error(f"Erreur lors de la lecture de la collaboration {id_collaboration} : {e}")
            return None

    @log
    def update(self, collaboration: Collaboration) -> bool:
        """
        Met à jour une collaboration existante.

        Parameters
        ----------
        collaboration : Collaboration

        Returns
        -------
        bool
            True si la modification a réussi, False sinon.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE collaborations
                           SET id_conversation = %(id_conversation)s,
                               id_user = %(id_user)s,
                               role = %(role)s
                         WHERE id_collaboration = %(id_collaboration)s;
                        """,
                        {
                            "id_conversation": collaboration.id_conversation,
                            "id_user": collaboration.id_user,
                            "role": collaboration.role,
                            "id_collaboration": collaboration.id_collaboration,
                        },
                    )
                    return cursor.rowcount == 1

        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour de la collaboration {collaboration.id_collaboration} : {e}")
            return False

    @log
    def delete(self, id_collaboration: int) -> bool:
        """
        Supprime une collaboration par son identifiant.

        Parameters
        ----------
        id_collaboration : int

        Returns
        -------
        bool
            True si la suppression a réussi.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM collaborations
                         WHERE id_collaboration = %(id_collaboration)s;
                        """,
                        {"id_collaboration": id_collaboration},
                    )
                    return cursor.rowcount == 1

        except Exception as e:
            logging.error(f"Erreur lors de la suppression de la collaboration {id_collaboration} : {e}")
            return False

    # -------------------------
    # Méthodes supplémentaires
    # -------------------------

    @log
    def list_all(self) -> List[Collaboration]:
        """
        Retourne la liste de toutes les collaborations.

        Returns
        -------
        List[Collaboration]
        """
        collaborations = []
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM collaborations ORDER BY id_conversation, id_user;")
                    res = cursor.fetchall()

            for row in res or []:
                collaborations.append(
                    Collaboration(
                        id_collaboration=row["id_collaboration"],
                        id_conversation=row["id_conversation"],
                        id_user=row["id_user"],
                        role=row["role"].lower(),  # Normalize role to lowercase
                    )
                )

        except Exception as e:
            logging.error(f"Erreur lors de la récupération de la liste des collaborations : {e}")

        return collaborations

    @log
    def find_by_conversation(self, id_conversation: int) -> List[Collaboration]:
        """Retourne toutes les collaborations d’une conversation donnée."""
        collaborations = []
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * FROM collaborations
                         WHERE id_conversation = %(id_conversation)s
                         ORDER BY id_user;
                        """,
                        {"id_conversation": id_conversation},
                    )
                    res = cursor.fetchall()

            for row in res or []:
                collaborations.append(
                    Collaboration(
                        id_collaboration=row["id_collaboration"],
                        id_conversation=row["id_conversation"],
                        id_user=row["id_user"],
                        role=row["role"].lower(),  # Normalize role to lowercase
                    )
                )

        except Exception as e:
            logging.error(f"Erreur lors de la recherche des collaborations pour la conversation {id_conversation} : {e}")

        return collaborations

    @log
    def find_by_user(self, id_user: int) -> List[Collaboration]:
        """Retourne toutes les collaborations d’un utilisateur donné."""
        collaborations = []
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * FROM collaborations
                         WHERE id_user = %(id_user)s
                         ORDER BY id_conversation;
                        """,
                        {"id_user": id_user},
                    )
                    res = cursor.fetchall()

            for row in res or []:
                collaborations.append(
                    Collaboration(
                        id_collaboration=row["id_collaboration"],
                        id_conversation=row["id_conversation"],
                        id_user=row["id_user"],
                        role=row["role"].lower(),  # Normalize role to lowercase
                    )
                )

        except Exception as e:
            logging.error(f"Erreur lors de la recherche des collaborations pour l'utilisateur {id_user} : {e}")

        return collaborations

    @log
    def find_by_conversation_and_user(self, id_conversation: int, id_user: int) -> Optional[Collaboration]:
        """Retourne la collaboration d’un utilisateur spécifique dans une conversation."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * FROM collaborations
                         WHERE id_conversation = %(id_conversation)s
                           AND id_user = %(id_user)s;
                        """,
                        {"id_conversation": id_conversation, "id_user": id_user},
                    )
                    res = cursor.fetchone()

            if res:
                return Collaboration(
                    id_collaboration=res["id_collaboration"],
                    id_conversation=res["id_conversation"],
                    id_user=res["id_user"],
                    role=res["role"],
                )
            return None

        except Exception as e:
            logging.error(
                f"Erreur lors de la recherche de la collaboration pour conversation={id_conversation}, user={id_user} : {e}"
            )
            return None

    @log
    def update_role(self, id_collaboration: int, new_role: str) -> bool:
        """Modifie uniquement le rôle d’une collaboration."""
        try:
            new_role = new_role.strip().upper()
            if new_role not in {"ADMIN", "WRITER", "VIEWER", "BANNED"}:
                raise ValueError("Rôle invalide")

            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE collaborations
                           SET role = %(role)s
                         WHERE id_collaboration = %(id_collaboration)s;
                        """,
                        {"role": new_role, "id_collaboration": id_collaboration},
                    )
                    return cursor.rowcount == 1

        except Exception as e:
            logging.error(f"Erreur lors de la modification du rôle de la collaboration {id_collaboration} : {e}")
            return False

    @log
    def delete_by_conversation_and_user(self, id_conversation: int, id_user: int) -> bool:
        """Supprime une collaboration à partir d’une paire (conversation, utilisateur)."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM collaborations
                         WHERE id_conversation = %(id_conversation)s
                           AND id_user = %(id_user)s;
                        """,
                        {"id_conversation": id_conversation, "id_user": id_user},
                    )
                    return cursor.rowcount > 0

        except Exception as e:
            logging.error(
                f"Erreur lors de la suppression de la collaboration conversation={id_conversation}, user={id_user} : {e}"
            )
            return False

    @log
    def count_by_conversation(self, id_conversation: int) -> int:
        """Compte le nombre de collaborateurs dans une conversation."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT COUNT(*) AS total
                          FROM collaborations
                         WHERE id_conversation = %(id_conversation)s;
                        """,
                        {"id_conversation": id_conversation},
                    )
                    res = cursor.fetchone()
                    return res["total"] if res and "total" in res else 0

        except Exception as e:
            logging.error(f"Erreur lors du comptage des collaborateurs de la conversation {id_conversation} : {e}")
            return 0
