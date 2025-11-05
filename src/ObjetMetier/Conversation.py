from datetime import datetime


class Conversation:
    """
    Représente une conversation dans le système.

    Attributs
    ----------
    id_conversation : int
        Identifiant unique de la conversation.
    titre : str
        Titre de la conversation.
    created_at : datetime
        Date et heure de création de la conversation.
    setting_conversation : str
        Paramètres ou contexte lié à la conversation.
    token_viewer : str
        Jeton permettant d’accéder à la conversation en lecture seule.
    token_writter : str
        Jeton permettant d’écrire dans la conversation.
    is_active : bool
        Indique si la conversation est encore active (True) ou archivée (False).
    """

    def __init__(
        self,
        id_conversation: int,
        titre: str,
        created_at: datetime,
        setting_conversation: str,
        token_viewer: str,
        token_writter: str,
        is_active: bool,
    ):
        """
        Initialise une nouvelle instance de Conversation avec vérifications de type.
        """

        # Vérifications de type
        if not isinstance(id_conversation, int):
            raise ValueError("id_conversation must be an integer")
        if not isinstance(titre, str):
            raise ValueError("titre must be a string")
        if not isinstance(created_at, datetime):
            raise ValueError("created_at must be a datetime object")
        if not isinstance(setting_conversation, str):
            raise ValueError("setting_conversation must be a string")
        if not isinstance(token_viewer, str):
            raise ValueError("token_viewer must be a string")
        if not isinstance(token_writter, str):
            raise ValueError("token_writter must be a string")
        if not isinstance(is_active, bool):
            raise ValueError("is_active must be a boolean")

        # Assignations
        self.id_conversation = id_conversation
        self.titre = titre
        self.created_at = created_at
        self.setting_conversation = setting_conversation
        self.token_viewer = token_viewer
        self.token_writter = token_writter
        self.is_active = is_active
