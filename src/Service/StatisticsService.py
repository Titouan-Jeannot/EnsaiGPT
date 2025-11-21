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
        """Initialise le service de statistiques avec les DAO et paramètres nécessaires."""
        self.message_dao = message_dao
        self.conversation_dao = conversation_dao
        self.collaboration_dao = collaboration_dao
        self.user_dao = user_dao
        self.idle_threshold = idle_threshold

    # ------------------------------------------------------------
    #                       UTILITAIRES
    # ------------------------------------------------------------
    def _get_callable(self, obj, *names):
        """Recherche et retourne la première méthode callable parmi les noms donnés dans l'objet."""
        for n in names:
            fn = getattr(obj, n, None)
            if callable(fn):
                return fn
        return None

    def _validate_id(self, name: str, value: int) -> None:
        """Valide qu'un identifiant est un entier positif."""
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} invalide")

    # ------------------------------------------------------------
    #                    NOMBRE DE CONVERSATIONS
    def nb_conv(self, user_id: int) -> int:
        """
        Calcule le nombre de conversations ACTIVES distinctes auxquelles un utilisateur a
        participe, en utilisant les DAO disponibles.
        """
        self._validate_id("user_id", user_id)

        # 1) CollaborationDAO : m??thodes de comptage pr??f??r??es
        if self.collaboration_dao:
            for name in ("count_conversations_by_user", "count_by_user", "count_conv_by_user"):
                fn = getattr(self.collaboration_dao, name, None)
                if callable(fn):
                    try:
                        return int(fn(user_id))
                    except Exception:
                        logging.exception('Nombre de converation : Erreur en utilisant CollaborationDAO')
            # fallback : r??cup??rer les collaborations et d??duire les conversations uniques
            for name in ("get_by_user_id", "find_by_user", "get_collaborations_by_user", "read_by_user"):
                fn = getattr(self.collaboration_dao, name, None)
                if callable(fn):
                    colls = fn(user_id)
                    try:
                        return len({c.id_conversation for c in colls})
                    except Exception:
                        logging.exception('Nombre de converation : Erreur en utilisant CollaborationDAO')

        # 2) Fallback via MessageDAO
        for name in ("get_messages_by_user", "get_by_user", "get_messages_for_user"):
            fn = getattr(self.message_dao, name, None)
            if callable(fn):
                msgs = fn(user_id)
                return len({getattr(m, 'id_conversation', None) for m in msgs})

        # 3) Plus aucune m??thode disponible
        raise RuntimeError('Impossible de calculer nb_conv : aucune m??thode compatible')

    def nb_messages(self, user_id: int) -> int:
        """
        Calcule le nombre de messages envoy??s par un utilisateur, en utilisant les DAO disponibles.
        """
        self._validate_id('user_id', user_id)

        # 1) DAO direct count
        for name in ('count_messages_by_user', 'count_by_user'):
            fn = getattr(self.message_dao, name, None)
            if callable(fn):
                try:
                    return int(fn(user_id))
                except Exception:
                    logging.exception('nb_messages: ??chec m??thode %s', name)

        # 2) Fallback via listings
        for name in ('get_messages_by_user', 'get_by_user', 'get_messages_for_user'):
            fn = getattr(self.message_dao, name, None)
            if callable(fn):
                msgs = fn(user_id)
                return len(msgs or [])

        # 3) Plus aucune m??thode disponible
        raise RuntimeError('Impossible de calculer nb_messages : aucune m??thode compatible')


    def average_message_length(self, user_id: Optional[int] = None) -> float:
        # Longueur moyenne des messages (scop??e utilisateur ou globale)
        if user_id is not None:
            getter = getattr(self.message_dao, "get_messages_by_user", None)
            if getter:
                try:
                    msgs: List[Message] = getter(user_id)
                    if not msgs:
                        return 0.0
                    total = sum(len(str(getattr(m, "message", "") or "")) for m in msgs)
                    return round(total / len(msgs))
                except Exception:
                    logging.exception("average_message_length: get_messages_by_user echoue")
            return 0.0

        avg_fn = getattr(self.message_dao, "get_average_message_length", None)
        if callable(avg_fn):
            try:
                return float(avg_fn())
            except Exception:
                logging.exception("average_message_length: get_average_message_length echoue")

        for name in ("get_all_messages_minimal", "get_all_messages", "get_all"):
            fn = getattr(self.message_dao, name, None)
            if callable(fn):
                msgs = fn()
                if not msgs:
                    return 0.0
                try:
                    total = sum(len(str(getattr(m, "message", "") or "")) for m in msgs)
                    return round(total / len(msgs))
                except Exception:
                    logging.exception("average_message_length: fallback echoue")
                    break

        return 0.0


    def nb_message_conv(self, conversation_id: int) -> int:
        """
        Calcule le nombre de messages dans une conversation donn??e, en utilisant les DAO disponibles.
        """
        self._validate_id('conversation_id', conversation_id)

        for name in ('count_messages_by_conversation', 'count_by_conversation'):
            fn = getattr(self.message_dao, name, None)
            if callable(fn):
                try:
                    return int(fn(conversation_id))
                except Exception:
                    logging.exception('nb_message_conv: ??chec m??thode %s', name)

        for name in ('get_messages_by_conversation', 'get_by_conversation'):
            fn = getattr(self.message_dao, name, None)
            if callable(fn):
                msgs = fn(conversation_id)
                return len(msgs or [])

        raise RuntimeError('Impossible de calculer nb_message_conv : aucune m??thode compatible')


    def nb_messages_de_user_par_conv(self, user_id: int, conversation_id: int) -> int:
        """
        Calcule le nombre de messages envoy??s par un utilisateur dans une conversation donn??e,
        en utilisant les DAO disponibles.
        """
        self._validate_id('user_id', user_id)
        self._validate_id('conversation_id', conversation_id)

        for name in ('count_messages_user_in_conversation', 'count_by_user_in_conversation', 'count_messages_by_user_in_conversation'):
            fn = getattr(self.message_dao, name, None)
            if callable(fn):
                try:
                    return int(fn(user_id, conversation_id))
                except Exception:
                    logging.exception('nb_messages_de_user_par_conv: count direct ??choue')

        for name in ('get_messages_by_conversation_and_user', 'get_by_conversation_and_user'):
            fn = getattr(self.message_dao, name, None)
            if callable(fn):
                msgs = fn(conversation_id, user_id)
                return len(msgs or [])

        for name in ('get_messages_by_conversation', 'get_by_conversation'):
            fn = getattr(self.message_dao, name, None)
            if callable(fn):
                msgs = fn(conversation_id)
                return sum(1 for m in msgs or [] if getattr(m, 'id_user', None) == user_id)

        raise RuntimeError('Impossible de calculer nb_messages_de_user_par_conv : aucune m??thode compatible')


    def count_collaborators_by_conv(self, conversation_id: int) -> int:
        """
        Calcule le nombre de collaborateurs dans une conversation donnée, en utilisant les DAO disponibles.
        """
        self._validate_id("conversation_id", conversation_id)

        if self.collaboration_dao:
            fn = self.collaboration_dao.count_by_conversation
            if callable(fn):
                try:
                    return int(fn(conversation_id))
                except Exception:
                    logging.exception("count_collaborators_by_conv: échec méthode count_collaborators_by_conversation")
        return 0

    def _compute_active_time(self, timestamps, simple_window: bool = False):
        if not timestamps or len(timestamps) < 2:
            return datetime.timedelta(0)
        timestamps = list(timestamps)
        if simple_window:
            return timestamps[-1] - timestamps[0]
        total = datetime.timedelta(0)
        session_start = timestamps[0]
        for prev, cur in zip(timestamps, timestamps[1:]):
            if cur - prev <= self.idle_threshold:
                continue
            total += prev - session_start
            session_start = cur
        total += timestamps[-1] - session_start
        return total

    def temps_passe(self, user_id: int, simple_window: bool = False):
        if simple_window:
            ts = self._get_sorted_timestamps_for_user(user_id)
            return self._compute_active_time(ts, simple_window=True)
        conv_ids = []
        if getattr(self, "_get_conversation_ids_of_user", None):
            try:
                conv_ids = self._get_conversation_ids_of_user(user_id) or []
            except Exception:
                conv_ids = []
        total = datetime.timedelta(0)
        if conv_ids:
            for cid in conv_ids:
                ts = self._get_sorted_timestamps_for_user_in_conv(user_id, cid)
                total += self._compute_active_time(ts, simple_window=False)
        else:
            ts = self._get_sorted_timestamps_for_user(user_id)
            total = self._compute_active_time(ts, simple_window=False)
        return total

    def temps_passe_par_conv(self, user_id: int, conversation_id: int, simple_window: bool = False):
        ts = self._get_sorted_timestamps_for_user_in_conv(user_id, conversation_id)
        return self._compute_active_time(ts, simple_window=simple_window)


    def top_active_users(self, limit: int = 5) -> List[tuple]:
        if limit <= 0:
            raise ValueError("limit doit etre > 0")

        def _normalize(entries):
            norm = []
            for e in entries or []:
                if isinstance(e, dict):
                    uid = e.get("user_id")
                    count = e.get("count")
                elif isinstance(e, (list, tuple)) and len(e) >= 2:
                    uid, count = e[0], e[1]
                else:
                    continue
                try:
                    uid_int = int(uid)
                    count_int = int(count)
                except Exception:
                    continue
                norm.append((uid_int, count_int))
            return norm

        direct_fn = getattr(self.message_dao, "get_top_users_by_message_count", None) or getattr(self.message_dao, "top_users", None)
        if callable(direct_fn):
            try:
                return _normalize(direct_fn(limit))[:limit]
            except Exception:
                logging.exception("top_active_users: direct DAO echoue")

        for name in ("get_all_messages_minimal", "get_all_messages", "get_all"):
            fn = getattr(self.message_dao, name, None)
            if callable(fn):
                try:
                    msgs = fn()
                    counts = {}
                    for m in msgs or []:
                        uid = getattr(m, "id_user", None)
                        if uid is None:
                            continue
                        uid_int = int(uid)
                        counts[uid_int] = counts.get(uid_int, 0) + 1
                    ordered = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                    return ordered[:limit]
                except Exception:
                    logging.exception("top_active_users: fallback echoue")
                    break

        raise RuntimeError("Aucune methode compatible pour top_active_users")
    def _get_sorted_timestamps_for_user(self, user_id: int):
        getter = None
        for name in ("get_messages_by_user", "get_by_user", "get_messages_for_user"):
            fn = getattr(self.message_dao, name, None)
            if callable(fn):
                getter = fn
                break
        if not getter:
            return []
        msgs = getter(user_id) or []
        ts = [m.datetime for m in msgs if hasattr(m, "datetime")]
        ts = [t for t in ts if isinstance(t, datetime.datetime)]
        ts.sort()
        return ts

    def _get_sorted_timestamps_for_user_in_conv(self, user_id: int, conversation_id: int):
        getter = None
        for name in ("get_messages_by_conversation_and_user", "get_by_conversation_and_user"):
            fn = getattr(self.message_dao, name, None)
            if callable(fn):
                getter = lambda cid, uid, f=fn: f(cid, uid)
                break
        if getter is None:
            for name in ("get_messages_by_conversation", "get_by_conversation"):
                fn = getattr(self.message_dao, name, None)
                if callable(fn):
                    getter = lambda cid, uid, f=fn: [m for m in (f(cid) or []) if getattr(m, "id_user", None) == uid]
                    break
        if getter is None:
            return []
        msgs = getter(conversation_id, user_id) or []
        ts = [m.datetime for m in msgs if hasattr(m, "datetime")]
        ts = [t for t in ts if isinstance(t, datetime.datetime)]
        ts.sort()
        return ts

    def _get_conversation_ids_of_user(self, user_id: int):
        if self.conversation_dao and hasattr(self.conversation_dao, "get_list_conv"):
            try:
                convs = self.conversation_dao.get_list_conv(user_id) or []
                return list({getattr(c, "id_conversation", None) for c in convs if getattr(c, "id_conversation", None) is not None})
            except Exception:
                pass
        getter = getattr(self.message_dao, "get_messages_by_user", None)
        if getter:
            msgs = getter(user_id) or []
            return list({getattr(m, "id_conversation", None) for m in msgs if getattr(m, "id_conversation", None) is not None})
        return []
