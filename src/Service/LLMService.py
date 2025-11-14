# src/Service/LLMService.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime, timezone
import os
# from config import AGENT_USER_ID
AGENT_USER_ID = 6  # Valeur importée de config.py
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
    from ObjetMetier.Message import Message  # type: ignore
    from ObjetMetier.Conversation import Conversation  # type: ignore
    from ObjetMetier.User import User  # type: ignore

# --- DAO (typing uniquement) ---
if TYPE_CHECKING:
    try:
        from DAO.MessageDAO import MessageDAO
        from DAO.ConversationDAO import ConversationDAO
        from DAO.UserDAO import UserDAO
    except Exception:
        from DAO.MessageDAO import MessageDAO  # type: ignore
        from DAO.ConversationDAO import ConversationDAO  # type: ignore
        from DAO.UserDAO import UserDAO  # type: ignore
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
        default_system_prompt: str = "Tu es un assiastant IA utile.", # assistant
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
        """
        Appelle POST /generate et renvoie un dict {content, usage} dans un format unifié.

        On se cale sur l'API ENSAI-GPT qui attend :
          - history: liste de {role, content}
          - éventuellement temperature, max_tokens, model
        """
        import requests  # s'assurer que le nom existe bien dans cette portée

        url = f"{self.base_url}/generate"
        print(f"_http_chat Appel à l'API LLM: {url}")

        # ⚠️ Payload minimal pour éviter les 422 (on ajoute les champs seulement si besoin)
        payload: Dict[str, Any] = {
            "history": messages,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        else:
            payload["temperature"] = self.default_temperature

        if max_tokens is not None:
            # si l'API utilise max_tokens
            payload["max_tokens"] = max_tokens
        else:
            payload["max_tokens"] = self.default_max_tokens

        # Si l'API n'aime pas les champs inconnus, tu peux commenter ou supprimer ça
        # payload["top_p"] = 1

        if model or self.model:
            payload["model"] = model or self.model

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            resp = self._session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout as e:
            # timeout réseau → à toi ensuite de remonter un message propre côté CLI
            raise RuntimeError(f"Timeout ({self.timeout}s) sur {url}") from e
        except requests.exceptions.RequestException as e:
            # autre erreur réseau (DNS, connexion, etc.)
            raise RuntimeError(f"Erreur réseau lors de l'appel à {url}: {e}") from e

        # erreur HTTP (4xx / 5xx) avec message détaillé
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            # on récupère le texte renvoyé par l'API pour debug
            text = resp.text
            raise RuntimeError(
                f"HTTP {resp.status_code} sur {url} – corps de réponse: {text[:800]}"
            ) from e

        # -------------------------
        # Normalisation de la réponse
        # -------------------------
        try:
            data = resp.json() or {}
        except ValueError as e:
            raise RuntimeError(f"Réponse non-JSON depuis {url}: {resp.text[:800]}") from e

        print(f"_http_chat Données brutes: {data}")

        # Plusieurs formats possibles, on essaie dans l'ordre
        content = ""

        # 1) style "simple"
        if isinstance(data, dict) and "content" in data:
            content = str(data.get("content", ""))

        # 2) style "message": {"message": {"role": "...", "content": "..."}}
        elif "message" in data and isinstance(data["message"], dict):
            content = str(data["message"].get("content", ""))

        # 3) style "choices" type OpenAI
        elif "choices" in data and data["choices"]:
            first = data["choices"][0]
            if isinstance(first, dict):
                # OpenAI-style: {"message":{"role":...,"content":...}}
                if "message" in first and isinstance(first["message"], dict):
                    content = str(first["message"].get("content", ""))
                # ou plus simple: {"text": "..."}
                elif "text" in first:
                    content = str(first.get("text", ""))

        # si on n'a toujours rien
        if not content:
            raise RuntimeError(
                f"Impossible de trouver le contenu généré dans la réponse: {data}"
            )

        # usage token, si fourni
        usage_raw = data.get("usage", {}) if isinstance(data, dict) else {}
        usage: Dict[str, int] = {}
        if isinstance(usage_raw, dict):
            # on supporte plusieurs conventions possibles
            prompt_tokens = usage_raw.get("prompt_tokens") or usage_raw.get("input_tokens") or 0
            completion_tokens = usage_raw.get("completion_tokens") or usage_raw.get("output_tokens") or 0
            total_tokens = usage_raw.get("total_tokens") or (prompt_tokens + completion_tokens)

            usage = {
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "total_tokens": int(total_tokens),
            }

        return {
            "content": content,
            "usage": usage,
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
        print(get_msgs) # Debug: afficher la fonction récupérée
        if not callable(get_msgs):
            raise RuntimeError("MessageDAO ne fournit pas get_messages_by_conversation/get_by_conversation")

        history: List[Message] = list(get_msgs(conversation_id))
        print(f"Historique récupéré: {len(history)} messages")  # Debug: afficher le nombre de messages
        try:
            history.sort(key=lambda m: m.datetime)
            print("Historique trié par date")  # Debug: confirmer le tri
        except Exception:
            pass

        # 2) Construire le payload messages
        sys_msg = system_prompt or self.default_system_prompt
        print(f"System prompt utilisé: {sys_msg}")  # Debug: afficher le system prompt
        messages: List[Dict[str, str]] = [{"role": "system", "content": sys_msg}]
        print(f"Ajout de {len(history)} messages à l'historique")  # Debug: afficher le nombre de messages ajoutés

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
        print("Envoi de la requête à l'API LLM...")  # Debug: avant l'appel
        out = self._http_chat(messages, temperature=temperature, max_tokens=max_tokens, model=model)
        print("Réponse reçue de l'API LLM")  # Debug: confirmer la réception
        print(out)
        content = str(out.get("content", ""))
        print(f"Contenu reçu: {content[:100]}...")  # Debug: afficher un extrait du contenu
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
        print(create_fn)  # Debug: afficher la fonction récupérée
        if not callable(create_fn):
            raise RuntimeError("MessageDAO ne fournit pas create/insert")
        created = create_fn(msg_obj)
        return created
