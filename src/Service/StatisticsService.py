from typing import List, Optional, Dict, Tuple, TYPE_CHECKING
import datetime
import logging

# -----------------------------
# Import des entités métiers
# -----------------------------
try:
    from ObjetMetier.Message import Message
    from ObjetMetier.Conversation import Conversation
    from ObjetMetier.User import User
    from ObjetMetier.Collaboration import Collaboration
except Exception:
    from ObjetMetier.Message import Message  # type: ignore
    from ObjetMetier.Conversation import Conversation  # type: ignore
    from ObjetMetier.User import User  # type: ignore
    from ObjetMetier.Collaboration import Collaboration  # type: ignore

# -----------------------------
# Typage conditionnel (DAO uniquement pour mypy)
# -----------------------------
if TYPE_CHECKING:
    from DAO.MessageDAO import MessageDAO
    from DAO.ConversationDAO import ConversationDAO
    from DAO.CollaborationDAO import CollaborationDAO
    from DAO.UserDAO import UserDAO
else:
    MessageDAO = object  # type: ignore
    ConversationDAO = object  # type: ignore
    CollaborationDAO = object  # type: ignore
    UserDAO = object  # type: ignore


class StatisticsService:
    """
    Service de statistiques adapté aux DAO présents dans le projet.

    Stratégie :
    - Priorité aux méthodes DAO dédiées (count_*, get_*).
    - Sinon, collecte via les DAO disponibles (collaborations/conversations)
      puis parcours Python des messages (MessageDAO.get_messages_by_conversation).
    """

    def __init__(
        self,
        message_dao: MessageDAO,
        conversation_dao: Optional[ConversationDAO] = None,
        collaboration_dao: Optional[CollaborationDAO] = None,
        user_dao: Optional[UserDAO] = None,
        idle_threshold: datetime.timedelta = datetime.timedelta(minutes=10),
    ):
        self.message_dao = message_dao
        self.conversation_dao = conversation_dao
        self.collaboration_dao = collaboration_dao
        self.user_dao = user_dao
        self.idle_threshold = idle_threshold

    # ------------------------------------------------------------
    #                       UTILITAIRES
    # ------------------------------------------------------------
    def _get_callable(self, obj, *names):
        for n in names:
            fn = getattr(obj, n, None)
            if callable(fn):
                return fn
        return None

    def _validate_id(self, name: str, value: int) -> None:
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} invalide")

    # ------------------------------------------------------------
    #                    NOMBRE DE CONVERSATIONS
    # ------------------------------------------------------------
    def nb_conv(self, user_id: int) -> int:
        """
        Calcule le nombre de conversations ACTIVES distinctes auxquelles un utilisateur a
        participé, en utilisant les DAO disponibles.
        """
        self._validate_id("user_id", user_id)

        # 1) CollaborationDAO.find_by_user -> unique conversations
        if self.collaboration_dao:
            try:
                colls: List[Collaboration] = self.collaboration_dao.find_by_user(user_id)
                return len({c.id_conversation for c in colls})
            except Exception:
                logging.exception("Nombre de converation : Erreur en utilisant CollaborationDAO")


    # ------------------------------------------------------------
    #                    NOMBRE DE MESSAGES
    # ------------------------------------------------------------
    def nb_messages(self, user_id: int) -> int:
        """
        Calcule le nombre de messages envoyés par un utilisateur, en utilisant les DAO disponibles.
        """
        self._validate_id("user_id", user_id)




        # 1) DAO direct count
        fn = self.message_dao.count_messages_by_user
        if callable(fn):
            try:
                return int(fn(user_id))
            except Exception:
                logging.exception("nb_messages: échec méthode count_messages_by_user")


    def nb_message_conv(self, conversation_id: int) -> int:
        """
        Calcule le nombre de messages dans une conversation donnée, en utilisant les DAO disponibles.
        """
        self._validate_id("conversation_id", conversation_id)

        fn = self.message_dao.count_messages_by_conversation
        if callable(fn):
            try:
                return int(fn(conversation_id))
            except Exception:
                logging.exception("nb_message_conv: échec méthode count_messages_by_conversation")


    def nb_messages_de_user_par_conv(self, user_id: int, conversation_id: int) -> int:
        self._validate_id("user_id", user_id)
        self._validate_id("conversation_id", conversation_id)

        fn = self.message_dao.count_messages_by_user_in_conversation
        if callable(fn):
            try:
                return int(fn(user_id, conversation_id))
            except Exception:
                logging.exception("nb_messages_de_user_par_conv: count direct échoue")



    def average_message_length(self, user_id: Optional[int] = None) -> float:
        """
        Calcule la longueur moyenne des messages.
        - si user_id fourni : moyenne sur les messages de cet utilisateur
        - sinon : moyenne globale
        """
        # Calcul pour un utilisateur donné
        if user_id is not None:
            fn = self.message_dao.get_messages_by_user
            if fn:
                try:
                    msgs: List[Message] = fn(user_id)
                    if not msgs:
                        return 0.0
                    total = sum(len(str(getattr(m, "message", "") or "")) for m in msgs)
                    return round(total / len(msgs))
                except Exception:
                    logging.exception("average_message_length: get_messages_by_user échoue")

