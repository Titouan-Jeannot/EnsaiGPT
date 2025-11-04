from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.DAO.ConversationDAO import ConversationDAO
from src.ObjetMetier.Conversation import Conversation
from src.Utils.Singleton import Singleton


def _reset_singleton():
    """Réinitialise le singleton ConversationDAO entre les tests."""
    Singleton._instances.pop(ConversationDAO, None)


def _build_conversation() -> Conversation:
    return Conversation(
        id_conversation=None,
        titre="Titre",
        created_at=datetime.now(),
        setting_conversation="",
        token_viewer="viewer",
        token_writter="writer",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def reset_singleton_fixture():
    _reset_singleton()
    yield
    _reset_singleton()


@patch("src.DAO.ConversationDAO.DBConnection")
def test_create_success(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {"id_conversation": 42}

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()
    conversation = _build_conversation()

    result = dao.create(conversation, user_id=1)

    assert result.id_conversation == 42
    mock_cursor.execute.assert_called_once()


@patch("src.DAO.ConversationDAO.DBConnection")
def test_create_failure(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("db error")

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    with pytest.raises(ValueError):
        dao.create(_build_conversation(), user_id=1)


@patch("src.DAO.ConversationDAO.DBConnection")
def test_get_by_id_found(mock_db_connection):
    now = datetime.now()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {
        "id_conversation": 1,
        "titre": "Test",
        "created_at": now,
        "setting_conversation": "param",
        "token_viewer": "tv",
        "token_writter": "tw",
        "is_active": True,
    }

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    conversation = dao.get_by_id(1)

    assert conversation is not None
    assert conversation.id_conversation == 1
    assert conversation.titre == "Test"


@patch("src.DAO.ConversationDAO.DBConnection")
def test_get_by_id_not_found(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    conversation = dao.get_by_id(99)

    assert conversation is None


@patch("src.DAO.ConversationDAO.DBConnection")
def test_update_title_success(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    assert dao.update_title(1, "Nouveau") is True


@patch("src.DAO.ConversationDAO.DBConnection")
def test_update_title_failure(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 0

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    assert dao.update_title(1, "Nouveau") is False


@patch("src.DAO.ConversationDAO.DBConnection")
def test_delete_success(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    assert dao.delete(1) is True


@patch("src.DAO.ConversationDAO.DBConnection")
def test_delete_failure(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 0

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    assert dao.delete(1) is False


@patch("src.DAO.ConversationDAO.DBConnection")
def test_has_access_true(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {"exists": 1}

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    assert dao.has_access(1, 2) is True


@patch("src.DAO.ConversationDAO.DBConnection")
def test_has_access_false(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    assert dao.has_access(1, 2) is False


@patch("src.DAO.ConversationDAO.DBConnection")
def test_has_write_access_roles(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.side_effect = [
        {"role": "ADMIN"},
        {"role": "writer"},
        None,
    ]

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    assert dao.has_write_access(1, 2) is True
    assert dao.has_write_access(1, 2) is True
    assert dao.has_write_access(1, 2) is False


@patch("src.DAO.ConversationDAO.DBConnection")
def test_add_user_access_insert(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    assert dao.add_user_access(1, 2, can_write=False) is True
    assert mock_cursor.execute.call_count == 2


@patch("src.DAO.ConversationDAO.DBConnection")
def test_add_user_access_update(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {"id_collaboration": 5}

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    assert dao.add_user_access(1, 2, can_write=True) is True
    assert mock_cursor.execute.call_count == 2


@patch("src.DAO.ConversationDAO.DBConnection")
def test_get_conversations_by_user(mock_db_connection):
    now = datetime.now()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            "id_conversation": 1,
            "titre": "Conv",
            "created_at": now,
            "setting_conversation": "",
            "token_viewer": "tv",
            "token_writter": "tw",
            "is_active": True,
        }
    ]

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    conversations = dao.get_conversations_by_user(1)

    assert len(conversations) == 1
    assert conversations[0].titre == "Conv"


@patch("src.DAO.ConversationDAO.DBConnection")
def test_get_conversations_by_date(mock_db_connection):
    now = datetime.now()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            "id_conversation": 1,
            "titre": "Conv",
            "created_at": now,
            "setting_conversation": "",
            "token_viewer": "tv",
            "token_writter": "tw",
            "is_active": True,
        }
    ]

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    conversations = dao.get_conversations_by_date(1, now)

    assert len(conversations) == 1


@patch("src.DAO.ConversationDAO.DBConnection")
def test_search_conversations_by_title(mock_db_connection):
    now = datetime.now()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            "id_conversation": 1,
            "titre": "Conv",
            "created_at": now,
            "setting_conversation": "",
            "token_viewer": "tv",
            "token_writter": "tw",
            "is_active": True,
        }
    ]

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    conversations = dao.search_conversations_by_title(1, "Conv")

    assert len(conversations) == 1


@patch("src.DAO.ConversationDAO.DBConnection")
def test_set_active_success(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    assert dao.set_active(1, True) is True


@patch("src.DAO.ConversationDAO.DBConnection")
def test_set_active_failure(mock_db_connection):
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 0

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_connection.return_value.connection = mock_connection

    dao = ConversationDAO()

    assert dao.set_active(1, False) is False
