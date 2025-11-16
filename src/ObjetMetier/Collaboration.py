class Collaboration:
    """
    Représente la collaboration entre un utilisateur et une conversation.

    Attributs
    ----------
    id_collaboration : int | None
        Identifiant unique de la collaboration (None avant insertion).
    id_conversation : int
        Identifiant de la conversation concernée.
    id_user : int
        Identifiant de l’utilisateur.
    role : str
        Rôle de l’utilisateur : 'admin', 'viewer', 'writer' ou 'banni'.
    """

    def __init__(
        self,
        id_collaboration=None,
        id_conversation=None,
        id_user=None,
        role=None,
    ):
        """
        Initialise une instance de Collaboration avec validations.

        Paramètres
        ----------
        id_collaboration : int | None
            Identifiant unique (None avant insertion).
        id_conversation : int
            Identifiant de la conversation associée.
        id_user : int
            Identifiant de l'utilisateur.
        role : str
            Rôle ('admin', 'viewer', 'writer', 'banni').

        Raises
        ------
        ValueError
            Si un des champs ne respecte pas le type ou les valeurs attendues.
        """

        # --- Vérifications de type ---
        if id_collaboration is not None and not isinstance(id_collaboration, int):
            raise ValueError("id_collaboration must be an integer or None")
        if id_conversation is None or not isinstance(id_conversation, int):
            raise ValueError("id_conversation must be an integer")
        if id_user is None or not isinstance(id_user, int):
            raise ValueError("id_user must be an integer")
        if role is None or not isinstance(role, str):
            raise ValueError("role must be a non-null string")

        # --- Validation du rôle ---
        # Interdit tout espace, tabulation ou saut de ligne
        if any(ch.isspace() for ch in role):
            raise ValueError("role ne doit pas contenir d'espaces ou de caractères blancs")

        role_norm = role.lower()
        allowed_roles = {"admin", "viewer", "writer", "banni"}
        if role_norm not in allowed_roles:
            raise ValueError("role doit être 'admin', 'viewer', 'writer' ou 'banni'")

        # --- Assignations ---
        self.id_collaboration = id_collaboration
        self.id_conversation = id_conversation
        self.id_user = id_user
        self.role = role_norm

    def __eq__(self, other):
        """Compare deux collaborations champ à champ."""
        if not isinstance(other, Collaboration):
            return False
        return (
            self.id_collaboration == other.id_collaboration
            and self.id_conversation == other.id_conversation
            and self.id_user == other.id_user
            and self.role == other.role
        )

    def __str__(self):
        """Représentation lisible."""
        return (
            f"Collaboration(id_collaboration={self.id_collaboration}, "
            f"id_conversation={self.id_conversation}, "
            f"id_user={self.id_user}, role='{self.role}')"
        )

    def __repr__(self):
        """Représentation pour le débogage."""
        return self.__str__()
