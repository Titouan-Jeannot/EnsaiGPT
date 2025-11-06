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
        Paramètres ou contexte lié à la conversation (JSON sous forme de chaîne).
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
        created_at: Optional[datetime] = None,
        setting_conversation: Optional[str] = None,
        token_viewer: Optional[str] = None,
        token_writter: Optional[str] = None,
        is_active: Optional[bool] = None,
    ):
        """
        Initialise une instance de Conversation avec vérifications de type.
        Les tokens peuvent être None (ils seront complétés dans le DAO).
        Les paramètres non fournis reçoivent des valeurs par défaut
        compatibles avec les tests unitaires.

        Paramètres
        ----------
        id_conversation : int | None
            Identifiant unique de la conversation. Peut être None avant insertion en base.
        titre : str
            Titre de la conversation (peut être vide, ex: "").
        created_at : datetime, optionnel
            Date et heure de création. Par défaut : datetime.now().
        setting_conversation : str, optionnel
            Paramètres liés à la conversation (par défaut "{}").
        token_viewer : str | None, optionnel
            Jeton de lecture seule (None par défaut).
        token_writter : str | None, optionnel
            Jeton d’écriture (None par défaut).
        is_active : bool, optionnel
            Indique si la conversation est active (True par défaut).

        Raises
        ------
        ValueError
            Si les types ou valeurs des paramètres ne sont pas conformes.
        """

        # --- Vérifications de type minimales ---
        if id_conversation is not None and not isinstance(id_conversation, int):
            raise ValueError("id_conversation must be an integer or None")
        if not isinstance(titre, str):
            raise ValueError("titre must be a string")

        # --- Valeurs par défaut (compatibilité tests / usage pratique) ---
        if created_at is None:
            created_at = datetime.now()
        if setting_conversation is None:
            setting_conversation = "{}"
        if is_active is None:
            is_active = True

        # --- Vérifications supplémentaires ---
        if not isinstance(created_at, datetime):
            raise ValueError("created_at must be a datetime object")
        if not isinstance(setting_conversation, str):
            raise ValueError("setting_conversation must be a string")
        if token_viewer is not None and not isinstance(token_viewer, str):
            raise ValueError("token_viewer must be a string or None")
        if token_writter is not None and not isinstance(token_writter, str):
            raise ValueError("token_writter must be a string or None")
        if not isinstance(is_active, bool):
            raise ValueError("is_active must be a boolean")

        # --- Assignations ---
        self.id_conversation = id_conversation
        self.titre = titre
        self.created_at = created_at
        self.setting_conversation = setting_conversation
        self.token_viewer = token_viewer
        self.token_writter = token_writter
        self.is_active = is_active

    def __eq__(self, other) -> bool:
        """Compare deux objets Conversation champ à champ."""
        if not isinstance(other, Conversation):
            return False
        return (
            self.id_conversation == other.id_conversation
            and self.titre == other.titre
            and self.created_at == other.created_at
            and self.setting_conversation == other.setting_conversation
            and self.token_viewer == other.token_viewer
            and self.token_writter == other.token_writter
            and self.is_active == other.is_active
        )

    def __repr__(self) -> str:
        """Représentation textuelle complète (utile pour le débogage)."""
        return (
            f"Conversation(id_conversation={self.id_conversation}, "
            f"titre={self.titre!r}, created_at={self.created_at!r}, "
            f"setting_conversation={self.setting_conversation!r}, "
            f"token_viewer={self.token_viewer!r}, "
            f"token_writter={self.token_writter!r}, "
            f"is_active={self.is_active})"
        )
