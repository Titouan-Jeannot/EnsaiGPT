import logging
from typing import List
from src.DAO.CollaborationDAO import CollaborationDAO
from src.DAO.UserDAO import UserDAO
from src.DAO.ConversationDAO import ConversationDAO
from src.ObjetMetier.Collaboration import Collaboration
from src.Utils.Singleton import Singleton
from src.Utils.log_decorator import log


class CollaborationService(metaclass=Singleton):
    """
    Service pour gérer la logique métier des collaborations.
    Cette couche interagit avec CollaborationDAO, UserDAO et ConversationDAO.
    """

    def __init__(self):
        self.collab_dao = CollaborationDAO()
        self.user_dao = UserDAO()
        self.conversation_dao = ConversationDAO()

    # ------------------------------
    # Vérification des rôles
    # ------------------------------

    @log
    def is_admin(self, user_id: int, conversation_id: int) -> bool:
        """Vérifie si un utilisateur est admin dans une conversation."""
        collab = self.collab_dao.find_by_conversation_and_user(conversation_id, user_id)
        return collab is not None and collab.role.lower() == "admin"

    @log
    def is_writer(self, user_id: int, conversation_id: int) -> bool:
        """Vérifie si un utilisateur est writer dans une conversation."""
        collab = self.collab_dao.find_by_conversation_and_user(conversation_id, user_id)
        return collab is not None and collab.role.lower() == "writer"

    @log
    def is_viewer(self, user_id: int, conversation_id: int) -> bool:
        """Vérifie si un utilisateur est viewer dans une conversation."""
        collab = self.collab_dao.find_by_conversation_and_user(conversation_id, user_id)
        return collab is not None and collab.role.lower() == "viewer"

    # ------------------------------
    # Gestion des collaborations
    # ------------------------------

    @log
    def create_collab(self, user_id: int, conversation_id: int, role: str) -> bool:
        """Crée une nouvelle collaboration (vérifie l’existence du user & de la conversation)."""
        try:
            # Vérifier que l’utilisateur et la conversation existent
            if not self.user_dao.read(user_id):
                raise ValueError(f"Utilisateur {user_id} introuvable.")
            if not self.conversation_dao.read(conversation_id):
                raise ValueError(f"Conversation {conversation_id} introuvable.")

            # Vérifier que le rôle est valide
            if role.lower() not in {"admin", "writer", "viewer", "banned"}:
                raise ValueError("Rôle invalide.")

            # Vérifier qu’il n’existe pas déjà une collaboration pour cette paire
            existing = self.collab_dao.find_by_conversation_and_user(conversation_id, user_id)
            if existing:
                raise ValueError("Une collaboration existe déjà pour cet utilisateur dans cette conversation.")

            collab = Collaboration(
                id_conversation=conversation_id,
                id_user=user_id,
                role=role
            )
            return self.collab_dao.create(collab)
        except Exception as e:
            logging.error(f"Erreur dans create_collab : {e}")
            return False

    @log
    def add_collaboration(self, collab: Collaboration) -> bool:
        """Ajoute une collaboration directement (objet Collaboration)."""
        return self.collab_dao.create(collab)

    @log
    def list_collaborators(self, conversation_id: int) -> List[Collaboration]:
        """Liste tous les collaborateurs d'une conversation."""
        return self.collab_dao.find_by_conversation(conversation_id)

    @log
    def delete_collaborator(self, conversation_id: int, user_id: int) -> bool:
        """Supprime un collaborateur d'une conversation."""
        return self.collab_dao.delete_by_conversation_and_user(conversation_id, user_id)

    @log
    def change_role(self, conversation_id: int, user_id: int, new_role: str) -> bool:
        """Change le rôle d’un utilisateur dans une conversation."""
        collab = self.collab_dao.find_by_conversation_and_user(conversation_id, user_id)
        if not collab:
            logging.warning("Collaboration inexistante.")
            return False
        return self.collab_dao.update_role(collab.id_collaboration, new_role)

    # ------------------------------
    # Vérification des tokens
    # ------------------------------

    @log
    def verify_token_collaboration(self, conversation_id: int, token: str) -> bool:
        """
        Vérifie si un token (viewer ou writer) correspond à une conversation.

        Comportement attendu par les tests :
        - False si la conversation n'existe pas
        - True si le token correspond à token_viewer ou token_writter
        - False sinon
        """
        conv = self.conversation_dao.read(conversation_id)
        if conv is None:
            return False

        if token == getattr(conv, "token_viewer", None):
            return True
        if token == getattr(conv, "token_writter", None):
            return True

        return False

    def add_collab_by_token(
        self, conversation_id: int, token: str, user_id: int
    ) -> bool:
        """
        Ajoute une collaboration à un utilisateur en fonction du token fourni.

        Comportement attendu par les tests :
        - False si la conversation n'existe pas
        - Ajoute en tant que viewer si le token correspond à token_viewer
        - Ajoute en tant que writer si le token correspond à token_writter
        - False sinon
        """
        conv = self.conversation_dao.read(conversation_id)
        if conv is None:
            return False

        if token == getattr(conv, "token_viewer", None):
            return self.create_collab(user_id, conversation_id, "viewer")
        if token == getattr(conv, "token_writter", None):
            return self.create_collab(user_id, conversation_id, "writer")

        return False
