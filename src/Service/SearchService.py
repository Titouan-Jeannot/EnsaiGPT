from datetime import datetime
from typing import List

from src.DAO.CollaborationDAO import CollaborationDAO
from src.DAO.ConversationDAO import ConversationDAO

# Importez vos DAOs
from src.DAO.MessageDAO import MessageDAO

# Importez vos classes métiers
from src.Objet_Metier.Message import Message
from src.ObjetMetier.Collaboration import Collaboration  # Utile pour le type-hinting
from src.ObjetMetier.Conversation import Conversation


class SearchService:
    """
    Service dédié à la recherche dans les messages et les conversations.
    Toutes les recherches sont filtrées pour n'afficher que le contenu
    accessible par l'utilisateur (via CollaborationDAO).
    """

    def __init__(
        self,
        message_dao: MessageDAO,
        conversation_dao: ConversationDAO,
        collaboration_dao: CollaborationDAO,
    ):
        self.message_dao = message_dao
        self.conversation_dao = conversation_dao
        self.collaboration_dao = collaboration_dao
        # Note: L'injection de dépendances est la bonne pratique ici.

    # ------------------------------------------------------------------ #
    # Helper privé pour garantir la sécurité                               #
    # ------------------------------------------------------------------ #

    def _get_user_accessible_conversation_ids(self, user_id: int) -> List[int]:
        """
        Récupère les IDs des conversations auxquelles l'utilisateur a accès.
        """
        # 1. Utilise la méthode existante dans CollaborationDAO
        collaborations: List[Collaboration] = self.collaboration_dao.find_by_user(user_id)

        # 2. Filtre par rôle autorisé pour la recherche (ADMIN, WRITER, VIEWER)
        allowed_roles = {"ADMIN", "WRITER", "VIEWER"}

        conversation_ids = [
            c.id_conversation
            for c in collaborations
            # On normalise en majuscule, même si le DAO renvoie en minuscule
            if c.role.upper() in allowed_roles
        ]
        return conversation_ids

    # ------------------------------------------------------------------ #
    # Recherche dans les MESSAGES (Utilise CollaborationDAO + MessageDAO)  #
    # ------------------------------------------------------------------ #

    def search_messages_by_keyword(self, user_id: int, keyword: str) -> List[Message]:
        """
        Recherche des messages par mot-clé, limités aux conversations de l'utilisateur.
        """
        if not keyword:
            return []

        # 1. Obtenir les IDs autorisés
        conversation_ids = self._get_user_accessible_conversation_ids(user_id)
        if not conversation_ids:
            return []

        # 2. Déléguer la recherche multi-conversation au MessageDAO
        return self.message_dao.search_by_keyword(keyword, conversation_ids)

    def search_messages_by_date(self, user_id: int, target_date: datetime) -> List[Message]:
        """
        Recherche des messages par date (journée entière), limités aux conversations de l'utilisateur.
        """
        # 1. Obtenir les IDs autorisés
        conversation_ids = self._get_user_accessible_conversation_ids(user_id)
        if not conversation_ids:
            return []

        # 2. Déléguer la recherche par date multi-conversation au MessageDAO
        return self.message_dao.search_by_date(target_date, conversation_ids)

    # ------------------------------------------------------------------ #
    # Recherche dans les CONVERSATIONS (Utilise ConversationDAO)           #
    # ------------------------------------------------------------------ #

    def search_conversations_by_keyword(self, user_id: int, keyword: str) -> List[Conversation]:
        """
        Recherche des conversations par mot-clé dans le titre, limitées à celles de l'utilisateur.
        """
        if not keyword:
            return []

        # ConversationDAO gère directement la jointure avec les collaborations de l'utilisateur
        return self.conversation_dao.search_conversations_by_title(user_id, keyword)

    def search_conversations_by_date(
        self, user_id: int, target_date: datetime
    ) -> List[Conversation]:
        """
        Recherche des conversations par date de création (journée entière), limitées à celles de l'utilisateur.
        """
        # ConversationDAO gère directement la jointure avec les collaborations de l'utilisateur
        # et le filtre par date de création.
        return self.conversation_dao.get_conversations_by_date(user_id, target_date)
