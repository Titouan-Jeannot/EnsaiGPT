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
    def __init__(self,
                id_conversation: int,
                titre: str,
                created_at: datetime,
                setting_conversation: str,
                token_viewer: str,
                token_writter: str,
                is_active: bool):
        """
        Initialise une nouvelle instance de Conversation.
        """
        self.id_conversation = id_conversation
        self.titre = titre
        self.created_at = created_at
        self.setting_conversation = setting_conversation
        self.token_viewer = token_viewer
        self.token_writter = token_writter
        self.is_active = is_active
