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
        id_message,  # peut être None
        id_conversation: int,
        id_user: int,
        datetime: timestamp,
        message: str,
        is_from_agent: bool,
    ):
        """
        Initialisation de la classe Message.
        - id_message peut être None si le message n'est pas encore inséré en base.
        """

        # Vérifications des types
        if id_message is not None and not isinstance(id_message, int):
            raise ValueError("id_message must be an integer or None")
        if not isinstance(id_conversation, int):
            raise ValueError("id_conversation must be an integer")
        if not isinstance(id_user, int):
            raise ValueError("id_user must be an integer")
        if not isinstance(datetime, timestamp):
            raise ValueError("datetime must be a timestamp (datetime object)")
        if not isinstance(message, str):
            raise ValueError("message must be a string")
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
