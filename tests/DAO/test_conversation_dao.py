from datetime import datetime

from src.DAO.ConversationDAO import ConversationDAO
from src.ObjetMetier.Conversation import Conversation


def build_conversation(title: str = "Projet") -> Conversation:
    return Conversation(
        id_conversation=None,
        titre=title,
        setting_conversation="",
        token_viewer="view",
        token_writter="write",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


def test_conversation_crud(conversation_dao: ConversationDAO):
    created = conversation_dao.create(build_conversation())
    assert created.id_conversation is not None
    fetched = conversation_dao.get_by_id(created.id_conversation)
    assert fetched == created
    created.titre = "Nouveau"
    conversation_dao.update(created)
    assert conversation_dao.get_by_id(created.id_conversation).titre == "Nouveau"
    assert conversation_dao.delete(created.id_conversation) is True


def test_list_helpers(conversation_dao: ConversationDAO):
    first = conversation_dao.create(build_conversation("Analyse"))
    second = conversation_dao.create(build_conversation("Développement"))
    ids = [conv.id_conversation for conv in (first, second)]
    assert len(conversation_dao.list_by_ids(ids)) == 2
    by_title = conversation_dao.list_by_title("dévelop")
    assert by_title == [second]
    by_date = conversation_dao.list_by_date(datetime(2024, 1, 1).date())
    assert len(by_date) == 2
