from typing import List, Optional, Dict, Set, TYPE_CHECKING
import datetime

# --- Entités métiers (légères) ---
try:
    from ObjetMetier.Message import Message
    from ObjetMetier.Conversation import Conversation
    from ObjetMetier.User import User
except Exception:
    from ObjetMetier.Message import Message  # type: ignore
    from ObjetMetier.Conversation import Conversation  # type: ignore
    from ObjetMetier.User import User  # type: ignore

# --- Types DAO / Services: uniquement pour l'analyse statique ---
if TYPE_CHECKING:
    try:
        from DAO.MessageDAO import MessageDAO
        from DAO.ConversationDAO import ConversationDAO
        from DAO.UserDAO import UserDAO
        from DAO.CollaborationDAO import CollaborationDAO
        from Service.CollaborationService import CollaborationService
        from Service.UserService import UserService
    except Exception:  # type: ignore
        from DAO.MessageDAO import MessageDAO  # type: ignore
        from DAO.ConversationDAO import ConversationDAO  # type: ignore
        from DAO.UserDAO import UserDAO  # type: ignore
        from DAO.CollaborationDAO import CollaborationDAO  # type: ignore
        from Service.CollaborationService import CollaborationService  # type: ignore
        from Service.UserService import UserService  # type: ignore
else:
    from typing import Any as MessageDAO  # type: ignore
    from typing import Any as ConversationDAO  # type: ignore
    from typing import Any as UserDAO  # type: ignore
    from typing import Any as CollaborationDAO  # type: ignore
    from typing import Any as CollaborationService  # type: ignore
    from typing import Any as UserService  # type: ignore


class ExportService:
    """
    Service d'export de conversation (texte/markdown).

    UML:
      - export_conversation(conversation_id: int, user_id: int) -> str
      - format_conversation(conversation: Conversation, messages: List[Message]) -> str

    Par défaut, on produit du Markdown avec :
      - titre, métadonnées (id, date de création),
      - messages triés par date, avec auteur et rôle (agent ou utilisateur).

    Sécurité / Accès:
      - Si CollaborationService/DAO est fourni: l'utilisateur doit être collaborateur (viewer/writer/admin) de la conversation.
      - Sinon, fallback: on autorise si l'utilisateur a écrit au moins un message dans la conversation.
    """

    def __init__(
        self,
        message_dao: MessageDAO,
        conversation_dao: ConversationDAO,
        user_dao: Optional[UserDAO] = None,
        collaboration_dao: Optional[CollaborationDAO] = None,
        collaboration_service: Optional[CollaborationService] = None,
        user_service: Optional[UserService] = None,
        *,
        default_format: str = "markdown",
        time_format: str = "%Y-%m-%d %H:%M",
        include_usernames: bool = True,
    ) -> None:
        self.message_dao = message_dao
        self.conversation_dao = conversation_dao
        self.user_dao = user_dao
        self.collaboration_dao = collaboration_dao
        self.collaboration_service = collaboration_service
        self.user_service = user_service
        self.default_format = default_format
        self.time_format = time_format
        self.include_usernames = include_usernames

    # ------------------------------------------------------------------
    # Helpers (style MessageService)
    # ------------------------------------------------------------------
    def _get_callable(self, obj, *names):
        for n in names:
            fn = getattr(obj, n, None)
            if callable(fn):
                return fn
        return None

    def _validate_id(self, name: str, value: int) -> None:
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} invalide")

    # ------------------------------------------------------------------
    # Contrôle d'accès minimal
    # ------------------------------------------------------------------
    def _check_access(self, user_id: int, conversation_id: int) -> bool:
        # 1) Service de collaboration si dispo (méthodes booléennes usuelles)
        if self.collaboration_service:
            for method in ("is_admin", "is_writer", "is_viewer"):
                fn = getattr(self.collaboration_service, method, None)
                if callable(fn):
                    try:
                        if fn(user_id, conversation_id):
                            return True
                    except Exception:
                        pass

        # 2) CollaborationDAO: l'utilisateur doit avoir une collaboration sur la conv
        if self.collaboration_dao:
            fn = self._get_callable(
                self.collaboration_dao,
                "get_by_user_id",
                "get_collaborations_by_user",
                "read_by_user",
            )
            if fn:
                try:
                    colls = fn(user_id)
                    for c in colls:
                        if int(getattr(c, "id_conversation", -1)) == conversation_id:
                            return True
                except Exception:
                    pass

        # 3) Fallback: autoriser si l'utilisateur a au moins un message dans la conv
        fn_msg = self._get_callable(
            self.message_dao,
            "get_messages_by_conversation_and_user",
            "get_by_conversation_and_user",
        )
        if fn_msg:
            try:
                msgs = fn_msg(conversation_id, user_id)
                return len(msgs) > 0
            except Exception:
                pass

        return False

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------
    def export_conversation(self, conversation_id: int, user_id: int, *, fmt: Optional[str] = None) -> str:
        """
        Exporte une conversation sous forme de chaîne (Markdown par défaut).
        - Valide l'accès utilisateur.
        - Récupère Conversation + Messages triés par date.
        - Injecte les usernames si possible.
        """
        self._validate_id("conversation_id", conversation_id)
        self._validate_id("user_id", user_id)

        effective_fmt = (fmt or self.default_format or "markdown").lower()

        # 1) vérifier accès
        if not self._check_access(user_id, conversation_id):
            raise PermissionError("Accès refusé: l'utilisateur ne peut pas exporter cette conversation")

        # 2) récupérer la conversation
        conv = None
        fn_read_conv = self._get_callable(
            self.conversation_dao,
            "read",
            "get_by_id",
            "get_conversation_by_id",
        )
        if fn_read_conv:
            conv = fn_read_conv(conversation_id)
        if conv is None:
            raise ValueError("Conversation introuvable")

        # 3) récupérer les messages (triés par datetime si possible)
        fn_get_msgs = self._get_callable(
            self.message_dao,
            "get_messages_by_conversation",
            "get_by_conversation",
        )
        if not fn_get_msgs:
            raise RuntimeError("Le DAO des messages ne permet pas de lister les messages d'une conversation")
        messages: List[Message] = list(fn_get_msgs(conversation_id))
        try:
            messages.sort(key=lambda m: m.datetime)
        except Exception:
            pass

        # 4) map user_id -> username si possible
        users_map: Optional[Dict[int, str]] = None
        if self.include_usernames and self.user_dao and messages:
            user_ids: Set[int] = {int(getattr(m, "id_user", 0)) for m in messages}
            users_map = self._build_users_map(user_ids)

        # 5) formatage
        return self.format_conversation(conv, messages, users_map=users_map, fmt=effective_fmt)

    def format_conversation(
        self,
        conversation: Conversation,
        messages: List[Message],
        *,
        users_map: Optional[Dict[int, str]] = None,
        fmt: str = "markdown",
    ) -> str:
        """Formate la conversation et ses messages en chaîne."""
        fmt = (fmt or "markdown").lower()
        if fmt == "plain":
            return self._format_plain(conversation, messages, users_map)
        # défaut: markdown
        return self._format_markdown(conversation, messages, users_map)

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------
    def _build_users_map(self, user_ids: Set[int]) -> Dict[int, str]:
        users_map: Dict[int, str] = {}
        fn_get_user = self._get_callable(self.user_dao, "get_user_by_id", "read") if self.user_dao else None
        if not fn_get_user:
            return users_map
        for uid in user_ids:
            try:
                u: Optional[User] = fn_get_user(uid)
                if u is not None:
                    name = getattr(u, "username", None) or getattr(u, "prenom", None) or f"user_{uid}"
                    users_map[int(uid)] = str(name)
            except Exception:
                continue
        return users_map

    def _format_markdown(
        self,
        conversation: Conversation,
        messages: List[Message],
        users_map: Optional[Dict[int, str]] = None,
    ) -> str:
        titre = getattr(conversation, "titre", None) or f"Conversation #{getattr(conversation, 'id_conversation', '?')}"
        created = getattr(conversation, "created_at", None)
        created_s = created.strftime(self.time_format) if isinstance(created, (datetime.datetime, datetime.date)) else "?"
        conv_id = getattr(conversation, "id_conversation", "?")

        lines: List[str] = []
        lines.append(f"# {titre}")
        lines.append("")
        lines.append(f"**ID**: {conv_id}  ")
        lines.append(f"**Créée le**: {created_s}")
        lines.append("")
        lines.append("---")

        for m in messages:
            ts = getattr(m, "datetime", None)
            ts_s = ts.strftime(self.time_format) if isinstance(ts, (datetime.datetime, datetime.date)) else "?"
            uid = int(getattr(m, "id_user", 0))
            is_agent = bool(getattr(m, "is_from_agent", False))
            role = "agent" if is_agent else "user"
            author = "Agent"
            if not is_agent:
                if users_map and uid in users_map:
                    author = users_map[uid]
                else:
                    author = f"user_{uid}"
            content = str(getattr(m, "message", ""))
            # Chaque message en bloc Markdown
            lines.append(f"**[{ts_s}] {author} ({role})**\n\n{content}\n")
            lines.append("---")

        return "\n".join(lines).rstrip()

    def _format_plain(
        self,
        conversation: Conversation,
        messages: List[Message],
        users_map: Optional[Dict[int, str]] = None,
    ) -> str:
        titre = getattr(conversation, "titre", None) or f"Conversation #{getattr(conversation, 'id_conversation', '?')}"
        created = getattr(conversation, "created_at", None)
        created_s = created.strftime(self.time_format) if isinstance(created, (datetime.datetime, datetime.date)) else "?"
        conv_id = getattr(conversation, "id_conversation", "?")

        lines: List[str] = []
        lines.append(f"{titre}\n")
        lines.append(f"ID: {conv_id}")
        lines.append(f"Créée le: {created_s}")
        lines.append("")

        for m in messages:
            ts = getattr(m, "datetime", None)
            ts_s = ts.strftime(self.time_format) if isinstance(ts, (datetime.datetime, datetime.date)) else "?"
            uid = int(getattr(m, "id_user", 0))
            is_agent = bool(getattr(m, "is_from_agent", False))
            role = "agent" if is_agent else "user"
            author = "Agent"
            if not is_agent:
                if users_map and uid in users_map:
                    author = users_map[uid]
                else:
                    author = f"user_{uid}"
            content = str(getattr(m, "message", ""))
            lines.append(f"[{ts_s}] {author} ({role})\n{content}\n")

        return "\n".join(lines).rstrip()
