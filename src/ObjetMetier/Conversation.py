from datetime import datetime
from typing import Optional


class Conversation:
    """
    Représente une conversation dans le système.

    Attributs
    ----------
    id_conversation : int | None
        Identifiant unique de la conversation.
    titre : str
        Titre de la conversation.
    created_at : datetime
        Date et heure de création de la conversation.
    setting_conversation : str
        Paramètres ou contexte lié à la conversation.
    token_viewer : str | None
        Jeton (lecture seule). Peut être None à la création : généré en DAO.
    token_writter : str | None
        Jeton (écriture). Peut être None à la création : généré en DAO.
    is_active : bool
        Conversation active (True) ou archivée (False).
    """

    def __init__(
        self,
        id_conversation: Optional[int],
        titre: str,
        created_at: datetime,
        setting_conversation: str,
        token_viewer: Optional[str],
        token_writter: Optional[str],
        is_active: bool,
    ):
        """
        Initialise une instance de Conversation avec vérifications de type.
        Les tokens peuvent être None (ils seront complétés dans le DAO).
        """

        # Vérifications de type
        if id_conversation is not None and not isinstance(id_conversation, int):
            raise ValueError("id_conversation must be an integer or None")
        if not isinstance(titre, str):
            raise ValueError("titre must be a string")
        if not isinstance(created_at, datetime):
            raise ValueError("created_at must be a datetime object")
        if not isinstance(setting_conversation, str):
            raise ValueError("setting_conversation must be a string")
        # ⬇️ Assouplissement : autoriser None ou str pour les tokens
        if token_viewer is not None and not isinstance(token_viewer, str):
            raise ValueError("token_viewer must be a string or None")
        if token_writter is not None and not isinstance(token_writter, str):
            raise ValueError("token_writter must be a string or None")
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
