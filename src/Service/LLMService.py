from typing import List, Optional, Dict, Any, TYPE_CHECKING, Tuple
import datetime

"""
LLMService
----------

Objectif: encapsuler l'appel à un modèle de langage (LLM) de façon découplée
et testable (provider injecté), en restant cohérent avec le style de vos services.

Fonctions principales:
- simple_complete(prompt) -> str : complétion directe.
- generate_agent_reply(conversation_id, user_id, ...) -> Message :
    * construit le contexte (messages récents d'une conversation)
    * appelle le provider LLM
    * persiste la réponse comme message de l'agent (is_from_agent=True)
- summarize_conversation(conversation_id, ...) -> str : résumé de la conversation.
- count_tokens(text) -> int : comptage via provider si disponible (fallback heuristique).

Sécurité:
- possibilité d'injecter un MotsBannisService (ou équivalent) pour filtrer prompt / sortie.

Dépendances DAO/Services:
- MessageDAO pour lire/écrire les messages
- (optionnel) ConversationDAO, UserDAO
- (optionnel) MotsBannisService-like (nom libre), via duck typing

Aucune dépendance réseau au runtime dans ce module: le provider est injecté
par l'appelant (il peut être un Fake en tests, un vrai client OpenAI/HF en prod).
"""

# --- Entités métiers (légères) ---
try:
    from ObjetMetier.Message import Message
    from ObjetMetier.Conversation import Conversation
    from ObjetMetier.User import User
except Exception:
    from src.ObjetMetier.Message import Message  # type: ignore
    from src.ObjetMetier.Conversation import Conversation  # type: ignore
    from src.ObjetMetier.User import User  # type: ignore

# --- Types DAO / Services uniquement pour l'analyse statique ---
if TYPE_CHECKING:
    try:
        from DAO.MessageDAO import MessageDAO
        from DAO.ConversationDAO import ConversationDAO
        from DAO.UserDAO import UserDAO
    except Exception:  # type: ignore
        from src.DAO.MessageDAO import MessageDAO  # type: ignore
        from src.DAO.ConversationDAO import ConversationDAO  # type: ignore
        from src.DAO.UserDAO import UserDAO  # type: ignore
else:
    from typing import Any as MessageDAO  # type: ignore
    from typing import Any as ConversationDAO  # type: ignore
    from typing import Any as UserDAO  # type: ignore


class LLMService:
    """
    Service d'orchestration LLM (provider-injected, testable, sans dépendances lourdes).

    Provider attendu (duck typing):
        - chat(messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]
            retourne au minimum {"content": str, "usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}}
        - (optionnel) count_tokens(text: str) -> int

    Exemples de messages pour provider.chat:
        [{"role": "system", "content": "..."},
         {"role": "user",   "content": "..."},
         {"role": "assistant", "content": "..."}]
    """

    def __init__(
        self,
        message_dao: MessageDAO,
        provider: Any,
        conversation_dao: Optional[ConversationDAO] = None,
        user_dao: Optional[UserDAO] = None,
        banned_service: Optional[Any] = None,
        *,
        default_system_prompt: str = "You are a helpful assistant.",
        max_history_messages: int = 20,
        default_temperature: float = 0.7,
        default_max_tokens: int = 512,
        model: Optional[str] = None,
    ) -> None:
        self.message_dao = message_dao
        self.provider = provider
        self.conversation_dao = conversation_dao
        self.user_dao = user_dao
        self.banned_service = banned_service
        self.default_system_prompt = default_system_prompt
        self.max_history_messages = max_history_messages
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        self.model = model

    # ------------------------------------------------------------------
    # Helpers (style commun)
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
    # Public API
    # ------------------------------------------------------------------
    def simple_complete(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        extra_messages: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Complétion directe (pas de persistance en base)."""
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt vide")
        sys_msg = system_prompt or self.default_system_prompt
        msgs: List[Dict[str, str]] = [{"role": "system", "content": sys_msg}]
        if extra_messages:
            msgs.extend(extra_messages)
        msgs.append({"role": "user", "content": prompt})

        self._ensure_not_banned("input", prompt)
        out = self._provider_chat(
            msgs,
            temperature=temperature if temperature is not None else self.default_temperature,
            max_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
            model=model or self.model,
        )
        content = str(out.get("content", ""))
        self._ensure_not_banned("output", content)
        return content

    def generate_agent_reply(
        self,
        conversation_id: int,
        user_id: int,
        *,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        include_last_n: Optional[int] = None,
        extra_context: Optional[str] = None,
    ) -> Message:
        """
        Construit un contexte de conversation, appelle le LLM, puis persiste
        la réponse comme message d'agent (is_from_agent=True).
        Retourne l'objet Message créé.
        """
        self._validate_id("conversation_id", conversation_id)
        self._validate_id("user_id", user_id)

        # 1) Récupérer l'historique
        get_msgs = self._get_callable(self.message_dao, "get_messages_by_conversation", "get_by_conversation")
        if not get_msgs:
            raise RuntimeError("MessageDAO ne fournit pas get_messages_by_conversation")
        history: List[Message] = list(get_msgs(conversation_id))
        try:
            history.sort(key=lambda m: m.datetime)
        except Exception:
            pass

        # 2) Construire le prompt
        sys_msg = system_prompt or self.default_system_prompt
        take_n = include_last_n if include_last_n is not None else self.max_history_messages
        selected = history[-take_n:] if take_n > 0 else history
        msgs: List[Dict[str, str]] = [{"role": "system", "content": sys_msg}]

        for m in selected:
            role = "assistant" if bool(getattr(m, "is_from_agent", False)) else "user"
            content = str(getattr(m, "message", ""))
            # Si on veut différencier chaque utilisateur, on peut préfixer (optionnel)
            if role == "user":
                uid = int(getattr(m, "id_user", 0))
                content = f"<user id={uid}>\n{content}"
            msgs.append({"role": role, "content": content})

        if extra_context:
            msgs.append({"role": "system", "content": f"Context:\n{extra_context}"})

        # 3) Vérifier contenu interdit dans l'entrée
        for m in msgs:
            if m.get("role") in ("user", "system"):
                self._ensure_not_banned("input", m.get("content", ""))

        # 4) Appel provider
        out = self._provider_chat(
            msgs,
            temperature=temperature if temperature is not None else self.default_temperature,
            max_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
            model=model or self.model,
        )
        content = str(out.get("content", ""))
        self._ensure_not_banned("output", content)

        # 5) Persister comme message d'agent
        now = datetime.datetime.now()
        msg_obj = Message(
            id_message=None,
            id_conversation=conversation_id,
            id_user=0,  # 0 = agent
            datetime=now,
            message=content,
            is_from_agent=True,
        )
        create_fn = self._get_callable(self.message_dao, "create", "insert", "add")
        if not create_fn:
            raise RuntimeError("MessageDAO ne fournit pas de méthode create/insert/add")
        created = create_fn(msg_obj)
        return created

    def summarize_conversation(
        self,
        conversation_id: int,
        *,
        max_tokens: Optional[int] = None,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
        include_last_n: Optional[int] = None,
        model: Optional[str] = None,
        bullet_points: bool = True,
    ) -> str:
        """Produit un résumé de la conversation (en chaîne, pas de persistance)."""
        self._validate_id("conversation_id", conversation_id)
        get_msgs = self._get_callable(self.message_dao, "get_messages_by_conversation", "get_by_conversation")
        if not get_msgs:
            raise RuntimeError("MessageDAO ne fournit pas get_messages_by_conversation")
        history: List[Message] = list(get_msgs(conversation_id))
        try:
            history.sort(key=lambda m: m.datetime)
        except Exception:
            pass
        take_n = include_last_n if include_last_n is not None else self.max_history_messages
        selected = history[-take_n:] if take_n > 0 else history

        sys_msg = system_prompt or "Tu es un assistant qui résume brièvement et fidèlement les échanges."
        style = "\n- Utilise des puces concises." if bullet_points else ""
        user_prompt_lines = [
            "Résume la conversation ci-dessous. Sois factuel, bref et couvre les points clés.",
            style,
            "\nConversation:\n",
        ]
        for m in selected:
            role = "Agent" if bool(getattr(m, "is_from_agent", False)) else f"User#{int(getattr(m, 'id_user', 0))}"
            dt = getattr(m, "datetime", None)
            dt_s = dt.isoformat(sep=" ") if isinstance(dt, (datetime.datetime, datetime.date)) else "?"
            content = str(getattr(m, "message", ""))
            user_prompt_lines.append(f"[{dt_s}] {role}: {content}")
        prompt = "\n".join([ln for ln in user_prompt_lines if ln])

        self._ensure_not_banned("input", prompt)
        out = self._provider_chat(
            [{"role": "system", "content": sys_msg}, {"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
            model=model or self.model,
        )
        content = str(out.get("content", ""))
        self._ensure_not_banned("output", content)
        return content

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def count_tokens(self, text: str) -> int:
        if hasattr(self.provider, "count_tokens") and callable(getattr(self.provider, "count_tokens")):
            try:
                return int(self.provider.count_tokens(text))
            except Exception:
                pass
        # Heuristique simple: ~ 1 token ≈ 4 chars (langue dépendante)
        return max(1, (len(text) + 3) // 4)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _provider_chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        chat = getattr(self.provider, "chat", None)
        if not callable(chat):
            raise RuntimeError("Le provider LLM ne définit pas 'chat(messages, **kwargs)'.")
        out = chat(messages, **{k: v for k, v in kwargs.items() if v is not None})
        if not isinstance(out, dict) or "content" not in out:
            raise RuntimeError("Réponse provider invalide: dict avec clé 'content' attendu")
        return out

    def _ensure_not_banned(self, stage: str, text: str) -> None:
        if not self.banned_service or not text:
            return
        # On accepte différentes API via duck typing
        for name in ("contains_banned", "has_banned", "detect", "validate"):
            fn = getattr(self.banned_service, name, None)
            if callable(fn):
                try:
                    result = fn(text)
                    if isinstance(result, bool) and result:
                        raise ValueError(f"Contenu interdit détecté ({stage})")
                    # Autres variantes: {ok: bool, reason: str}
                    if isinstance(result, dict) and not result.get("ok", True):
                        raise ValueError(f"Contenu interdit détecté ({stage}): {result.get('reason', '')}")
                except ValueError:
                    raise
                except Exception:
                    # en cas d'erreur du service, on n'empêche pas l'appel mais on continue
                    pass
                return
        # si le service ne fournit pas d'API reconnue → on ignore silencieusement
        return
