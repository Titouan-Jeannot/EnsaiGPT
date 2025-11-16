import logging
from typing import List, Optional
from DAO.CollaborationDAO import CollaborationDAO
from DAO.UserDAO import UserDAO
from DAO.ConversationDAO import ConversationDAO
from ObjetMetier.Collaboration import Collaboration
from Utils.Singleton import Singleton
from Utils.log_decorator import log


class CollaborationService(metaclass=Singleton):
    """
    Service pour gérer la logique métier des collaborations.
    Cette couche interagit avec CollaborationDAO, UserDAO et ConversationDAO.
    """

    VALID_ROLES = {"admin", "writer", "viewer", "banni"}

    def __init__(self):
        self.collab_dao = CollaborationDAO()
        self.user_dao = UserDAO()
        self.conversation_dao = ConversationDAO()

    def _normalize_role(self, role: str) -> str:
        if not isinstance(role, str):
            raise ValueError("Rôle invalide.")
        norm = role.strip().lower()
        if norm not in self.VALID_ROLES:
            raise ValueError(
                "Rôle invalide. Les rôles autorisés sont: admin, writer, viewer, banni."
            )
        return norm

    def _require_collaboration(self, conversation_id: int, user_id: int) -> Collaboration:
        collab = self.collab_dao.find_by_conversation_and_user(conversation_id, user_id)
        if not collab:
            raise PermissionError("Accès refusé à cette conversation.")
        return collab

    def _require_admin(self, conversation_id: int, user_id: int) -> Collaboration:
        collab = self._require_collaboration(conversation_id, user_id)
        if collab.role.lower() != "admin":
            raise PermissionError("Seuls les administrateurs peuvent modifier les collaborateurs.")
        return collab

    def _count_collaborators(self, conversation_id: int) -> int:
        if hasattr(self.collab_dao, "count_by_conversation"):
            try:
                return int(self.collab_dao.count_by_conversation(conversation_id))
            except Exception:
                pass
        collaborations = self.collab_dao.find_by_conversation(conversation_id)
        return len(collaborations)

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
        """Crée une nouvelle collaboration (vérifie l'existence du user & de la conversation)."""
        try:
            # Vérifier que l’utilisateur et la conversation existent
            if not self.user_dao.read(user_id):
                raise ValueError(f"Utilisateur {user_id} introuvable.")
            if not self.conversation_dao.read(conversation_id):
                raise ValueError(f"Conversation {conversation_id} introuvable.")

            role_norm = self._normalize_role(role)

            # Vérifier qu’il n’existe pas déjà une collaboration pour cette paire
            existing = self.collab_dao.find_by_conversation_and_user(conversation_id, user_id)
            if existing:
                raise ValueError("Une collaboration existe déjà pour cet utilisateur dans cette conversation.")

            collab = Collaboration(
                id_conversation=conversation_id,
                id_user=user_id,
                role=role_norm
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

    def list_collaborators_for_user(self, conversation_id: int, requester_id: int) -> List[Collaboration]:
        """
        Liste les collaborateurs d'une conversation en vérifiant que l'utilisateur courant
        dispose bien d'un accès (admin/writer/viewer/banni).
        """
        self._require_collaboration(conversation_id, requester_id)
        return self.list_collaborators(conversation_id)

    @log
    def delete_collaborator(
        self, conversation_id: int, target_user_id: int, requester_id: int
    ) -> bool:
        """Supprime un collaborateur d'une conversation en vérifiant les droits."""
        self._require_admin(conversation_id, requester_id)
        target = self.collab_dao.find_by_conversation_and_user(conversation_id, target_user_id)
        if not target:
            raise ValueError("Collaborateur introuvable.")

        if target_user_id == requester_id and self._count_collaborators(conversation_id) <= 1:
            raise ValueError(
                "Impossible de modifier votre propre rôle tant que vous êtes seul dans cette conversation."
            )
        return self.collab_dao.delete_by_conversation_and_user(conversation_id, target_user_id)

    @log
    def change_role(
        self,
        conversation_id: int,
        target_user_id: int,
        new_role: str,
        requester_id: int,
    ) -> bool:
        """Change le rôle d’un utilisateur dans une conversation."""
        self._require_admin(conversation_id, requester_id)
        collab = self.collab_dao.find_by_conversation_and_user(conversation_id, target_user_id)
        if not collab:
            raise ValueError("Collaborateur introuvable.")

        role_norm = self._normalize_role(new_role)
        if target_user_id == requester_id and self._count_collaborators(conversation_id) <= 1:
            raise ValueError(
                "Impossible de modifier votre propre rôle tant que vous êtes seul dans cette conversation."
            )
        return self.collab_dao.update_role(collab.id_collaboration, role_norm)

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
