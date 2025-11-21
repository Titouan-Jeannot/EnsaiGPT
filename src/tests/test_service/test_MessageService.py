import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from datetime import datetime, timezone

from Service.MessageService import MessageService, AGENT_USER_ID
from ObjetMetier.Message import Message


# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------

@pytest.fixture
def mock_message_dao():
    return MagicMock()


@pytest.fixture
def mock_user_service():
    return MagicMock()


@pytest.fixture
def mock_auth_service():
    return MagicMock()


@pytest.fixture
def msg_service(mock_message_dao, mock_user_service, mock_auth_service):
    return MessageService(
        message_dao=mock_message_dao,
        user_service=mock_user_service,
        auth_service=mock_auth_service,
    )


# -------------------------------------------------------------------
# send_message
# -------------------------------------------------------------------

def test_send_message_ok_with_user_service(mock_message_dao, mock_user_service):
    # user existe
    mock_user_service.get_user_by_id.return_value = SimpleNamespace(id=1)

    svc = MessageService(
        message_dao=mock_message_dao,
        user_service=mock_user_service,
        auth_service=None,
    )

    # retour du DAO
    created = Message(
        id_message=123,
        id_conversation=10,
        id_user=1,
        datetime=datetime.now(timezone.utc),
        message="hello",
        is_from_agent=False,
    )
    mock_message_dao.create.return_value = created

    res = svc.send_message(10, 1, "hello")

    mock_user_service.get_user_by_id.assert_called_once_with(1)
    mock_message_dao.create.assert_called_once()
    assert res is created
    arg = mock_message_dao.create.call_args[0][0]
    assert isinstance(arg, Message)
    assert arg.id_conversation == 10
    assert arg.id_user == 1
    assert arg.is_from_agent is False
    assert arg.message == "hello"


def test_send_message_ok_with_auth_service(mock_message_dao, mock_auth_service):
    svc = MessageService(
        message_dao=mock_message_dao,
        user_service=None,          # pas de user_service
        auth_service=mock_auth_service,
    )

    created = Message(
        id_message=123,
        id_conversation=10,
        id_user=2,
        datetime=datetime.now(timezone.utc),
        message="bonjour",
        is_from_agent=False,
    )
    mock_message_dao.create.return_value = created

    res = svc.send_message(10, 2, "bonjour")

    mock_auth_service.check_user_exists.assert_called_once_with(2)
    mock_message_dao.create.assert_called_once()
    assert res is created


@pytest.mark.parametrize("bad_cid", [-1, "a", 1.5])
def test_send_message_invalid_conversation_id(msg_service, bad_cid):
    with pytest.raises(ValueError, match="conversation_id invalide"):
        msg_service.send_message(bad_cid, 1, "hello")


@pytest.mark.parametrize("bad_uid", [-1, "a", 1.5])
def test_send_message_invalid_user_id(msg_service, bad_uid):
    with pytest.raises(ValueError, match="user_id invalide"):
        msg_service.send_message(10, bad_uid, "hello")


@pytest.mark.parametrize("bad_msg", ["", "   ", None])
def test_send_message_invalid_message_content(msg_service, bad_msg):
    with pytest.raises(ValueError, match="message non fourni"):
        msg_service.send_message(10, 1, bad_msg)  # type: ignore[arg-type]


def test_send_message_too_long(msg_service):
    long_msg = "x" * 5001
    with pytest.raises(ValueError, match="message trop long"):
        msg_service.send_message(10, 1, long_msg)


def test_send_message_user_not_found_with_user_service(mock_message_dao, mock_user_service):
    mock_user_service.get_user_by_id.return_value = None
    svc = MessageService(
        message_dao=mock_message_dao,
        user_service=mock_user_service,
        auth_service=None,
    )

    with pytest.raises(ValueError, match="Utilisateur introuvable"):
        svc.send_message(10, 1, "hello")


def test_send_message_user_not_found_with_auth_service(mock_message_dao, mock_auth_service):
    mock_auth_service.check_user_exists.side_effect = Exception("boom")

    svc = MessageService(
        message_dao=mock_message_dao,
        user_service=None,
        auth_service=mock_auth_service,
    )

    with pytest.raises(ValueError, match="Utilisateur introuvable"):
        svc.send_message(10, 1, "hello")


# -------------------------------------------------------------------
# get_messages
# -------------------------------------------------------------------

def test_get_messages_ok(msg_service, mock_message_dao):
    m1 = Message(None, 10, 1, datetime.now(timezone.utc), "a", False)
    m2 = Message(None, 10, 2, datetime.now(timezone.utc), "b", True)
    mock_message_dao.get_messages_by_conversation.return_value = [m1, m2]

    res = msg_service.get_messages(10)

    mock_message_dao.get_messages_by_conversation.assert_called_once_with(10)
    assert res == [m1, m2]


@pytest.mark.parametrize("bad_cid", [-1, "a"])
def test_get_messages_invalid_conversation_id(msg_service, bad_cid):
    with pytest.raises(ValueError, match="conversation_id invalide"):
        msg_service.get_messages(bad_cid)  # type: ignore[arg-type]


# -------------------------------------------------------------------
# get_message_by_id
# -------------------------------------------------------------------

def test_get_message_by_id_ok(msg_service, mock_message_dao):
    m = Message(5, 10, 1, datetime.now(timezone.utc), "x", False)
    mock_message_dao.get_by_id.return_value = m

    res = msg_service.get_message_by_id(5)

    mock_message_dao.get_by_id.assert_called_once_with(5)
    assert res is m


@pytest.mark.parametrize("bad_mid", [-1, "a"])
def test_get_message_by_id_invalid(msg_service, bad_mid):
    with pytest.raises(ValueError, match="message_id invalide"):
        msg_service.get_message_by_id(bad_mid)  # type: ignore[arg-type]


# -------------------------------------------------------------------
# delete_all_messages_by_conversation
# -------------------------------------------------------------------

def test_delete_all_messages_by_conversation_ok(msg_service, mock_message_dao):
    msg_service.delete_all_messages_by_conversation(10)
    mock_message_dao.delete_by_conversation.assert_called_once_with(10)


@pytest.mark.parametrize("bad_cid", [-1, "a"])
def test_delete_all_messages_by_conversation_invalid(msg_service, bad_cid):
    with pytest.raises(ValueError, match="conversation_id invalide"):
        msg_service.delete_all_messages_by_conversation(bad_cid)  # type: ignore[arg-type]


# -------------------------------------------------------------------
# check_conversation_exists
# -------------------------------------------------------------------

def test_check_conversation_exists_true(msg_service, mock_message_dao):
    mock_message_dao.count_messages_by_conversation.return_value = 0
    assert msg_service.check_conversation_exists(10) is True


def test_check_conversation_exists_false(msg_service, mock_message_dao):
    mock_message_dao.count_messages_by_conversation.return_value = -1
    assert msg_service.check_conversation_exists(10) is False


# -------------------------------------------------------------------
# get_last_message
# -------------------------------------------------------------------

def test_get_last_message_ok(msg_service, mock_message_dao):
    m = Message(7, 10, 1, datetime.now(timezone.utc), "last", False)
    mock_message_dao.get_last_message.return_value = m

    res = msg_service.get_last_message(10)

    mock_message_dao.get_last_message.assert_called_once_with(10)
    assert res is m


@pytest.mark.parametrize("bad_cid", [-1, "a"])
def test_get_last_message_invalid(msg_service, bad_cid):
    with pytest.raises(ValueError, match="conversation_id invalide"):
        msg_service.get_last_message(bad_cid)  # type: ignore[arg-type]


# -------------------------------------------------------------------
# validate_message_content
# -------------------------------------------------------------------

def test_validate_message_content_ok(msg_service):
    assert msg_service.validate_message_content("Ceci est un message normal.")


def test_validate_message_content_empty(msg_service):
    with pytest.raises(ValueError, match="Message vide"):
        msg_service.validate_message_content("   ")


def test_validate_message_content_too_long(msg_service):
    big = "x" * 5001
    with pytest.raises(ValueError, match="Message trop long"):
        msg_service.validate_message_content(big)


@pytest.mark.parametrize(
    "pattern",
    [
        "<script>",
        "javascript:",
        "data:",
        "vbscript:",
        "onclick=",
        "onerror=",
        "--",
        "/*",
        "*/",
        "@@",
    ],
)
def test_validate_message_content_forbidden_patterns(msg_service, pattern):
    txt = f"Du texte avant {pattern} du texte après"
    with pytest.raises(ValueError, match="Contenu non autorisé"):
        msg_service.validate_message_content(txt)


def test_validate_message_content_null_char(msg_service):
    with pytest.raises(ValueError, match="Caractères nuls non autorisés"):
        msg_service.validate_message_content("abc\x00def")


# -------------------------------------------------------------------
# send_agent_message
# -------------------------------------------------------------------

def test_send_agent_message_ok(msg_service, mock_message_dao, monkeypatch):
    # on s'assure que validate_message_content est bien appelée
    called = {}

    def fake_validate(msg):
        called["ok"] = True
        return True

    monkeypatch.setattr(msg_service, "validate_message_content", fake_validate)

    created = Message(
        id_message=99,
        id_conversation=10,
        id_user=AGENT_USER_ID,
        datetime=datetime.now(timezone.utc),
        message="Réponse agent",
        is_from_agent=True,
    )
    mock_message_dao.create.return_value = created

    res = msg_service.send_agent_message(10, "Réponse agent")

    assert called.get("ok") is True
    mock_message_dao.create.assert_called_once()
    arg = mock_message_dao.create.call_args[0][0]
    assert arg.id_conversation == 10
    assert arg.id_user == AGENT_USER_ID
    assert arg.is_from_agent is True
    assert res is created


def test_send_agent_message_invalid_content_propagates(msg_service, monkeypatch):
    def fake_validate(msg):
        raise ValueError("bad content")

    monkeypatch.setattr(msg_service, "validate_message_content", fake_validate)

    with pytest.raises(ValueError, match="bad content"):
        msg_service.send_agent_message(10, "xxx")  # ne doit pas appeler le DAO


# -------------------------------------------------------------------
# get_messages_paginated
# -------------------------------------------------------------------

def test_get_messages_paginated_ok(msg_service, mock_message_dao):
    msg_service.get_messages_paginated(10, page=2, per_page=20)
    mock_message_dao.get_messages_by_conversation_paginated.assert_called_once_with(
        10, 2, 20
    )


def test_get_messages_paginated_invalid_page(msg_service):
    with pytest.raises(ValueError, match="Page invalide"):
        msg_service.get_messages_paginated(10, page=0, per_page=20)


# -------------------------------------------------------------------
# count_messages
# -------------------------------------------------------------------

def test_count_messages(msg_service, mock_message_dao):
    mock_message_dao.count_messages_by_conversation.return_value = 42
    res = msg_service.count_messages(10)
    mock_message_dao.count_messages_by_conversation.assert_called_once_with(10)
    assert res == 42


# -------------------------------------------------------------------
# search_messages
# -------------------------------------------------------------------

def test_search_messages_ok(msg_service, mock_message_dao):
    msg_service.search_messages(10, "bonjour")
    mock_message_dao.search_messages.assert_called_once_with(10, "bonjour")


def test_search_messages_invalid_keyword(msg_service):
    with pytest.raises(ValueError, match="Mot-clé de recherche requis"):
        msg_service.search_messages(10, "   ")


# -------------------------------------------------------------------
# get_messages_by_date_range
# -------------------------------------------------------------------

def test_get_messages_by_date_range_ok(msg_service, mock_message_dao):
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 2, tzinfo=timezone.utc)

    msg_service.get_messages_by_date_range(10, start, end)

    mock_message_dao.get_messages_by_date_range.assert_called_once_with(
        10, start, end
    )


# -------------------------------------------------------------------
# update_message
# -------------------------------------------------------------------

def test_update_message_ok(msg_service, mock_message_dao, monkeypatch):
    msg_obj = SimpleNamespace(
        id_message=5,
        id_conversation=10,
        id_user=1,
        datetime=datetime.now(timezone.utc),
        message="old",
        is_from_agent=False,
    )
    # get_message_by_id doit renvoyer un message
    monkeypatch.setattr(msg_service, "get_message_by_id", lambda mid: msg_obj)

    # validate ok
    monkeypatch.setattr(msg_service, "validate_message_content", lambda txt: True)
    mock_message_dao.update.return_value = True

    res = msg_service.update_message(5, "new content")

    assert msg_obj.message == "new content"
    mock_message_dao.update.assert_called_once_with(msg_obj)
    assert res is True


def test_update_message_not_found(msg_service, monkeypatch):
    monkeypatch.setattr(msg_service, "get_message_by_id", lambda mid: None)

    with pytest.raises(ValueError, match="Message introuvable"):
        msg_service.update_message(5, "x")


def test_update_message_invalid_content(msg_service, monkeypatch):
    msg_obj = SimpleNamespace(
        id_message=5,
        id_conversation=10,
        id_user=1,
        datetime=datetime.now(timezone.utc),
        message="old",
        is_from_agent=False,
    )
    monkeypatch.setattr(msg_service, "get_message_by_id", lambda mid: msg_obj)

    def fake_validate(txt):
        raise ValueError("non valide")

    monkeypatch.setattr(msg_service, "validate_message_content", fake_validate)

    with pytest.raises(ValueError, match="non valide"):
        msg_service.update_message(5, "bad")


# -------------------------------------------------------------------
# delete_message
# -------------------------------------------------------------------

def test_delete_message_ok(msg_service, mock_message_dao):
    mock_message_dao.delete_by_id.return_value = True
    res = msg_service.delete_message(5)
    mock_message_dao.delete_by_id.assert_called_once_with(5)
    assert res is True


@pytest.mark.parametrize("bad_mid", [-1, "a"])
def test_delete_message_invalid(msg_service, bad_mid):
    with pytest.raises(ValueError, match="message_id invalide"):
        msg_service.delete_message(bad_mid)  # type: ignore[arg-type]
