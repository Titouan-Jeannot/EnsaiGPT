from utils.singleton import Singleton
from utils.log_decorator import log
from dao.db_connection import DBConnection
from business_object.collaboration import Collaboration


class CollaborationDao(metaclass=Singleton):
    """Classe contenant les méthodes pour accéder aux Collaborations de la base de données"""

    @log
    def creer(self, collaboration: Collaboration) -> bool:
        """Création d'une collaboration dans la base de données

        Parameters
        ----------
        collaboration : Collaboration

        Returns
        -------
        created : bool
            True si la création est un succès
            False sinon
        """

        res = None

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO collaborations(id_conversation, id_user, role) VALUES "
                        "(%(id_conversation)s, %(id_user)s, %(role)s)                      "
                        "RETURNING id_collaboration;                                        ",
                        {
                            "id_conversation": collaboration.id_conversation,
                            "id_user": collaboration.id_user,
                            "role": collaboration.role
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logging.info(e)

        created = False
        if res:
            collaboration.id_collaboration = res["id_collaboration"]
            created = True

        return created

    @log
    def trouver_par_id(self, id_collaboration: int) -> Collaboration:
        """Trouver une collaboration grâce à son id

        Parameters
        ----------
        id_collaboration : int
            numéro id de la collaboration que l'on souhaite trouver

        Returns
        -------
        collaboration : Collaboration
            renvoie la collaboration que l'on cherche par id
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT *                                "
                        "  FROM collaborations                   "
                        " WHERE id_collaboration = %(id_collaboration)s;",
                        {"id_collaboration": id_collaboration},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logging.info(e)
            raise

        collaboration = None
        if res:
            collaboration = Collaboration(
                id_collaboration=res["id_collaboration"],
                id_conversation=res["id_conversation"],
                id_user=res["id_user"],
                role=res["role"]
            )

        return collaboration

    @log
    def lister_toutes(self) -> list[Collaboration]:
        """Lister toutes les collaborations

        Parameters
        ----------
        None

        Returns
        -------
        liste_collaborations : list[Collaboration]
            renvoie la liste de toutes les collaborations dans la base de données
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT *                     "
                        "  FROM collaborations;       "
                    )
                    res = cursor.fetchall()
        except Exception as e:
            logging.info(e)
            raise

        liste_collaborations = []

        if res:
            for row in res:
                collaboration = Collaboration(
                    id_collaboration=row["id_collaboration"],
                    id_conversation=row["id_conversation"],
                    id_user=row["id_user"],
                    role=row["role"]
                )
                liste_collaborations.append(collaboration)

        return liste_collaborations

    @log
    def modifier(self, collaboration: Collaboration) -> bool:
        """Modification d'une collaboration dans la base de données

        Parameters
        ----------
        collaboration : Collaboration

        Returns
        -------
        modified : bool
            True si la modification est un succès
            False sinon
        """

        res = None

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE collaborations                    "
                        "   SET id_conversation = %(id_conversation)s, "
                        "       id_user = %(id_user)s,           "
                        "       role = %(role)s                  "
                        " WHERE id_collaboration = %(id_collaboration)s;",
                        {
                            "id_conversation": collaboration.id_conversation,
                            "id_user": collaboration.id_user,
                            "role": collaboration.role,
                            "id_collaboration": collaboration.id_collaboration
                        },
                    )
                    res = cursor.rowcount
        except Exception as e:
            logging.info(e)

        return res == 1

    @log
    def supprimer(self, collaboration: Collaboration) -> bool:
        """Suppression d'une collaboration dans la base de données

        Parameters
        ----------
        collaboration : Collaboration
            collaboration à supprimer de la base de données

        Returns
        -------
        bool
            True si la collaboration a bien été supprimée
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM collaborations              "
                        " WHERE id_collaboration = %(id_collaboration)s",
                        {"id_collaboration": collaboration.id_collaboration},
                    )
                    res = cursor.rowcount
        except Exception as e:
            logging.info(e)
            raise

        return res > 0

    @log
    def trouver_par_conversation(self, id_conversation: int) -> list[Collaboration]:
        """Trouver toutes les collaborations d'une conversation

        Parameters
        ----------
        id_conversation : int
            id de la conversation

        Returns
        -------
        list[Collaboration]
            liste des collaborations de la conversation
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT *                                "
                        "  FROM collaborations                   "
                        " WHERE id_conversation = %(id_conversation)s "
                        " ORDER BY role, id_user;                ",
                        {"id_conversation": id_conversation},
                    )
                    res = cursor.fetchall()
        except Exception as e:
            logging.info(e)
            raise

        liste_collaborations = []

        if res:
            for row in res:
                collaboration = Collaboration(
                    id_collaboration=row["id_collaboration"],
                    id_conversation=row["id_conversation"],
                    id_user=row["id_user"],
                    role=row["role"]
                )
                liste_collaborations.append(collaboration)

        return liste_collaborations

    @log
    def trouver_par_utilisateur(self, id_user: int) -> list[Collaboration]:
        """Trouver toutes les collaborations d'un utilisateur

        Parameters
        ----------
        id_user : int
            id de l'utilisateur

        Returns
        -------
        list[Collaboration]
            liste des collaborations de l'utilisateur
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT *                          "
                        "  FROM collaborations             "
                        " WHERE id_user = %(id_user)s      "
                        " ORDER BY id_conversation;        ",
                        {"id_user": id_user},
                    )
                    res = cursor.fetchall()
        except Exception as e:
            logging.info(e)
            raise

        liste_collaborations = []

        if res:
            for row in res:
                collaboration = Collaboration(
                    id_collaboration=row["id_collaboration"],
                    id_conversation=row["id_conversation"],
                    id_user=row["id_user"],
                    role=row["role"]
                )
                liste_collaborations.append(collaboration)

        return liste_collaborations

    @log
    def trouver_par_conversation_et_utilisateur(self, id_conversation: int, id_user: int) -> Collaboration:
        """Trouver une collaboration spécifique par conversation et utilisateur

        Parameters
        ----------
        id_conversation : int
            id de la conversation
        id_user : int
            id de l'utilisateur

        Returns
        -------
        Collaboration
            la collaboration trouvée ou None
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT *                                "
                        "  FROM collaborations                   "
                        " WHERE id_conversation = %(id_conversation)s "
                        "   AND id_user = %(id_user)s;           ",
                        {
                            "id_conversation": id_conversation,
                            "id_user": id_user
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logging.info(e)
            raise

        collaboration = None
        if res:
            collaboration = Collaboration(
                id_collaboration=res["id_collaboration"],
                id_conversation=res["id_conversation"],
                id_user=res["id_user"],
                role=res["role"]
            )

        return collaboration

    @log
    def modifier_role(self, id_collaboration: int, nouveau_role: str) -> bool:
        """Modifier uniquement le rôle d'une collaboration

        Parameters
        ----------
        id_collaboration : int
            id de la collaboration
        nouveau_role : str
            nouveau rôle ('admin', 'viewer', 'writer', 'banned')

        Returns
        -------
        bool
            True si la modification est un succès
        """

        res = None

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE collaborations         "
                        "   SET role = %(role)s        "
                        " WHERE id_collaboration = %(id_collaboration)s;",
                        {
                            "role": nouveau_role,
                            "id_collaboration": id_collaboration
                        },
                    )
                    res = cursor.rowcount
        except Exception as e:
            logging.info(e)

        return res == 1

    @log
    def supprimer_par_conversation_et_utilisateur(self, id_conversation: int, id_user: int) -> bool:
        """Supprimer une collaboration par conversation et utilisateur

        ajustement : utile pour qu'un utilisateur quitte une conversation

        Parameters
        ----------
        id_conversation : int
            id de la conversation
        id_user : int
            id de l'utilisateur

        Returns
        -------
        bool
            True si la suppression est un succès
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM collaborations              "
                        " WHERE id_conversation = %(id_conversation)s "
                        "   AND id_user = %(id_user)s;           ",
                        {
                            "id_conversation": id_conversation,
                            "id_user": id_user
                        },
                    )
                    res = cursor.rowcount
        except Exception as e:
            logging.info(e)
            raise

        return res > 0

    @log
    def compter_par_conversation(self, id_conversation: int) -> int:
        """Compter le nombre de collaborateurs dans une conversation

        ajustement : utile pour des statistiques

        Parameters
        ----------
        id_conversation : int
            id de la conversation

        Returns
        -------
        int
            nombre de collaborateurs
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*)              "
                        "  FROM collaborations        "
                        " WHERE id_conversation = %(id_conversation)s;",
                        {"id_conversation": id_conversation},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logging.info(e)
            raise

        return res[0] if res else 0
