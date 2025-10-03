from datetime import datetime

class Message:
    """
    Représente un message échangé dans une conversation.

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

    def __init__(self,
                 id_message: int,
                 id_conversation: int,
                 id_user: int,
                 datetime: datetime,
                 message: str,
                 is_from_agent: bool):
        """
        Initialise une instance de Message.
        """
        self.id_message = id_message
        self.id_conversation = id_conversation
        self.id_user = id_user
        self.datetime = datetime
        self.message = message
        self.is_from_agent = is_from_agent
