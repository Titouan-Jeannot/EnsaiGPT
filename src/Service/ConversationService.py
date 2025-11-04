"""Service métier pour les conversations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.DAO.CollaborationDAO import CollaborationDAO
from src.DAO.ConversationDAO import ConversationDAO
from src.ObjetMetier.Collaboration import Collaboration
from src.ObjetMetier.Conversation import Conversation


@dataclass(slots=True)
class ConversationService:
    """Coordonne la gestion des conversations."""

    conversation_dao: ConversationDAO
    collaboration_dao: CollaborationDAO

    def create_conversation(
        self, conversation: Conversation, owner_id: int
    ) -> Conversation:
        created = self.conversation_dao.create(conversation)
        self.collaboration_dao.create(
            Collaboration(
                id_collaboration=None,
                id_conversation=created.id_conversation or 0,
                id_user=owner_id,
                role="ADMIN",
            )
        )
        return created

    def get_conversation_by_id(self, conversation_id: int) -> Optional[Conversation]:
        return self.conversation_dao.get_by_id(conversation_id)

    def get_list_conv(self, user_id: int) -> List[Conversation]:
        collaborations = self.collaboration_dao.list_by_user(user_id)
        conversation_ids = [collab.id_conversation for collab in collaborations]
        conversations = self.conversation_dao.list_by_ids(conversation_ids)
        return [conv for conv in conversations if conv.is_active]

    def get_list_conv_by_date(self, user_id: int, target_date: datetime) -> List[Conversation]:
        conversations = self.get_list_conv(user_id)
        return [conv for conv in conversations if conv.created_at.date() == target_date.date()]

    def get_list_conv_by_title(self, user_id: int, title: str) -> List[Conversation]:
        keyword = title.lower()
        conversations = self.get_list_conv(user_id)
        return [conv for conv in conversations if keyword in conv.titre.lower()]

    def modify_title(
        self,
        conversation_id: int,
        new_title: str,
        actor_id: Optional[int] = None,
    ) -> Conversation:
        if not new_title or not new_title.strip():
            raise ValueError("Titre invalide")
        conversation = self.conversation_dao.get_by_id(conversation_id)
        if conversation is None:
            raise ValueError("Conversation introuvable")
        if actor_id is not None:
            collab = self.collaboration_dao.find_by_user_and_conversation(actor_id, conversation_id)
            if collab is None or not collab.can_write():
                raise PermissionError("L'utilisateur ne peut pas modifier cette conversation")
        conversation.titre = new_title.strip()
        self.conversation_dao.update(conversation)
        return conversation

    def delete_conversation(self, conversation_id: int, actor_id: Optional[int] = None) -> bool:
        if actor_id is not None:
            collab = self.collaboration_dao.find_by_user_and_conversation(actor_id, conversation_id)
            if collab is None or not collab.is_admin():
                raise PermissionError("Seul un administrateur peut supprimer la conversation")
        return self.conversation_dao.delete(conversation_id)
