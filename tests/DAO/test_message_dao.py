from datetime import datetime

from src.DAO.Message_DAO import MessageDAO
from src.ObjetMetier.Message import Message


def build_message(conversation_id: int = 1, user_id: int = 1, content: str = "Salut") -> Message:
    return Message(
        id_message=None,
        id_conversation=conversation_id,
        id_user=user_id,
        message=content,
        datetime_sent=datetime(2024, 1, 1, 12, 0, 0),
        is_from_agent=False,
    )


def test_message_crud(message_dao: MessageDAO):
    created = message_dao.create(build_message())
    assert created.id_message is not None
    assert message_dao.read(created.id_message) == created
    created.message = "Bonjour"
    message_dao.update(created)
    assert message_dao.read(created.id_message).message == "Bonjour"
    assert message_dao.delete(created.id_message) is True


def test_message_lists(message_dao: MessageDAO):
    first = message_dao.create(build_message())
    second = message_dao.create(build_message(content="Re"))
    other_conv = message_dao.create(build_message(conversation_id=2, user_id=1))
    assert message_dao.list_by_conversation(1) == [first, second]
    assert message_dao.list_by_user(1) == [first, second, other_conv]
    assert message_dao.delete_by_conversation(1) == 2
