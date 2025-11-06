# src/tests/test_service/test_LLMService_HTTP.py
import json
import datetime
import pytest
from unittest.mock import MagicMock

try:
    from ObjetMetier.Message import Message
except Exception:
    from src.ObjetMetier.Message import Message  # type: ignore

try:
    from Service.LLMService import LLMService
except Exception:
    from src.Service.LLMService import LLMService  # type: ignore


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def make_msg(
    id_conversation=1,
    id_user=123,
    text="hello",
    is_from_agent=False,
    dt=None,
):
    if dt is None:
        dt = datetime.datetime(2025, 1, 1, 12, 0, 0)
    return Message(
        id_message=None,
        id_conversation=id_conversation,
        id_user=id_user,
        datetime=dt,
        message=text,
        is_from_agent=is_from_agent,
    )


class FakeResponseOK:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        # 200 -> no error
        return None

    def json(self):
        return self._payload


class FakeResponseError:
    def __init__(self, status_code=500, text="boom"):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        # Simule requests.HTTPError
        import requests

        raise requests.HTTPError(f"{self.status_code} {self.text}")

    def json(self):
        return {"error": self.text}


# ---------------------------------------------------------------------
# Tests simple_complete
# ---------------------------------------------------------------------
def test_simple_complete_happy_path():
    # Mock session.post -> OK
    session = MagicMock()
    session.post.return_value = FakeResponseOK(
        {"content": "Bonjour!", "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}}
    )

    dao = MagicMock()  # pas utilisé par simple_complete
    svc = LLMService(
        dao,
        requests_session=session,
        base_url="https://ensai-gpt-109912438483.europe-west4.run.app",
        default_system_prompt="You are helpful.",
    )

    out = svc.simple_complete("Salut ?")
    assert out == "Bonjour!"

    # Vérifie le JSON envoyé
    args, kwargs = session.post.call_args
    assert args[0].endswith("/chat/generate")
    body = kwargs["json"]
    assert body["messages"][0] == {"role": "system", "content": "You are helpful."}
    assert body["messages"][1] == {"role": "user", "content": "Salut ?"}
    assert body["temperature"] == svc.default_temperature
    assert body["max_tokens"] == svc.default_max_tokens
    # pas de model si None
    assert "model" not in body


def test_simple_complete_with_api_key_header():
    session = MagicMock()
    session.post.return_value = FakeResponseOK({"content": "ok"})

    dao = MagicMock()
    svc = LLMService(
        dao,
        requests_session=session,
        base_url="https://ensai-gpt-109912438483.europe-west4.run.app",
        api_key="SECRET123",
    )
    _ = svc.simple_complete("Ping")

    _, kwargs = session.post.call_args
    headers = kwargs["headers"]
    assert headers.get("Authorization") == "Bearer SECRET123"
    assert headers.get("Content-Type") == "application/json"


def test_simple_complete_banned_input_raises():
    session = MagicMock()
    session.post.return_value = FakeResponseOK({"content": "ne devrait pas être appelé"})

    banned = MagicMock()
    banned.contains_banned.return_value = True  # déclenche l'erreur

    dao = MagicMock()
    svc = LLMService(dao, requests_session=session, banned_service=banned)

    with pytest.raises(ValueError):
        svc.simple_complete("Texte interdit")

    # L'appel HTTP ne doit PAS être fait
    session.post.assert_not_called()


def test_simple_complete_http_error_propagates():
    session = MagicMock()
    session.post.return_value = FakeResponseError(502, "Bad Gateway")

    dao = MagicMock()
    svc = LLMService(dao, requests_session=session)

    import requests

    with pytest.raises(requests.HTTPError):
        svc.simple_complete("Hello")


# ---------------------------------------------------------------------
# Tests generate_agent_reply
# ---------------------------------------------------------------------
def test_generate_agent_reply_sends_full_history_and_persists():
    # Historique : user -> agent -> user
    history = [
        make_msg(text="Salut", id_user=11, is_from_agent=False, dt=datetime.datetime(2025, 1, 1, 10, 0, 0)),
        make_msg(text="Bonjour, comment puis-je vous aider ?", id_user=0, is_from_agent=True, dt=datetime.datetime(2025, 1, 1, 10, 0, 1)),
        make_msg(text="J'ai un souci.", id_user=11, is_from_agent=False, dt=datetime.datetime(2025, 1, 1, 10, 1, 0)),
    ]

    # DAO
    dao = MagicMock()
    dao.get_messages_by_conversation.return_value = history

    # Session -> réponse modèle
    session = MagicMock()
    session.post.return_value = FakeResponseOK(
        {"content": "Voici la solution.", "usage": {"prompt_tokens": 42, "completion_tokens": 10, "total_tokens": 52}}
    )

    # create() renvoie l'objet persisted (on peut renvoyer ce qu'on veut)
    def fake_create(msg_obj):
        # Simule que la DB assigne un id_message
        msg_obj.id_message = 999
        return msg_obj

    dao.create.side_effect = fake_create

    svc = LLMService(
        dao,
        requests_session=session,
        default_system_prompt="System prompt ici.",
    )

    created = svc.generate_agent_reply(conversation_id=1, user_id=11)

    # Vérifie persistance
    assert created.is_from_agent is True
    assert created.message == "Voici la solution."
    assert created.id_message == 999
    dao.create.assert_called_once()

    # Vérifie le payload envoyé à l'API
    args, kwargs = session.post.call_args
    assert args[0].endswith("/chat/generate")
    body = kwargs["json"]
    msgs = body["messages"]
    assert msgs[0] == {"role": "system", "content": "System prompt ici."}
    # mapping des rôles + préfixe <user id=...>
    assert msgs[1] == {"role": "user", "content": "<user id=11>\nSalut"}
    assert msgs[2] == {"role": "assistant", "content": "Bonjour, comment puis-je vous aider ?"}
    assert msgs[3] == {"role": "user", "content": "<user id=11>\nJ'ai un souci."}


def test_generate_agent_reply_with_extra_context():
    dao = MagicMock()
    dao.get_messages_by_conversation.return_value = [make_msg(text="Aide moi", id_user=10)]

    session = MagicMock()
    session.post.return_value = FakeResponseOK({"content": "OK"})

    svc = LLMService(dao, requests_session=session)

    _ = svc.generate_agent_reply(1, 10, extra_context="Infos supplémentaires")

    _, kwargs = session.post.call_args
    msgs = kwargs["json"]["messages"]
    # Le dernier message system doit contenir le contexte
    assert msgs[-1]["role"] == "system"
    assert "Infos supplémentaires" in msgs[-1]["content"]


def test_generate_agent_reply_missing_dao_method_raises():
    dao = MagicMock()
    # ni get_messages_by_conversation ni get_by_conversation
    dao.get_messages_by_conversation = None
    dao.get_by_conversation = None

    session = MagicMock()
    session.post.return_value = FakeResponseOK({"content": "x"})

    svc = LLMService(dao, requests_session=session)
    with pytest.raises(RuntimeError):
        svc.generate_agent_reply(1, 2)


def test_generate_agent_reply_banned_output_raises_and_no_persist():
    # Historique minimal
    dao = MagicMock()
    dao.get_messages_by_conversation.return_value = [make_msg(text="Hi", id_user=9)]

    # L'API répond du contenu "interdit"
    session = MagicMock()
    session.post.return_value = FakeResponseOK({"content": ">>>BANNED<<<"})

    banned = MagicMock()
    # Autorise input, bloque output
    banned.contains_banned.side_effect = [False, True]

    svc = LLMService(dao, requests_session=session, banned_service=banned)

    with pytest.raises(ValueError):
        svc.generate_agent_reply(1, 9)

    # Rien ne doit être créé en base si contenu interdit
    dao.create.assert_not_called()


def test_generate_agent_reply_http_error_propagates():
    dao = MagicMock()
    dao.get_messages_by_conversation.return_value = [make_msg(text="hello", id_user=1)]

    session = MagicMock()
    session.post.return_value = FakeResponseError(503, "Service Unavailable")

    svc = LLMService(dao, requests_session=session)

    import requests

    with pytest.raises(requests.HTTPError):
        svc.generate_agent_reply(1, 1)

