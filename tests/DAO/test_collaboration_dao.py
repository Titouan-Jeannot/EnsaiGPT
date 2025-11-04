import pytest

from src.DAO.CollaborationDAO import CollaborationDAO
from src.ObjetMetier.Collaboration import Collaboration


def build_collaboration(conversation_id: int = 1, user_id: int = 1) -> Collaboration:
    return Collaboration(
        id_collaboration=None,
        id_conversation=conversation_id,
        id_user=user_id,
        role="ADMIN",
    )


def test_collaboration_create_and_list(collaboration_dao: CollaborationDAO):
    collab = collaboration_dao.create(build_collaboration())
    assert collab.id_collaboration is not None
    assert collaboration_dao.list_by_conversation(1) == [collab]
    assert collaboration_dao.list_by_user(1) == [collab]


def test_duplicate_collaboration(collaboration_dao: CollaborationDAO):
    collaboration_dao.create(build_collaboration())
    with pytest.raises(ValueError):
        collaboration_dao.create(build_collaboration())


def test_find_update_delete(collaboration_dao: CollaborationDAO):
    collab = collaboration_dao.create(build_collaboration())
    fetched = collaboration_dao.find_by_user_and_conversation(1, 1)
    assert fetched == collab
    collab.role = "WRITER"
    collaboration_dao.update(collab)
    assert collaboration_dao.find_by_user_and_conversation(1, 1).role == "WRITER"
    assert collaboration_dao.delete(collab.id_collaboration) is True
