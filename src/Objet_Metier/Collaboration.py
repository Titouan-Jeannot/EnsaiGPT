class Collaboration:
    """
    Classe représentant une collaboration entre un utilisateur et une conversation.
    Attributs:
    - id_collaboration : identifiant unique de la collaboration
    - id_conversation : identifiant de la conversation
    - id_user : identifiant de l'utilisateur
    - role : rôle de l'utilisateur dans la conversation (ex: admin, membre)
    Méthodes:
    - __init__(self, id_collaboration, id_conversation, id_user, role) : constructeur de la classe


    """

    def __init__(self, id_collaboration, id_conversation, id_user, role):
        """
        Constructeur de la classe Collaboration.

        Paramètres:
        -----------
        - id_collaboration : identifiant unique de la collaboration
        - id_conversation : identifiant de la conversation
        - id_user : identifiant de l'utilisateur
        - role : rôle de l'utilisateur dans la conversation (ex: admin, membre)

        Raises:
        -------
        - ValueError : si un des paramètres est None

        """
        if id_collaboration is None or not isinstance(id_collaboration, int):
            raise ValueError("id_collaboration doit etre un integer non null")
        if id_conversation is None or not isinstance(id_conversation, int):
            raise ValueError("id_conversation doit etre un integer non null")
        if id_user is None or not isinstance(id_user, int):
            raise ValueError("id_user doit etre un integer non null")
        if role is None or not isinstance(role, str):
            raise ValueError("role doit etre une chaine non nulle")
        if role not in ["admin", "viewer", "writer", "banned"]:
            raise ValueError("role doit etre 'admin', 'viewer', 'writer' ou 'banned'")

        self.id_collaboration = id_collaboration
        self.id_conversation = id_conversation
        self.id_user = id_user
        self.role = role

    def __eq__(self, other):
        if not isinstance(other, Collaboration):
            return False
        return (
            self.id_collaboration == other.id_collaboration
            and self.id_conversation == other.id_conversation
            and self.id_user == other.id_user
            and self.role == other.role
        )

    def __str__(self):
        return f"Collaboration(id_collaboration={self.id_collaboration}, id_conversation={self.id_conversation}, id_user={self.id_user}, role='{self.role}')"
