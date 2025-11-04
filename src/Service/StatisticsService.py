"""Service fournissant des statistiques d'utilisation."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import timedelta
from typing import List

from src.DAO.CollaborationDAO import CollaborationDAO
from src.DAO.ConversationDAO import ConversationDAO
from src.DAO.Message_DAO import MessageDAO
from src.DAO.User_DAO import UserDAO
from src.ObjetMetier.Conversation import Conversation
from src.ObjetMetier.User import User


@dataclass(slots=True)
class StatisticsService:
    """Calcule des agrégats simples sur l'activité de la plateforme."""

    user_dao: UserDAO
    conversation_dao: ConversationDAO
    message_dao: MessageDAO
    collaboration_dao: CollaborationDAO

    def _conversations_for_user(self, user_id: int) -> List[Conversation]:
        conv_ids = [
            collab.id_conversation
            for collab in self.collaboration_dao.list_by_user(user_id)
            if collab.role != "BANNED"
        ]
        return self.conversation_dao.list_by_ids(conv_ids)

    def nb_conv(self, user_id: int) -> int:
        return len(self._conversations_for_user(user_id))

    def nb_messages(self, user_id: int) -> int:
        return len(self.message_dao.list_by_user(user_id))

    def nb_messages_de_user_par_conv(self, user_id: int, conversation_id: int) -> int:
        return sum(
            1
            for message in self.message_dao.list_by_conversation(conversation_id)
            if message.id_user == user_id
        )

    def nb_message_conv(self, conversation_id: int) -> int:
        return len(self.message_dao.list_by_conversation(conversation_id))

    def temps_passe_par_conv(self, user_id: int, conversation_id: int) -> timedelta:
        timestamps = [
            message.datetime_sent
            for message in self.message_dao.list_by_conversation(conversation_id)
            if message.id_user == user_id
        ]
        if len(timestamps) < 2:
            return timedelta(0)
        return max(timestamps) - min(timestamps)

    def temps_passe(self, user_id: int) -> timedelta:
        total = timedelta(0)
        for conversation in self._conversations_for_user(user_id):
            total += self.temps_passe_par_conv(user_id, conversation.id_conversation or 0)
        return total

    def top_active_users(self, limit: int = 3) -> List[User]:
        counts: Counter[int] = Counter()
        for message in self.message_dao.list_all():
            counts[message.id_user] += 1
        ranked_ids = [user_id for user_id, _ in counts.most_common(limit)]
        return [user for user_id in ranked_ids if (user := self.user_dao.read(user_id))]

    def average_message_length(self) -> float:
        lengths = [len(message.message) for message in self.message_dao.list_all()]
        if not lengths:
            return 0.0
        return sum(lengths) / len(lengths)
