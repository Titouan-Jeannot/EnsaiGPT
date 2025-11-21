import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from datetime import datetime, timezone

import requests

from Service.LLMService import LLMService, AGENT_USER_ID
from ObjetMetier.Message import Message
from ObjetMetier.Conversation import Conversation
from ObjetMetier.User import User


# -------------------------------------------------------------------
# Fixtures DAO + service
# -------------------------------------------------------------------

@pytest.fixture
def mock_message_dao():
    return MagicMock()


@pytest.fixture
def mock_conversation_dao():
    return MagicMock()


@pytest.fixture
def mock_user_dao():
    return MagicMock()


@pytest.fixture
def llm_service(mock_message_dao, mock_conversation_dao, mock_user_dao):
    svc = LLMService(
        message_dao=mock_message_dao,
        conversation_dao=mock_conversation_dao,
        user_dao=mock_user_dao,
        base_url="https://fake-ensai-gpt.test",  # évite les vrais appels
        default_system_prompt="SYSTEM_DEFAULT",
        default_temperature=0.5,
        default_max_tokens=256,
        timeout=5.0,
    )
    # On fixe les overrides pour être sûrs des valeurs
    svc.temperature_override = 0.9
    svc.top_p_override = 0.8
    svc.max_tokens_override = 128
    return svc


# -------------------------------------------------------------------
# Helpers pour mocker requests.post
# -------------------------------------------------------------------

class DummyRespOK:
    def __init__(self, data):
        self._data = data
        self.status_code = 200
        self.text = "OK"

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class DummyRespHTTPError:
    def __init__(self):
        self.status_code = 500
        self.text = "Erreur interne"

    def raise_for_status(self):
        raise requests.exceptions.HTTPError("500 error")

    def json(self):
        return {}


# -------------------------------------------------------------------
# Tests _validate_id
# -------------------------------------------------------------------

def test_validate_id_ok(llm_service):
    llm_service._validate_id("conversation_id", 1)
    llm_service._validate_id("user_id", 42)


@pytest.mark.parametrize("bad", [0, -1, "a", 1.5])
def test_validate_id_invalid(llm_service, bad):
    with pytest.raises(ValueError, match="invalide"):
        llm_service._validate_id("conversation_id", bad)


# -------------------------------------------------------------------
# Tests _call_llm
# -------------------------------------------------------------------

def test_call_llm_success(llm_service, monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=None):
        assert url.endswith("/generate")
        # on vérifie que les paramètres sont passés
        assert "history" in json
        assert "max_tokens" in json
        assert "temperature" in json
        assert "top_p" in json
        data = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Réponse LLM",
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }
        return DummyRespOK(data)

    monkeypatch.setattr("Service.LLMService.requests.post", fake_post)

    history = [{"role": "system", "content": "SYS"}]
    out = llm_service._call_llm(
        history,
        temperature=0.3,
        max_tokens=50,
        top_p=0.9,
    )

    assert out["content"] == "Réponse LLM"
    assert out["usage"]["prompt_tokens"] == 10
    assert out["usage"]["completion_tokens"] == 20
    assert out["usage"]["total_tokens"] == 30


def test_call_llm_http_error(llm_service, monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=None):
        return DummyRespHTTPError()

    monkeypatch.setattr("Service.LLMService.requests.post", fake_post)

    with pytest.raises(RuntimeError, match="HTTP"):
        llm_service._call_llm([{"role": "system", "content": "SYS"}])


def test_call_llm_timeout(llm_service, monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=None):
        raise requests.exceptions.Timeout("timeout!")

    monkeypatch.setattr("Service.LLMService.requests.post", fake_post)

    with pytest.raises(RuntimeError, match="Timeout"):
        llm_service._call_llm([{"role": "system", "content": "SYS"}])


def test_call_llm_bad_json(llm_service, monkeypatch):
    class DummyNoJSON:
        def __init__(self):
            self.status_code = 200
            self.text = "not json"

        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError("no json")

    def fake_post(url, json=None, headers=None, timeout=None):
        return DummyNoJSON()

    monkeypatch.setattr("Service.LLMService.requests.post", fake_post)

    with pytest.raises(RuntimeError, match="non-JSON"):
        llm_service._call_llm([{"role": "system", "content": "SYS"}])


def test_call_llm_bad_structure(llm_service, monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=None):
        # pas de choices[0].message.content
        data = {"something": "wrong"}
        return DummyRespOK(data)

    monkeypatch.setattr("Service.LLMService.requests.post", fake_post)

    with pytest.raises(RuntimeError, match="Format de réponse inattendu"):
        llm_service._call_llm([{"role": "system", "content": "SYS"}])


# -------------------------------------------------------------------
# Tests _build_history_for_conversation
# -------------------------------------------------------------------

def _make_msg(id_user, text, is_agent=False, dt=None):
    dt = dt or datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    return Message(
        id_message=None,
        id_conversation=10,
        id_user=id_user,
        datetime=dt,
        message=text,
        is_from_agent=is_agent,
    )


def test_build_history_with_conv_prompt_priority(llm_service, mock_message_dao, mock_conversation_dao, mock_user_dao):
    # messages
    m1 = _make_msg(1, "Hello", is_agent=False)
    m2 = _make_msg(AGENT_USER_ID, "Hi!", is_agent=True)
    mock_message_dao.get_messages_by_conversation.return_value = [m1, m2]

    # prompts : conv > user > default
    mock_conversation_dao.get_prompts_conversation.return_value = "PROMPT_CONV"
    mock_user_dao.get_prompt_user.return_value = "PROMPT_USER"

    history = llm_service._build_history_for_conversation(conversation_id=10, user_id=1)

    assert history[0]["role"] == "system"
    assert history[0]["content"] == "PROMPT_CONV"

    # premier message user
    assert history[1]["role"] == "user"
    assert "<user id=1>" in history[1]["content"]
    assert "Hello" in history[1]["content"]

    # deuxième message agent
    assert history[2]["role"] == "assistant"
    assert "Hi!" in history[2]["content"]


def test_build_history_with_user_prompt_when_no_conv(llm_service, mock_message_dao, mock_conversation_dao, mock_user_dao):
    mock_message_dao.get_messages_by_conversation.return_value = []
    mock_conversation_dao.get_prompts_conversation.return_value = ""
    mock_user_dao.get_prompt_user.return_value = "PROMPT_USER_ONLY"

    history = llm_service._build_history_for_conversation(conversation_id=10, user_id=1)
    assert history[0]["role"] == "system"
    assert history[0]["content"] == "PROMPT_USER_ONLY"


def test_build_history_with_default_prompt(llm_service, mock_message_dao, mock_conversation_dao, mock_user_dao):
    mock_message_dao.get_messages_by_conversation.return_value = []

    # conversation_dao ou user_dao qui lèvent des exceptions
    mock_conversation_dao.get_prompts_conversation.side_effect = Exception("boom conv")
    mock_user_dao.get_prompt_user.side_effect = Exception("boom user")

    history = llm_service._build_history_for_conversation(conversation_id=10, user_id=1)
    assert history[0]["role"] == "system"
    # default_system_prompt passé au constructeur
    assert history[0]["content"] == "SYSTEM_DEFAULT"


def test_build_history_raises_if_message_dao_missing_method(llm_service):
    # on met un objet sans méthode get_messages_by_conversation
    llm_service.message_dao = SimpleNamespace()
    with pytest.raises(RuntimeError, match="ne fournit pas get_messages_by_conversation"):
        llm_service._build_history_for_conversation(conversation_id=10, user_id=1)


# -------------------------------------------------------------------
# Tests generate_agent_reply
# -------------------------------------------------------------------

def test_generate_agent_reply_success(llm_service, mock_message_dao, monkeypatch):
    # on mocke _build_history_for_conversation pour éviter de re-tester sa logique
    def fake_build_history(conv_id, user_id):
        assert conv_id == 10
        assert user_id == 2
        return [{"role": "system", "content": "SYS"}, {"role": "user", "content": "Hi"}]

    monkeypatch.setattr(llm_service, "_build_history_for_conversation", fake_build_history)

    # on mocke _call_llm
    def fake_call_llm(history, temperature=None, max_tokens=None, top_p=None):
        assert history[0]["content"] == "SYS"
        return {"content": "Réponse agent", "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3}}

    monkeypatch.setattr(llm_service, "_call_llm", fake_call_llm)

    now = datetime.now(timezone.utc)
    created_msg = Message(
        id_message=123,
        id_conversation=10,
        id_user=AGENT_USER_ID,
        datetime=now,
        message="Réponse agent",
        is_from_agent=True,
    )
    mock_message_dao.create.return_value = created_msg

    res = llm_service.generate_agent_reply(conversation_id=10, user_id=2)

    # on récupère bien le message créé par le DAO
    assert res is created_msg
    mock_message_dao.create.assert_called_once()
    arg = mock_message_dao.create.call_args[0][0]
    assert arg.id_conversation == 10
    assert arg.id_user == AGENT_USER_ID
    assert arg.is_from_agent is True
    assert isinstance(arg.message, str)


@pytest.mark.parametrize("cid, uid", [(0, 1), (-1, 1), (1, 0), (1, -2)])
def test_generate_agent_reply_invalid_ids(llm_service, cid, uid):
    with pytest.raises(ValueError, match="invalide"):
        llm_service.generate_agent_reply(conversation_id=cid, user_id=uid)


def test_generate_agent_reply_missing_create(llm_service, monkeypatch):
    # _build_history ok
    monkeypatch.setattr(llm_service, "_build_history_for_conversation", lambda c, u: [])
    # _call_llm ok
    monkeypatch.setattr(llm_service, "_call_llm", lambda history, **kw: {"content": "x", "usage": {}})

    # DAO sans méthode create
    llm_service.message_dao = SimpleNamespace()
    with pytest.raises(RuntimeError, match="ne fournit pas create"):
        llm_service.generate_agent_reply(conversation_id=1, user_id=1)


# -------------------------------------------------------------------
# Tests requete_invitee (méthode statique)
# -------------------------------------------------------------------

def test_requete_invitee_success(monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=None):
        # vérifier que le prompt est bien dans l'historique
        hist = json["history"]
        assert hist[1]["content"] == "Bonjour"
        data = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Réponse invitée",
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 7,
                "total_tokens": 12,
            },
        }
        return DummyRespOK(data)

    monkeypatch.setattr("Service.LLMService.requests.post", fake_post)

    out = LLMService.requete_invitee("Bonjour")
    assert out["content"] == "Réponse invitée"
    assert out["usage"]["total_tokens"] == 12


def test_requete_invitee_http_error(monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=None):
        return DummyRespHTTPError()

    monkeypatch.setattr("Service.LLMService.requests.post", fake_post)

    with pytest.raises(RuntimeError, match="HTTP invitee"):
        LLMService.requete_invitee("Hello")


def test_requete_invitee_bad_json(monkeypatch):
    class DummyNoJSON:
        def __init__(self):
            self.status_code = 200
            self.text = "not json"

        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError("no json")

    def fake_post(url, json=None, headers=None, timeout=None):
        return DummyNoJSON()

    monkeypatch.setattr("Service.LLMService.requests.post", fake_post)

    with pytest.raises(RuntimeError, match="non-JSON depuis invitee"):
        LLMService.requete_invitee("Hello")
