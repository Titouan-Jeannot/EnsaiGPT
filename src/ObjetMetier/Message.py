from datetime import datetime as timestamp


class Message:
    """
    Classe représentant un message d'une conversation.

    Attributs
    ----------
    id_message : int
        Identifiant unique du message.
    id_conversation : int
        Identifiant de la conversation à laquelle appartient le message.
    id_user : int
        Identifiant de l'utilisateur qui a envoyé le message.
    datetime : datetime
        Date et heure d'envoi du message.
    message : str
        Contenu textuel du message.
    is_from_agent : bool
        Indique si le message provient de l’agent (True) ou d’un utilisateur (False).
    """

    def __init__(
        self,
        id_message=None,  # peut être None
        id_conversation=None,
        id_user=None,
        datetime=None,
        message=None,
        is_from_agent=None,
    ):
        """
        Initialisation de la classe Message.
        - id_message peut être None si le message n'est pas encore inséré en base.
        - id_user, datetime et is_from_agent deviennent optionnels pour compatibilité avec les tests.
        """

        # Valeurs par défaut si non fournies
        if datetime is None:
            datetime = timestamp.now()
        if id_user is None:
            id_user = -1  # valeur par défaut neutre
        if is_from_agent is None:
            is_from_agent = False

        # Vérifications des types
        if id_message is not None and not isinstance(id_message, int):
            raise ValueError("id_message must be an integer or None")
        if id_conversation is None or not isinstance(id_conversation, int):
            raise ValueError("id_conversation must be an integer non null")
        if not isinstance(id_user, int):
            raise ValueError("id_user must be an integer")
        if not isinstance(datetime, timestamp):
            raise ValueError("datetime must be a timestamp (datetime object)")
        if message is None or not isinstance(message, str):
            raise ValueError("message must be a non-empty string")
        if not isinstance(is_from_agent, bool):
            raise ValueError("is_from_agent must be a boolean")

        self.id_message = id_message
        self.id_conversation = id_conversation
        self.id_user = id_user
        self.datetime = datetime
        self.message = message
        self.is_from_agent = is_from_agent

    def __eq__(self, other):
        if not isinstance(other, Message):
            return False
        return (
            self.id_message == other.id_message
            and self.id_conversation == other.id_conversation
            and self.id_user == other.id_user
            and self.datetime == other.datetime
            and self.message == other.message
            and self.is_from_agent == other.is_from_agent
        )

    def __str__(self):
        author = "Agent" if self.is_from_agent else "User"
        return f"[{self.datetime}] {author}({self.id_user}) : {self.message}"

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Crée une instance de Message depuis un dictionnaire."""
        return cls(
            id_message=data.get("id_message"),
            id_conversation=data["id_conversation"],
            id_user=data.get("id_user", -1),
            datetime=data.get("datetime", timestamp.now()),
            message=data["message"],
            is_from_agent=data.get("is_from_agent", False),
        )

    def to_dict(self) -> dict:
        """Convertit le message en dictionnaire."""
        return {
            "id_message": self.id_message,
            "id_conversation": self.id_conversation,
            "id_user": self.id_user,
            "datetime": self.datetime,
            "message": self.message,
            "is_from_agent": self.is_from_agent,
        }
