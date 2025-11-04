class Collaboration:
    """
    Classe représentant une collaboration entre un utilisateur et une conversation.

    Attributs:
    ----------
    - id_collaboration : int
        identifiant unique de la collaboration
    - id_conversation : int
        identifiant de la conversation
    - id_user : int
        identifiant de l'utilisateur
    - role : str
        rôle de l'utilisateur dans la conversation (admin, viewer, writer, banned)
    """

    def __init__(self, id_collaboration=None, id_conversation=None, id_user=None, role=None):
        """
        Constructeur de la classe Collaboration.

        Paramètres:
        -----------
        id_collaboration : int, optional
            identifiant unique de la collaboration
        id_conversation : int
            identifiant de la conversation
        id_user : int
            identifiant de l'utilisateur
        role : str
            rôle de l'utilisateur dans la conversation (admin, viewer, writer, banned)

        Raises:
        -------
        ValueError
            si un des paramètres requis est invalide
        """
        # Vérifications pour id_conversation, id_user et role (obligatoires)
        if id_conversation is None or not isinstance(id_conversation, int):
            raise ValueError("id_conversation doit être un integer non null")
        if id_user is None or not isinstance(id_user, int):
            raise ValueError("id_user doit être un integer non null")
        if role is None or not isinstance(role, str):
            raise ValueError("role doit être une chaîne non nulle")
        role = role.lower()  # Normalize role to lowercase
        if role not in ["admin", "viewer", "writer", "banned"]:
            raise ValueError("role doit être 'admin', 'viewer', 'writer' ou 'banned'")
            raise ValueError("role doit être 'admin', 'viewer', 'writer' ou 'banned'")

        # id_collaboration peut être None (auto-généré par la BDD lors de l'insertion)
        if id_collaboration is not None and not isinstance(id_collaboration, int):
            raise ValueError("id_collaboration doit être un integer ou None")

        self.id_collaboration = id_collaboration
        self.id_conversation = id_conversation
        self.id_user = id_user
        self.role = role

    def __eq__(self, other):
        """Compare deux collaborations"""
        if not isinstance(other, Collaboration):
            return False
        return (
            self.id_collaboration == other.id_collaboration and
            self.id_conversation == other.id_conversation and
            self.id_user == other.id_user and
            self.role == other.role
        )

    def __str__(self):
        """Représentation en chaîne de caractères"""
        return (f"Collaboration(id_collaboration={self.id_collaboration}, "
                f"id_conversation={self.id_conversation}, "
                f"id_user={self.id_user}, role='{self.role}')")

    def __repr__(self):
        """Représentation pour le débogage"""
        return self.__str__()
