from __future__ import annotations

from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime, timezone
import os
import requests

AGENT_USER_ID = 6  # ID de l'agent en base


# === Imports métier ===
try:
    from ObjetMetier.Message import Message
    from ObjetMetier.Conversation import Conversation
    from ObjetMetier.User import User
except Exception:  # import fallback
    from ObjetMetier.Message import Message  # type: ignore
    from ObjetMetier.Conversation import Conversation  # type: ignore
    from ObjetMetier.User import User  # type: ignore

# === Imports DAO pour les types ===
if TYPE_CHECKING:
    try:
        from src.DAO.MessageDAO import MessageDAO
        from src.DAO.ConversationDAO import ConversationDAO
        from src.DAO.UserDAO import UserDAO
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
    Service simple qui communique avec l'API ENSAI-GPT.

    POST https://ensai-gpt-109912438483.europe-west4.run.app/generate

    Body:
    {
      "history": [
        {"role": "system"|"user"|"assistant", "content": "..."},
        ...
      ],
      "max_tokens": 150,
      "temperature": 0.7,
      "top_p": 1
    }

    Réponse (extrait) :
    {
      "choices": [
        {
          "message": {
            "role": "assistant",
            "content": "..."
          }
        }
      ],
      "usage": {...}
    }
    """

    def __init__(
        self,
        message_dao: "MessageDAO",
        *,
        base_url: Optional[str] = None,
        conversation_dao: Optional["ConversationDAO"] = None,
        user_dao: Optional["UserDAO"] = None,
        banned_service: Optional[Any] = None,
        default_system_prompt: str = "Tu es un assistant IA utile.",
        default_temperature: float = 0.7,
        default_max_tokens: int = 512,
        timeout: float = 20.0,
    ) -> None:
        self.message_dao = message_dao
        self.conversation_dao = conversation_dao
        self.user_dao = user_dao
        self.banned_service = banned_service

        self.default_system_prompt = default_system_prompt
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        self.timeout = timeout

        # base_url = racine de l’API, on ajoute /generate ensuite
        self.base_url = (
            base_url
            or os.environ.get("LLM_API_BASE_URL")
            or "https://ensai-gpt-109912438483.europe-west4.run.app"
        ).rstrip("/")



    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _validate_id(self, name: str, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} invalide: {value}")

    def _ensure_not_banned(self, stage: str, text: str) -> None:
        """
        Vérification très simple via banned_service si fourni.
        Ne change rien au payload, juste lève une erreur si contenu interdit.
        """
        if not self.banned_service or not text:
            return

        for attr in ("contains_banned", "has_banned", "detect", "validate"):
            fn = getattr(self.banned_service, attr, None)
            if callable(fn):
                try:
                    res = fn(text)
                    # bool simple
                    if isinstance(res, bool) and res:
                        raise ValueError(f"Contenu interdit détecté ({stage})")
                    # dict style {"ok": False, "reason": "..."}
                    if isinstance(res, dict) and not res.get("ok", True):
                        raise ValueError(
                            f"Contenu interdit détecté ({stage}): {res.get('reason', '')}"
                        )
                except ValueError:
                    raise
                except Exception:
                    # on n'interrompt pas si erreur interne du banned_service
                    pass
                return

    def _call_llm(
        self,
        history: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Appelle POST /generate avec:
        {
          "history": [...],
          "max_tokens": ...,
          "temperature": ...,
          "top_p": 1
        }
        et renvoie un dict {"content": str, "usage": dict}
        """
        url = f"{self.base_url}/generate"
        print(f"[LLMService] Appel API POST {url}")

        payload: Dict[str, Any] = {
            "history": history,
            "max_tokens": max_tokens if max_tokens is not None else self.default_max_tokens,
            "temperature": temperature if temperature is not None else self.default_temperature,
            "top_p": 1,
        }

        print(f"[LLMService] Payload envoyé: {payload}")

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"[LLMService] HTTP ERROR {resp.status_code}: {resp.text}")
            raise RuntimeError(
                f"[LLM] HTTP {resp.status_code} sur {url} – corps: {resp.text[:800]}"
            ) from e
        except requests.exceptions.Timeout as e:
            raise RuntimeError(f"[LLM] Timeout ({self.timeout}s) sur {url}") from e
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"[LLM] Erreur réseau sur {url}: {e}") from e

        try:
            data = resp.json()
        except ValueError as e:
            print(f"[LLMService] Réponse non JSON: {resp.text[:800]}")
            raise RuntimeError(f"[LLM] Réponse non-JSON depuis {url}") from e

        print(f"[LLMService] Réponse brute: {data}")

        # On suit exactement le format de l'exemple:
        # data["choices"][0]["message"]["content"]
        try:
            first_choice = data["choices"][0]
            message = first_choice["message"]
            content = str(message.get("content", ""))
        except Exception as e:
            raise RuntimeError(
                f"[LLM] Format de réponse inattendu, impossible de lire choices[0].message.content: {data}"
            ) from e

        usage_raw = data.get("usage", {}) if isinstance(data, dict) else {}
        usage: Dict[str, int] = {}
        if isinstance(usage_raw, dict):
            usage = {
                "prompt_tokens": int(usage_raw.get("prompt_tokens", 0)),
                "completion_tokens": int(usage_raw.get("completion_tokens", 0)),
                "total_tokens": int(usage_raw.get("total_tokens", 0)),
            }

        return {
            "content": content,
            "usage": usage,
        }

    def _build_history_for_prompt(
        self,
        user_content: str,
        *,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        sys = system_prompt or self.default_system_prompt
        history = [
            {"role": "system", "content": sys},
            {"role": "user", "content": user_content},
        ]
        print(f"[LLMService] History pour simple_complete: {history}")
        return history

    def _build_history_for_conversation(
        self,
        conversation_id: int,
        *,
        system_prompt: Optional[str] = None,
        extra_context: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Construit le history pour l'API à partir des messages en BDD.
        """
        get_msgs = getattr(self.message_dao, "get_messages_by_conversation", None)
        if not callable(get_msgs):
            raise RuntimeError(
                "MessageDAO ne fournit pas get_messages_by_conversation"
            )

        history_messages: List[Message] = list(get_msgs(conversation_id))
        print(f"[LLMService] Historique récupéré: {len(history_messages)} messages")

        # Normalement déjà trié par timestamp dans le DAO, mais on sécurise
        try:
            history_messages.sort(key=lambda m: m.datetime)
        except Exception:
            pass

        sys = system_prompt or self.default_system_prompt
        messages: List[Dict[str, str]] = [{"role": "system", "content": sys}]

        for m in history_messages:
            is_agent = bool(getattr(m, "is_from_agent", False))
            role = "assistant" if is_agent else "user"
            content = str(getattr(m, "message", ""))

            # Option : encoder l'id user (comme tu faisais)
            if role == "user":
                uid = int(getattr(m, "id_user", 0))
                content = f"<user id={uid}>\n{content}"

            messages.append({"role": role, "content": content})

        if extra_context:
            messages.append(
                {"role": "system", "content": f"Contexte additionnel:\n{extra_context}"}
            )

        print(f"[LLMService] History complet envoyé à l'API ({len(messages)} messages)")
        return messages

    # ------------------------------------------------------------------
    # Méthodes publiques
    # ------------------------------------------------------------------
    def simple_complete(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Appel simple sans persistance en base.
        """
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt vide")

        self._ensure_not_banned("input", prompt)
        history = self._build_history_for_prompt(prompt, system_prompt=system_prompt)
        out = self._call_llm(
            history,
            temperature=temperature,
            max_tokens=max_tokens,
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
        extra_context: Optional[str] = None,
    ) -> Message:
        """
        Utilise l'historique complet de la conversation, envoie à l'API,
        récupère la réponse et la sauvegarde comme message agent.
        """
        self._validate_id("conversation_id", conversation_id)
        self._validate_id("user_id", user_id)

        # 1) Construire le history pour l'API
        history = self._build_history_for_conversation(
            conversation_id,
            system_prompt=system_prompt,
            extra_context=extra_context,
        )

        # 2) Vérif banned côté input
        for msg in history:
            if msg.get("role") in ("user", "system"):
                self._ensure_not_banned("input", msg.get("content", ""))

        # 3) Appel API
        print("[LLMService] Envoi de la requête à l'API LLM...")
        out = self._call_llm(
            history,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = str(out.get("content", ""))  # texte généré
        print(f"[LLMService] Contenu reçu (début) : {content[:200]}...")
        self._ensure_not_banned("output", content)

        # 4) Persister la réponse agent
        now = datetime.now(timezone.utc)
        msg_obj = Message(
            id_message=None,
            id_conversation=conversation_id,
            id_user=AGENT_USER_ID,
            datetime=now,
            message=content,
            is_from_agent=True,
        )

        create_fn = getattr(self.message_dao, "create", None)
        if not callable(create_fn):
            raise RuntimeError("MessageDAO ne fournit pas create")

        created: Message = create_fn(msg_obj)
        return created

    @staticmethod
    def requete_invitee(prompt: str) -> str:
        """
        Méthode statique pour des requêtes invitées simples.
        """

        default_temperature_invite = 0.7
        default_max_tokens_invite = 512
        timeout_invite = 20.0
        url = f"https://ensai-gpt-109912438483.europe-west4.run.app/generate"
        print(f"[LLMService] Appel API POST inivitee {url}")

        history_invitee = [
    {
      "content": "Tu es un assistant utile.",
      "role": "system"
    },
    {
      "content": prompt,
      "role": "user"
    }
  ]

        payload: Dict[str, Any] = {
            "history": history_invitee,
            "max_tokens": default_max_tokens_invite,
            "temperature": default_temperature_invite,
            "top_p": 1,
        }

        print(f"[LLMService] Payload envoyé invitee: {payload}")

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout_invite,
            )
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"[LLMService] HTTP ERROR invitee {resp.status_code}: {resp.text}")
            raise RuntimeError(
                f"[LLM] HTTP invitee {resp.status_code} sur {url} – corps: {resp.text[:800]}"
            ) from e
        except requests.exceptions.Timeout as e:
            raise RuntimeError(f"[LLM] Timeout invitee ({timeout_invite}s) sur {url}") from e
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"[LLM] Erreur réseau sur invitee {url}: {e}") from e

        try:
            data = resp.json()
        except ValueError as e:
            print(f"[LLMService] Réponse non JSON invitee : {resp.text[:800]}")
            raise RuntimeError(f"[LLM] Réponse non-JSON depuis invitee {url}") from e

        print(f"[LLMService] Réponse brute invitee: {data}")

        # On suit exactement le format de l'exemple:
        # data["choices"][0]["message"]["content"]
        try:
            first_choice = data["choices"][0]
            message = first_choice["message"]
            content = str(message.get("content", ""))
        except Exception as e:
            raise RuntimeError(
                f"[LLM] Format de réponse inattendu, impossible de lire choices[0].message.content: {data}"
            ) from e

        usage_raw = data.get("usage", {}) if isinstance(data, dict) else {}
        usage: Dict[str, int] = {}
        if isinstance(usage_raw, dict):
            usage = {
                "prompt_tokens": int(usage_raw.get("prompt_tokens", 0)),
                "completion_tokens": int(usage_raw.get("completion_tokens", 0)),
                "total_tokens": int(usage_raw.get("total_tokens", 0)),
            }

        return {
            "content": content,
            "usage": usage,
        }
