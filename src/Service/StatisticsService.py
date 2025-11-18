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


    # ------------------------------------------------------------
    #                    TEMPS PASSÉ (SESSIONS)
    # ------------------------------------------------------------
    def temps_passe(self, user_id: int, *, simple_window: bool = False) -> datetime.timedelta:
        self._validate_id("user_id", user_id)

        if simple_window:
            timestamps = self._get_sorted_timestamps_for_user(user_id)
            return self._compute_sessions_duration(timestamps, simple_window=True)

        total = datetime.timedelta(0)
        conv_ids = self._get_conversation_ids_of_user(user_id)

        if not conv_ids:
            timestamps = self._get_sorted_timestamps_for_user(user_id)
            return self._compute_sessions_duration(timestamps, simple_window=False)

        for cid in conv_ids:
            ts = self._get_sorted_timestamps_for_user_in_conv(user_id, cid)
            total += self._compute_sessions_duration(ts, simple_window=False)

        return total

    def temps_passe_par_conv(self, user_id: int, conversation_id: int, *, simple_window: bool = False) -> datetime.timedelta:
        self._validate_id("user_id", user_id)
        self._validate_id("conversation_id", conversation_id)
        timestamps = self._get_sorted_timestamps_for_user_in_conv(user_id, conversation_id)
        return self._compute_sessions_duration(timestamps, simple_window=simple_window)

    # ------------------------------------------------------------
    #                        AGRÉGATS
    # ------------------------------------------------------------
    def top_active_users(self, limit: int = 10) -> List[Tuple[int, int]]:
        if limit <= 0:
            raise ValueError("limit doit être > 0")

        # 1) DAO direct
        fn = self._get_callable(self.message_dao, "get_top_users_by_message_count", "top_users")
        if fn:
            try:
                rows = fn(limit)
                norm: List[Tuple[int, int]] = []
                for r in rows:
                    if isinstance(r, tuple) and len(r) >= 2:
                        norm.append((int(r[0]), int(r[1])))
                    elif isinstance(r, dict) and {"user_id", "count"} <= set(r.keys()):
                        norm.append((int(r["user_id"]), int(r["count"])))
                return norm
            except Exception:
                logging.exception("top_active_users: DAO top users échoue")

        # 2) Fallback: parcourir collaborations/conversations/messages
        counts: Dict[int, int] = {}
        # try message_dao.get_all_messages_minimal
        fn_all = self._get_callable(self.message_dao, "get_all_messages_minimal", "get_all_messages", "get_all")
        if fn_all:
            try:
                msgs: List[Message] = fn_all()
                for m in msgs:
                    uid = int(getattr(m, "id_user", 0))
                    counts[uid] = counts.get(uid, 0) + 1
                result = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
                return [(int(uid), int(c)) for uid, c in result]
            except Exception:
                logging.exception("top_active_users: get_all_messages fallback échoue")

        # try CollaborationDAO.list_all -> get unique conversations and iterate
        if self.collaboration_dao:
            fn_list = self._get_callable(self.collaboration_dao, "list_all", "find_by_conversation")
            if fn_list:
                try:
                    colls = self.collaboration_dao.list_all()
                    conv_ids = list({c.id_conversation for c in colls})
                    get_msgs = self._get_callable(self.message_dao, "get_messages_by_conversation", "get_by_conversation")
                    if not callable(get_msgs):
                        raise RuntimeError("MessageDAO ne fournit pas get_messages_by_conversation")
                    for cid in conv_ids:
                        msgs = get_msgs(cid)
                        for m in msgs:
                            uid = int(getattr(m, "id_user", 0))
                            counts[uid] = counts.get(uid, 0) + 1
                    result = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
                    return [(int(uid), int(c)) for uid, c in result]
                except Exception:
                    logging.exception("top_active_users: fallback via collaborations échoue")

        raise RuntimeError("Aucune méthode DAO compatible pour top_active_users")

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


    # ------------------------------------------------------------
    #                MÉTHODES INTERNES D’AIDE
    # ------------------------------------------------------------
    def _get_sorted_timestamps_for_user(self, user_id: int) -> List[datetime.datetime]:
        # recupere les timestamps pour un user sur toutes ses conversations
        conv_ids = self._get_conversation_ids_of_user(user_id)
        timestamps: List[datetime.datetime] = []
        get_msgs = self._get_callable(self.message_dao, "get_messages_by_conversation", "get_by_conversation")
        if not callable(get_msgs):
            # try get_messages_by_user if available
            fn_user = self._get_callable(self.message_dao, "get_messages_by_user", "get_by_user")
            if fn_user:
                try:
                    msgs: List[Message] = fn_user(user_id)
                    return sorted([m.datetime for m in msgs if getattr(m, "datetime", None)], key=lambda t: t)
                except Exception:
                    logging.exception("_get_sorted_timestamps_for_user: get_messages_by_user échoue")
            return []
        for cid in conv_ids:
            try:
                msgs = get_msgs(cid)
                timestamps.extend([m.datetime for m in msgs if int(getattr(m, "id_user", -1)) == user_id and getattr(m, "datetime", None)])
            except Exception:
                logging.exception("_get_sorted_timestamps_for_user: échec lecture messages conv %s", cid)
        return sorted(timestamps, key=lambda t: t)

    def _get_sorted_timestamps_for_user_in_conv(self, user_id: int, conversation_id: int) -> List[datetime.datetime]:
        get_by_conv_and_user = self._get_callable(self.message_dao, "get_messages_by_conversation_and_user", "get_by_conversation_and_user")
        if callable(get_by_conv_and_user):
            try:
                msgs: List[Message] = get_by_conv_and_user(conversation_id, user_id)
                return sorted([m.datetime for m in msgs if getattr(m, "datetime", None)], key=lambda t: t)
            except Exception:
                logging.exception("_get_sorted_timestamps_for_user_in_conv: get_messages_by_conversation_and_user échoue")

        get_conv = self._get_callable(self.message_dao, "get_messages_by_conversation", "get_by_conversation")
        if callable(get_conv):
            try:
                msgs: List[Message] = get_conv(conversation_id)
                return sorted([m.datetime for m in msgs if int(getattr(m, "id_user", -1)) == user_id and getattr(m, "datetime", None)], key=lambda t: t)
            except Exception:
                logging.exception("_get_sorted_timestamps_for_user_in_conv: get_messages_by_conversation échoue")

        raise RuntimeError("Impossible de récupérer les timestamps pour calculer le temps passé")

    def _get_conversation_ids_of_user(self, user_id: int) -> List[int]:
        # 1) CollaborationDAO
        if self.collaboration_dao:
            fn = self._get_callable(self.collaboration_dao, "find_by_user", "get_by_user", "get_collaborations_by_user")
            if fn:
                try:
                    colls: List[Collaboration] = fn(user_id)
                    return list({c.id_conversation for c in colls})
                except Exception:
                    logging.exception("_get_conversation_ids_of_user: collaboration_dao échoue")

        # 2) ConversationDAO
        if self.conversation_dao:
            fn = self._get_callable(self.conversation_dao, "get_conversations_by_user", "get_list_conv")
            if fn:
                try:
                    convs: List[Conversation] = fn(user_id)
                    seen = set()
                    out: List[int] = []
                    for c in convs:
                        cid = c.id_conversation
                        if cid not in seen:
                            seen.add(cid)
                            out.append(cid)
                    return out
                except Exception:
                    logging.exception("_get_conversation_ids_of_user: conversation_dao échoue")

        # 3) MessageDAO fallback (si get_messages_by_user)
        fn_msgs_user = self._get_callable(self.message_dao, "get_messages_by_user", "get_by_user", "get_messages_for_user")
        if fn_msgs_user:
            try:
                msgs: List[Message] = fn_msgs_user(user_id)
                return list({m.id_conversation for m in msgs})
            except Exception:
                logging.exception("_get_conversation_ids_of_user: message_dao.get_messages_by_user échoue")

        return []

    def _compute_sessions_duration(self, timestamps: List[datetime.datetime], *, simple_window: bool = False) -> datetime.timedelta:
        if not timestamps:
            return datetime.timedelta(0)

        if simple_window:
            return timestamps[-1] - timestamps[0]

        total = datetime.timedelta(0)
        session_start: Optional[datetime.datetime] = None
        prev: Optional[datetime.datetime] = None

        for ts in sorted(timestamps):
            if session_start is None:
                session_start = ts
                prev = ts
                continue

            gap = ts - prev  # type: ignore
            if gap <= self.idle_threshold:
                prev = ts
            else:
                total += (prev - session_start)  # type: ignore
                session_start = ts
                prev = ts

        total += (prev - session_start)  # type: ignore
        return total
