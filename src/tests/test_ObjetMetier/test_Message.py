import pytest
from datetime import datetime
from src.ObjetMetier.Message import Message


def test_message_initialization():
    msg = Message(
        id_message=1,
        id_conversation=10,
        id_user=100,
        datetime=datetime.now(),
        message="Bonjour",
        is_from_agent=True,
    )
    assert msg.id_message == 1
    assert msg.id_conversation == 10
    assert msg.id_user == 100
    assert isinstance(msg.datetime, datetime)
    assert msg.message == "Bonjour"
    assert msg.is_from_agent is True


def test_message_allows_none_id_message():
    # id_message peut être None selon ta doc -> ne doit PAS lever
    msg = Message(
        id_message=None,
        id_conversation=10,
        id_user=100,
        datetime=datetime.now(),
        message="Sans id_message",
        is_from_agent=False,
    )
    assert msg.id_message is None
    assert msg.is_from_agent is False


def test_message_init_type_errors():
    now = datetime.now()
    with pytest.raises(ValueError):
        Message(
            id_message="notint",
            id_conversation=10,
            id_user=100,
            datetime=now,
            message="x",
            is_from_agent=True,
        )
    with pytest.raises(ValueError):
        Message(
            id_message=1,
            id_conversation="notint",
            id_user=100,
            datetime=now,
            message="x",
            is_from_agent=True,
        )
    with pytest.raises(ValueError):
        Message(
            id_message=1,
            id_conversation=10,
            id_user="notint",
            datetime=now,
            message="x",
            is_from_agent=True,
        )
    with pytest.raises(ValueError):
        Message(
            id_message=1,
            id_conversation=10,
            id_user=100,
            datetime="notdatetime",
            message="x",
            is_from_agent=True,
        )
    with pytest.raises(ValueError):
        Message(
            id_message=1,
            id_conversation=10,
            id_user=100,
            datetime=now,
            message=123,
            is_from_agent=True,
        )
    with pytest.raises(ValueError):
        Message(
            id_message=1,
            id_conversation=10,
            id_user=100,
            datetime=now,
            message="x",
            is_from_agent="notbool",
        )


def test_message_equality():
    now = datetime.now()
    m1 = Message(1, 10, 100, now, "Hello", True)
    m2 = Message(1, 10, 100, now, "Hello", True)
    m3 = Message(2, 11, 101, now, "Different", False)

    assert m1 == m2
    assert m1 != m3


def test_message_edge_cases():
    # valeurs minimales
    m_min = Message(0, 0, 0, datetime.now(), "", False)
    assert m_min.id_message == 0
    assert m_min.id_conversation == 0
    assert m_min.id_user == 0
    assert m_min.message == ""
    assert m_min.is_from_agent is False

    # valeurs maximales raisonnables
    max_int = 2**31 - 1
    m_max = Message(max_int, max_int, max_int, datetime.now(), "A" * 1000, True)
    assert m_max.id_message == max_int
    assert m_max.id_conversation == max_int
    assert m_max.id_user == max_int
    assert m_max.message == "A" * 1000
    assert m_max.is_from_agent is True


def test_message_special_characters_in_message():
    msg_text = "Salut 😊🚀 #hashtag @mention"
    m = Message(1, 10, 100, datetime.now(), msg_text, True)
    assert m.message == msg_text


def test_message_whitespace_in_message():
    msg_text = "   Bonjour   "
    m = Message(1, 10, 100, datetime.now(), msg_text, False)
    assert m.message == msg_text


def test_message_future_datetime():
    future_date = datetime(3000, 1, 1)
    m = Message(1, 10, 100, future_date, "Future", True)
    assert m.datetime == future_date


def test_message_past_datetime():
    past_date = datetime(2000, 1, 1)
    m = Message(1, 10, 100, past_date, "Past", False)
    assert m.datetime == past_date


def test_message_str_contains_key_fields():
    now = datetime(2025, 1, 1, 12, 0, 0)
    m = Message(1, 10, 100, now, "Bonjour Bob !", True)
    s = str(m)
    assert isinstance(s, str)
    # On tolère différents formats, mais on veut au moins du contenu clé
    assert "Bonjour Bob" in s or "100" in s or "Agent" in s or "User" in s
