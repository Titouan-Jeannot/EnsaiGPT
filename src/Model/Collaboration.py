class Collaboration(self, id_collaboration, id_conversation, id_user, role):
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
        if id_collaboration is None:
            raise ValueError("id_collaboration ne peut pas être None")
        if id_conversation is None:
            raise ValueError("id_conversation ne peut pas être None")
        if id_user is None:
            raise ValueError("id_user ne peut pas être None")
        if role is None:
            raise ValueError("role ne peut pas être None")
        """
        self.id_collaboration__ = id_collaboration
        self.id_conversation = id_conversation
        self.id_user = id_user
        self.role = role
