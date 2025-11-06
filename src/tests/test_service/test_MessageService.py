# src/tests/test_service/test_MessageService.py
import datetime
import pytest
from unittest.mock import MagicMock

from src.Service.MessageService import MessageService

# On importe la classe Message réelle pour garder la même signature que le projet
from src.ObjetMetier.Message import Message


# -------- Helpers --------
def make_message(
    id_message=None,
    id_conversation=1,
    id_user=10,
    text="hello",
    is_from_agent=False,
    dt=None,
):
    return Message(
        id_message=id_message,
        id_conversation=id_conversation,
        id_user=id_user,
        datetime=dt or datetime.datetime.now(),
        message=text,
        is_from_agent=is_from_agent,
    )


# =========================
# send_message
# =========================
def test_send_message_success_with_user_service():
    dao = MagicMock()
    user_service = MagicMock()
    auth_service = None

    # l'utilisateur existe
    user_service.get_user_by_id.return_value = object()

    svc = MessageService(dao, user_service, auth_service)

    # le DAO renverra l'objet créé (avec id attribué)
    created = make_message(id_message=123, id_user=42, text="Salut")
    dao.create.return_value = created

    result = svc.send_message(conversation_id=7, user_id=42, message="Salut")
    assert result is created
    dao.create.assert_called_once()
    user_service.get_user_by_id.assert_called_once_with(42)
    assert dao.create.call_args.args[0].is_from_agent is False


def test_send_message_uses_auth_service_when_no_user_service():
    dao = MagicMock()
    user_service = None
    auth_service = MagicMock()
    auth_service.check_user_exists.return_value = True

    svc = MessageService(dao, user_service, auth_service)
    dao.create.return_value = make_message(id_message=1, id_user=5, text="ok")

    got = svc.send_message(3, 5, "ok")
    assert got.id_message == 1
    auth_service.check_user_exists.assert_called_once_with(5)
    dao.create.assert_called_once()


@pytest.mark.parametrize(
    "conv_id,user_id,msg",
    [
        (-1, 1, "x"),
        (1, -1, "x"),
        (1, 1, ""),            # message vide
        (1, 1, "   "),         # message espaces
    ],
)
def test_send_message_invalid_inputs(conv_id, user_id, msg):
    svc = MessageService(MagicMock())
    with pytest.raises(ValueError):
        svc.send_message(conv_id, user_id, msg)


def test_send_message_too_long():
    svc = MessageService(MagicMock())
    with pytest.raises(ValueError):
        svc.send_message(1, 1, "x" * 5001)


def test_send_message_user_not_found():
    dao = MagicMock()
    user_service = MagicMock()
    user_service.get_user_by_id.return_value = None
    svc = MessageService(dao, user_service, None)
    with pytest.raises(ValueError):
        svc.send_message(1, 99, "hello")


# =========================
# get_messages / get_message_by_id / delete_all...
# =========================
def test_get_messages_delegates_to_dao():
    dao = MagicMock()
    svc = MessageService(dao)
    expected = [make_message(id_message=1), make_message(id_message=2)]
    dao.get_messages_by_conversation.return_value = expected

    got = svc.get_messages(5)
    assert got == expected
    dao.get_messages_by_conversation.assert_called_once_with(5)


def test_get_messages_invalid_conversation_id():
    svc = MessageService(MagicMock())
    with pytest.raises(ValueError):
        svc.get_messages(-1)


def test_get_message_by_id_ok():
    dao = MagicMock()
    svc = MessageService(dao)
    m = make_message(id_message=77)
    dao.get_by_id.return_value = m

    got = svc.get_message_by_id(77)
    assert got is m
    dao.get_by_id.assert_called_once_with(77)


def test_get_message_by_id_invalid():
    svc = MessageService(MagicMock())
    with pytest.raises(ValueError):
        svc.get_message_by_id(-5)


def test_delete_all_messages_by_conversation_ok():
    dao = MagicMock()
    svc = MessageService(dao)
    svc.delete_all_messages_by_conversation(9)
    dao.delete_by_conversation.assert_called_once_with(9)


def test_delete_all_messages_by_conversation_invalid():
    svc = MessageService(MagicMock())
    with pytest.raises(ValueError):
        svc.delete_all_messages_by_conversation(-1)


def test_check_conversation_exists_true_when_count_nonnegative():
    dao = MagicMock()
    dao.count_messages_by_conversation.return_value = 0
    svc = MessageService(dao)
    assert svc.check_conversation_exists(1) is True


# =========================
# get_last_message
# =========================
def test_get_last_message_ok():
    dao = MagicMock()
    svc = MessageService(dao)
    last = make_message(id_message=10)
    dao.get_last_message.return_value = last

    got = svc.get_last_message(4)
    assert got is last
    dao.get_last_message.assert_called_once_with(4)


def test_get_last_message_invalid():
    svc = MessageService(MagicMock())
    with pytest.raises(ValueError):
        svc.get_last_message(-1)


# =========================
# validate_message_content
# =========================
def test_validate_message_content_ok_and_strip():
    svc = MessageService(MagicMock())
    assert svc.validate_message_content("  Bonjour  ") is True


@pytest.mark.parametrize(
    "bad",
    [
        "", "   ", "\x00",
        "<script>", "javascript:", "data:", "vbscript:",
        "onclick=", "onerror=",
        "--", "/*", "*/", "@@",
    ],
)
def test_validate_message_content_bad_patterns(bad):
    svc = MessageService(MagicMock())
    with pytest.raises(ValueError):
        svc.validate_message_content(bad)


def test_validate_message_content_too_long():
    svc = MessageService(MagicMock())
    with pytest.raises(ValueError):
        svc.validate_message_content("x" * 5001)


# =========================
# send_agent_message
# =========================
def test_send_agent_message_success():
    dao = MagicMock()
    svc = MessageService(dao)
    created = make_message(id_message=5, id_user=0, is_from_agent=True, text="bot")
    dao.create.return_value = created

    got = svc.send_agent_message(7, "bot")
    assert got is created
    dao.create.assert_called_once()
    # s'assure que l'objet envoyé au DAO est bien un message d'agent
    sent = dao.create.call_args.args[0]
    assert sent.is_from_agent is True
    assert sent.id_user == 0


# =========================
# pagination / count / search / date_range
# =========================
def test_get_messages_paginated_ok():
    dao = MagicMock()
    svc = MessageService(dao)
    svc.get_messages_paginated(3, page=2, per_page=10)
    dao.get_messages_by_conversation_paginated.assert_called_once_with(3, 2, 10)


def test_get_messages_paginated_invalid_page():
    svc = MessageService(MagicMock())
    with pytest.raises(ValueError):
        svc.get_messages_paginated(3, page=0, per_page=50)


def test_count_messages_delegates():
    dao = MagicMock()
    dao.count_messages_by_conversation.return_value = 12
    svc = MessageService(dao)
    assert svc.count_messages(8) == 12
    dao.count_messages_by_conversation.assert_called_once_with(8)


def test_search_messages_requires_keyword_and_strips():
    dao = MagicMock()
    svc = MessageService(dao)
    with pytest.raises(ValueError):
        svc.search_messages(1, "   ")

    svc.search_messages(1, "  archi  ")
    dao.search_messages.assert_called_once_with(1, "archi")


def test_get_messages_by_date_range_delegates():
    dao = MagicMock()
    svc = MessageService(dao)
    start = datetime.datetime(2025, 1, 1)
    end = datetime.datetime(2025, 1, 31)
    svc.get_messages_by_date_range(2, start, end)
    dao.get_messages_by_date_range.assert_called_once_with(2, start, end)


# =========================
# update / delete message
# =========================
def test_update_message_success():
    dao = MagicMock()
    svc = MessageService(dao)

    # message existant
    existing = make_message(id_message=50, text="old")
    dao.get_by_id.return_value = existing
    dao.update.return_value = True

    ok = svc.update_message(50, "new content!")
    assert ok is True
    dao.get_by_id.assert_called_once_with(50)
    dao.update.assert_called_once()
    assert existing.message == "new content!"


def test_update_message_not_found():
    dao = MagicMock()
    svc = MessageService(dao)
    dao.get_by_id.return_value = None
    with pytest.raises(ValueError):
        svc.update_message(99, "content")


def test_delete_message_ok_and_invalid():
    dao = MagicMock()
    svc = MessageService(dao)

    dao.delete_by_id.return_value = True
    assert svc.delete_message(10) is True
    dao.delete_by_id.assert_called_with(10)

    with pytest.raises(ValueError):
        svc.delete_message(-1)
