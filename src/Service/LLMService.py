# src/Service/LLMService.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime, timezone
import os
from config import AGENT_USER_ID

"""
LLMService (version intégrée)
-----------------------------

Service qui communique DIRECTEMENT avec l'API ENSAI-GPT :

  POST https://ensai-gpt-109912438483.europe-west4.run.app/chat/generate
  Body:
    {
      "messages": [{"role":"system"|"user"|"assistant", "content":"..."}],
      "temperature": 0.7,
      "max_tokens": 512,
      "model": "..."
    }

Réponse attendue:
    {
      "content": "...",
      "usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
    }

Fonctions exposées :
- simple_complete(prompt) -> str
- generate_agent_reply(conversation_id, user_id) -> Message

L'historique COMPLET de la conversation est automatiquement envoyé.
"""

# --- Entités métiers ---
try:
    from ObjetMetier.Message import Message
    from ObjetMetier.Conversation import Conversation
    from ObjetMetier.User import User
except Exception:  # import fallback
    from src.ObjetMetier.Message import Message  # type: ignore
    from src.ObjetMetier.Conversation import Conversation  # type: ignore
    from src.ObjetMetier.User import User  # type: ignore

# --- DAO (typing uniquement) ---
if TYPE_CHECKING:
    try:
        from DAO.MessageDAO import MessageDAO
        from DAO.ConversationDAO import ConversationDAO
        from DAO.UserDAO import UserDAO
    except Exception:
        from src.DAO.MessageDAO import MessageDAO  # type: ignore
        from src.DAO.ConversationDAO import ConversationDAO  # type: ignore
        from src.DAO.UserDAO import UserDAO  # type: ignore
else:
    from typing import Any as MessageDAO  # type: ignore
    from typing import Any as ConversationDAO  # type: ignore
    from typing import Any as UserDAO  # type: ignore


class LLMService:
    """
    Service d'orchestration du LLM avec appel HTTP direct à l'API ENSAI-GPT.
    """

    def __init__(
        self,
        message_dao: MessageDAO,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        requests_session: Optional[Any] = None,
        conversation_dao: Optional[ConversationDAO] = None,
        user_dao: Optional[UserDAO] = None,
        banned_service: Optional[Any] = None,
        default_system_prompt: str = "Tu es un assiastant IA utile.",
        default_temperature: float = 0.7,
        default_max_tokens: int = 512,
        model: Optional[str] = None,
        timeout: float = 20.0,
    ) -> None:
        """
        - base_url: par défaut lit LLM_API_BASE_URL, sinon utilise l'URL ENSAI-GPT fournie.
        - api_key: optionnel (Authorization: Bearer ...)
        - requests_session: optionnel (pour tests/mocks)
        """
        self.message_dao = message_dao
        self.conversation_dao = conversation_dao
        self.user_dao = user_dao
        self.banned_service = banned_service

        self.default_system_prompt = default_system_prompt
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        self.model = model
        self.timeout = timeout

        self.base_url = (
            base_url
            or os.environ.get("LLM_API_BASE_URL")
            or "https://ensai-gpt-109912438483.europe-west4.run.app"
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("LLM_API_KEY")

        try:
            import requests  # noqa: F401
        except Exception as e:
            raise RuntimeError("LLMService requiert 'requests' (pip install requests).") from e

        # session réutilisable (meilleur pour tests et perfs)
        if requests_session is None:
            import requests
            self._session = requests.Session()
        else:
            self._session = requests_session

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _validate_id(self, name: str, value: int) -> None:
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} invalide")

    def _ensure_not_banned(self, stage: str, text: str) -> None:
        if not self.banned_service or not text:
            return
        for name in ("contains_banned", "has_banned", "detect", "validate"):
            fn = getattr(self.banned_service, name, None)
            if callable(fn):
                try:
                    result = fn(text)
                    if isinstance(result, bool) and result:
                        raise ValueError(f"Contenu interdit détecté ({stage})")
                    if isinstance(result, dict) and not result.get("ok", True):
                        raise ValueError(f"Contenu interdit détecté ({stage}): {result.get('reason', '')}")
                except ValueError:
                    raise
                except Exception:
                    pass
                return

    def _http_chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Appelle POST /generate et renvoie un dict {content, usage}."""
        url = f"{self.base_url}/generate"

        payload = {
        "history": messages,  # <-- clé attendue
        "temperature": self.default_temperature if temperature is None else temperature,
        "max_tokens": self.default_max_tokens if max_tokens is None else max_tokens,
        "top_p": 1,  # <-- la doc montre top_p; mets une valeur explicite
        }
        # Ne pas envoyer 'model' si l’API ne l’attend pas; sinon:
        if (model or self.model) is not None:
            payload["model"] = model or self.model

        # supprime les clés None
        #payload = {k: v for k, v in payload.items() if v is not None}

        headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        resp = self._session.post(url, json=payload, headers=headers, timeout=self.timeout)


        # resp.raise_for_status()

        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            body = ""
            try:
                body = resp.text
            except Exception:
                pass
            raise RuntimeError(f"HTTP {resp.status_code} at {url} – {body[:800]}") from e


        data = resp.json() or {}

        content = data.get("content") or data.get("reply") or data.get("text") or ""
        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens", 0)) if isinstance(usage, dict) else 0
        completion_tokens = int(usage.get("completion_tokens", 0)) if isinstance(usage, dict) else 0
        total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))

        return {
            "content": str(content),
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            },
        }

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
    ) -> str:
        """Complétion directe (sans persistance en base)."""
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt vide")

        sys_msg = system_prompt or self.default_system_prompt
        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt},
        ]

        self._ensure_not_banned("input", prompt)
        out = self._http_chat(messages, temperature=temperature, max_tokens=max_tokens, model=model)
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
        extra_context: Optional[str] = None,
    ) -> Message:
        """
        Envoie l’historique COMPLET de la conversation à l’API,
        reçoit la réponse du modèle et la persiste comme message de l’agent.
        """
        self._validate_id("conversation_id", conversation_id)
        self._validate_id("user_id", user_id)

        # 1) Récupérer l'historique complet
        get_msgs = getattr(self.message_dao, "get_messages_by_conversation", None) or getattr(
            self.message_dao, "get_by_conversation", None
        )
        if not callable(get_msgs):
            raise RuntimeError("MessageDAO ne fournit pas get_messages_by_conversation/get_by_conversation")

        history: List[Message] = list(get_msgs(conversation_id))
        try:
            history.sort(key=lambda m: m.datetime)
        except Exception:
            pass

        # 2) Construire le payload messages
        sys_msg = system_prompt or self.default_system_prompt
        messages: List[Dict[str, str]] = [{"role": "system", "content": sys_msg}]

        for m in history:
            role = "assistant" if bool(getattr(m, "is_from_agent", False)) else "user"
            content = str(getattr(m, "message", ""))
            if role == "user":
                uid = int(getattr(m, "id_user", 0))
                content = f"<user id={uid}>\n{content}"
            messages.append({"role": role, "content": content})

        if extra_context:
            messages.append({"role": "system", "content": f"Context:\n{extra_context}"})

        # 3) Filtrage contenu interdit (optionnel)
        for m in messages:
            if m.get("role") in ("user", "system"):
                self._ensure_not_banned("input", m.get("content", ""))

        # 4) Appel HTTP
        out = self._http_chat(messages, temperature=temperature, max_tokens=max_tokens, model=model)
        content = str(out.get("content", ""))
        self._ensure_not_banned("output", content)

        # 5) Persister la réponse agent
        now = datetime.now(timezone.utc)
        msg_obj = Message(
            id_message=None,
            id_conversation=conversation_id,
            id_user=AGENT_USER_ID,  # Utiliser l'ID de l'agent
            datetime=now,
            message=content,
            is_from_agent=True,
        )
        create_fn = getattr(self.message_dao, "create", None) or getattr(self.message_dao, "insert", None)
        if not callable(create_fn):
            raise RuntimeError("MessageDAO ne fournit pas create/insert")
        created = create_fn(msg_obj)
        return created
