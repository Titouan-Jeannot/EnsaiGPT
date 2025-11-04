"""Service métier pour les collaborations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.DAO.CollaborationDAO import CollaborationDAO
from src.DAO.ConversationDAO import ConversationDAO
from src.DAO.User_DAO import UserDAO
from src.ObjetMetier.Collaboration import Collaboration


@dataclass(slots=True)
class CollaborationService:
    """Manipule les collaborations en appliquant les règles métier."""

    collaboration_dao: CollaborationDAO
    user_dao: UserDAO
    conversation_dao: ConversationDAO

    def _get_collaboration(self, user_id: int, conversation_id: int) -> Collaboration | None:
        return self.collaboration_dao.find_by_user_and_conversation(user_id, conversation_id)

    def is_admin(self, user_id: int, conversation_id: int) -> bool:
        collab = self._get_collaboration(user_id, conversation_id)
        return bool(collab and collab.is_admin())

    def is_writer(self, user_id: int, conversation_id: int) -> bool:
        collab = self._get_collaboration(user_id, conversation_id)
        return bool(collab and collab.can_write())

    def is_viewer(self, user_id: int, conversation_id: int) -> bool:
        collab = self._get_collaboration(user_id, conversation_id)
        return bool(collab and collab.role != "BANNED")

    def create_collab(self, user_id: int, conversation_id: int, role: str) -> Collaboration:
        if self.user_dao.read(user_id) is None:
            raise ValueError("Utilisateur introuvable")
        if self.conversation_dao.get_by_id(conversation_id) is None:
            raise ValueError("Conversation introuvable")
        collaboration = Collaboration(
            id_collaboration=None,
            id_conversation=conversation_id,
            id_user=user_id,
            role=role,
        )
        return self.collaboration_dao.create(collaboration)

    def verify_token_collaboration(self, conversation_id: int, token: str) -> bool:
        conversation = self.conversation_dao.get_by_id(conversation_id)
        if conversation is None:
            return False
        return token in {conversation.token_viewer, conversation.token_writter}

    def add_collaboration(self, collab: Collaboration) -> Collaboration:
        return self.collaboration_dao.create(collab)

    def list_collaborators(self, conversation_id: int) -> List[Collaboration]:
        return self.collaboration_dao.list_by_conversation(conversation_id)

    def delete_collaborator(self, conversation_id: int, user_id: int) -> bool:
        collab = self._get_collaboration(user_id, conversation_id)
        if collab is None:
            return False
        return self.collaboration_dao.delete(collab.id_collaboration or 0)

    def change_role(self, conversation_id: int, user_id: int, new_role: str) -> Collaboration:
        collab = self._get_collaboration(user_id, conversation_id)
        if collab is None:
            raise ValueError("Collaboration introuvable")
        candidate = new_role.upper()
        if candidate not in {"ADMIN", "WRITER", "VIEWER", "BANNED"}:
            raise ValueError("Nouveau rôle invalide")
        collab.role = candidate
        self.collaboration_dao.update(collab)
        return collab
