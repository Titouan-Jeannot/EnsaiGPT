from typing import List, Optional, Dict, Tuple, TYPE_CHECKING
import datetime

# Entités métiers (légères)
try:
    from ObjetMetier.Message import Message
    from ObjetMetier.Conversation import Conversation
    from ObjetMetier.User import User
    from ObjetMetier.Collaboration import Collaboration
except Exception:
    from src.ObjetMetier.Message import Message  # type: ignore
    from src.ObjetMetier.Conversation import Conversation  # type: ignore
    from src.ObjetMetier.User import User  # type: ignore
    from src.ObjetMetier.Collaboration import Collaboration  # type: ignore

# ⚠️ Ne PAS importer les DAO/Services au runtime (évite dotenv/psycopg2 pendant les tests)
if TYPE_CHECKING:
    try:
        from DAO.MessageDAO import MessageDAO
        from DAO.ConversationDAO import ConversationDAO
        from DAO.CollaborationDAO import CollaborationDAO
        from DAO.UserDAO import UserDAO
        from Service.UserService import UserService
    except Exception:  # type: ignore
        from src.DAO.MessageDAO import MessageDAO  # type: ignore
        from src.DAO.ConversationDAO import ConversationDAO  # type: ignore
        from src.DAO.CollaborationDAO import CollaborationDAO  # type: ignore
        from src.DAO.UserDAO import UserDAO  # type: ignore
        from src.Service.UserService import UserService  # type: ignore
else:
    from typing import Any as MessageDAO  # type: ignore
    from typing import Any as ConversationDAO  # type: ignore
    from typing import Any as CollaborationDAO  # type: ignore
    from typing import Any as UserDAO  # type: ignore
    from typing import Any as UserService  # type: ignore


class StatisticsService:
    """
    Service de statistiques.

    Méthodes (UML) :
      - nb_conv(user_id)
      - temps_passe(user_id)
      - temps_passe_par_conv(user_id, conversation_id)
      - nb_messages(user_id)
      - nb_messages_de_user_par_conv(user_id, conversation_id)
      - nb_message_conv(conversation_id)
      - top_active_users(limit)
      - average_message_length()

    Sessions :
    - Une session continue tant que l'écart entre deux messages successifs
      n'excède pas idle_threshold (10 min par défaut).
    - temps_passe(user_id) = SOMME des durées par conversation (mode par défaut).
      Si simple_window=True : fenêtre GLOBALE (du 1er au dernier message, toutes conv confondues).
    """

    def __init__(
        self,
        message_dao: MessageDAO,
        conversation_dao: Optional[ConversationDAO] = None,
        collaboration_dao: Optional[CollaborationDAO] = None,
        user_dao: Optional[UserDAO] = None,
        user_service: Optional[UserService] = None,
        idle_threshold: datetime.timedelta = datetime.timedelta(minutes=10),
    ):
        self.message_dao = message_dao
        self.conversation_dao = conversation_dao
        self.collaboration_dao = collaboration_dao
        self.user_dao = user_dao
        self.user_service = user_service
        self.idle_threshold = idle_threshold

    # ------------------------------- Helpers -------------------------------
    def _get_callable(self, obj, *names):
        for n in names:
            fn = getattr(obj, n, None)
            if callable(fn):
                return fn
        return None

    def _validate_id(self, name: str, value: int) -> None:
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} invalide")

    # ------------------------------- Compteurs ------------------------------
    def nb_conv(self, user_id: int) -> int:
        """Nombre de conversations auxquelles l'utilisateur participe."""
        self._validate_id("user_id", user_id)

        # 1) CollaborationDAO
        if self.collaboration_dao:
            fn = self._get_callable(
                self.collaboration_dao,
                "count_conversations_by_user",
                "count_by_user",
                "count_conv_by_user",
            )
            if fn:
                try:
                    return int(fn(user_id))
                except Exception:
                    pass

            fn_get = self._get_callable(
                self.collaboration_dao,
                "get_by_user_id",
                "get_collaborations_by_user",
                "read_by_user",
            )
            if fn_get:
                try:
                    colls: List[Collaboration] = fn_get(user_id)
                    return len({c.id_conversation for c in colls})
                except Exception:
                    pass

        # 2) Fallback: via messages
        fn_msgs_user = self._get_callable(
            self.message_dao,
            "get_messages_by_user",
            "get_by_user",
            "get_messages_for_user",
        )
        if fn_msgs_user:
            try:
                msgs: List[Message] = fn_msgs_user(user_id)
                return len({m.id_conversation for m in msgs})
            except Exception:
                pass

        raise RuntimeError("Impossible de calculer nb_conv avec les DAO fournis")

    def nb_messages(self, user_id: int) -> int:
        """Nombre total de messages envoyés par l'utilisateur (toutes conversations)."""
        self._validate_id("user_id", user_id)

        fn = self._get_callable(self.message_dao, "count_messages_by_user", "count_by_user")
        if fn:
            return int(fn(user_id))

        fn_get = self._get_callable(
            self.message_dao,
            "get_messages_by_user",
            "get_by_user",
            "get_messages_for_user",
        )
        if fn_get:
            msgs: List[Message] = fn_get(user_id)
            return len(msgs)

        raise RuntimeError("Aucune méthode DAO pour compter les messages d'un utilisateur")

    def nb_message_conv(self, conversation_id: int) -> int:
        """Nombre total de messages dans une conversation."""
        self._validate_id("conversation_id", conversation_id)

        fn = self._get_callable(self.message_dao, "count_messages_by_conversation", "count_by_conversation")
        if fn:
            return int(fn(conversation_id))

        fn_get = self._get_callable(self.message_dao, "get_messages_by_conversation", "get_by_conversation")
        if fn_get:
            msgs: List[Message] = fn_get(conversation_id)
            return len(msgs)

        raise RuntimeError("Aucune méthode DAO pour compter les messages d'une conversation")

    def nb_messages_de_user_par_conv(self, user_id: int, conversation_id: int) -> int:
        """Nombre de messages d'un utilisateur dans une conversation donnée."""
        self._validate_id("user_id", user_id)
        self._validate_id("conversation_id", conversation_id)

        fn = self._get_callable(
            self.message_dao,
            "count_messages_user_in_conversation",
            "count_by_user_in_conversation",
        )
        if fn:
            return int(fn(user_id, conversation_id))

        fn_get_user_conv = self._get_callable(
            self.message_dao,
            "get_messages_by_conversation_and_user",
            "get_by_conversation_and_user",
        )
        if fn_get_user_conv:
            msgs: List[Message] = fn_get_user_conv(conversation_id, user_id)
            return len(msgs)

        fn_get_conv = self._get_callable(self.message_dao, "get_messages_by_conversation", "get_by_conversation")
        if fn_get_conv:
            msgs: List[Message] = fn_get_conv(conversation_id)
            return sum(1 for m in msgs if int(getattr(m, "id_user", -1)) == user_id)

        raise RuntimeError("Aucune méthode DAO compatible pour nb_messages_de_user_par_conv")

    # ------------------------ Temps passé (sessions) ------------------------
    def temps_passe(self, user_id: int, *, simple_window: bool = False) -> datetime.timedelta:
        """
        Temps total passé par l'utilisateur.
        - Mode sessions (par défaut) : SOMME des durées par conversation.
        - Mode simple_window=True : fenêtre GLOBALE (du 1er au dernier message, toutes conv confondues).
        """
        self._validate_id("user_id", user_id)

        # simple_window => global
        if simple_window:
            timestamps = self._get_sorted_timestamps_for_user(user_id)
            return self._compute_sessions_duration(timestamps, simple_window=True)

        # sessions par conversation
        total = datetime.timedelta(0)
        conv_ids = self._get_conversation_ids_of_user(user_id)

        # Fallback si aucune conv détectée
        if not conv_ids:
            timestamps = self._get_sorted_timestamps_for_user(user_id)
            return self._compute_sessions_duration(timestamps, simple_window=False)

        for cid in conv_ids:
            ts = self._get_sorted_timestamps_for_user_in_conv(user_id, cid)
            total += self._compute_sessions_duration(ts, simple_window=False)

        return total

    def temps_passe_par_conv(
        self, user_id: int, conversation_id: int, *, simple_window: bool = False
    ) -> datetime.timedelta:
        """Temps total passé par l'utilisateur dans une conversation donnée."""
        self._validate_id("user_id", user_id)
        self._validate_id("conversation_id", conversation_id)
        timestamps = self._get_sorted_timestamps_for_user_in_conv(user_id, conversation_id)
        return self._compute_sessions_duration(timestamps, simple_window=simple_window)

    # ------------------------------- Agrégats -------------------------------
    def top_active_users(self, limit: int = 10) -> List[Tuple[int, int]]:
        """Retourne [(user_id, nb_messages)] trié décroissant."""
        if limit <= 0:
            raise ValueError("limit doit être > 0")

        fn = self._get_callable(self.message_dao, "get_top_users_by_message_count", "top_users")
        if fn:
            rows = fn(limit)
            norm: List[Tuple[int, int]] = []
            for r in rows:
                if isinstance(r, tuple) and len(r) >= 2:
                    norm.append((int(r[0]), int(r[1])))
                elif isinstance(r, dict) and {"user_id", "count"} <= set(r.keys()):
                    norm.append((int(r["user_id"]), int(r["count"])))
            return norm

        fn_all = self._get_callable(self.message_dao, "get_all_messages_minimal", "get_all_messages", "get_all")
        if fn_all:
            msgs: List[Message] = fn_all()
            counts: Dict[int, int] = {}
            for m in msgs:
                uid = int(getattr(m, "id_user", 0))
                counts[uid] = counts.get(uid, 0) + 1
            result = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
            return [(int(uid), int(c)) for uid, c in result]

        raise RuntimeError("Aucune méthode DAO compatible pour top_active_users")

    def average_message_length(self) -> float:
        """Longueur moyenne des messages en caractères."""
        fn = self._get_callable(self.message_dao, "get_average_message_length", "avg_message_length")
        if fn:
            try:
                return float(fn())
            except Exception:
                pass

        fn_all = self._get_callable(self.message_dao, "get_all_messages_minimal", "get_all_messages", "get_all")
        if fn_all:
            msgs: List[Message] = fn_all()
            if not msgs:
                return 0.0
            total = sum(len(str(getattr(m, "message", "") or "")) for m in msgs)
            return total / len(msgs)

        raise RuntimeError("Aucune méthode DAO compatible pour average_message_length")

    # ------------------------- Implémentation interne -----------------------
    def _get_sorted_timestamps_for_user(self, user_id: int) -> List[datetime.datetime]:
        fn = self._get_callable(self.message_dao, "get_messages_by_user", "get_by_user", "get_messages_for_user")
        if fn:
            msgs: List[Message] = fn(user_id)
            return sorted(
                [m.datetime for m in msgs if hasattr(m, "datetime") and m.datetime],
                key=lambda t: t,
            )

        conv_ids = self._get_conversation_ids_of_user(user_id)
        timestamps: List[datetime.datetime] = []
        for cid in conv_ids:
            ts = self._get_sorted_timestamps_for_user_in_conv(user_id, cid)
            timestamps.extend(ts)
        return sorted(timestamps, key=lambda t: t)

    def _get_sorted_timestamps_for_user_in_conv(
        self, user_id: int, conversation_id: int
    ) -> List[datetime.datetime]:
        fn = self._get_callable(
            self.message_dao,
            "get_messages_by_conversation_and_user",
            "get_by_conversation_and_user",
        )
        if fn:
            msgs: List[Message] = fn(conversation_id, user_id)
            return sorted(
                [m.datetime for m in msgs if hasattr(m, "datetime") and m.datetime],
                key=lambda t: t,
            )

        fn_conv = self._get_callable(self.message_dao, "get_messages_by_conversation", "get_by_conversation")
        if fn_conv:
            msgs: List[Message] = fn_conv(conversation_id)
            return sorted(
                [
                    m.datetime
                    for m in msgs
                    if int(getattr(m, "id_user", -1)) == user_id and getattr(m, "datetime", None)
                ],
                key=lambda t: t,
            )

        raise RuntimeError("Impossible de récupérer les messages pour calculer le temps passé")

    def _get_conversation_ids_of_user(self, user_id: int) -> List[int]:
        if self.collaboration_dao:
            fn = self._get_callable(self.collaboration_dao, "get_by_user_id", "get_collaborations_by_user", "read_by_user")
            if fn:
                colls: List[Collaboration] = fn(user_id)
                return list({c.id_conversation for c in colls})

        if self.conversation_dao:
            fn = self._get_callable(self.conversation_dao, "get_list_conv", "get_conversations_by_user")
            if fn:
                convs: List[Conversation] = fn(user_id)
                return [c.id_conversation for c in convs]

        fn_msgs_user = self._get_callable(self.message_dao, "get_messages_by_user", "get_by_user", "get_messages_for_user")
        if fn_msgs_user:
            msgs: List[Message] = fn_msgs_user(user_id)
            return list({m.id_conversation for m in msgs})

        return []

    def _compute_sessions_duration(
        self,
        timestamps: List[datetime.datetime],
        *,
        simple_window: bool = False,
    ) -> datetime.timedelta:
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
