from datetime import datetime, date
from unittest.mock import MagicMock, patch
import re
import pytest

from DAO.ConversationDAO import ConversationDAO
from ObjetMetier.Conversation import Conversation


def make_mock_db():
    """Construit une fausse connexion DB entièrement mockée (même pattern que Collaboration)."""
    mock_cursor = MagicMock()
    mock_connection = MagicMock()
    # context managers
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_instance = MagicMock()
    mock_db_instance.connection = mock_connection
    return mock_db_instance, mock_connection, mock_cursor


class TestConversationDAOUnit:
    @patch("DAO.ConversationDAO.DBConnection")
    def test_create_generates_tokens_and_returns_row(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        # Le DAO attend un dict avec ces clés au RETURNING
        mock_cur.fetchone.return_value = {
            "id_conversation": 42,
            "created_at": datetime(2025, 1, 1, 12, 0, 0),
            "token_viewer": "deadbeefdeadbeefdeadbeefdeadbeef",   # 32 hex
            "token_writter": "cafebabecafebabecafebabecafebabe",  # 32 hex
        }
        MockDB.return_value = mock_db

        dao = ConversationDAO()
        conv = Conversation(
            id_conversation=None,
            titre="Titre test",
            created_at=datetime.now(),
            setting_conversation="{}",
            token_viewer=None,
            token_writter=None,
            is_active=True,
        )

        out = dao.create(conv)

        # execute a été appelé avec INSERT et tokens (générés si None)
        sql, params = mock_cur.execute.call_args[0]
        assert "insert into conversation" in sql.lower()
        assert params["titre"] == "Titre test"
        assert params["settings"] == "{}"
        assert isinstance(params["token_viewer"], str) and len(params["token_viewer"]) == 32
        assert isinstance(params["token_writter"], str) and len(params["token_writter"]) == 32

        # Objet renvoyé complété avec le RETURNING
        assert out.id_conversation == 42
        assert out.created_at == mock_cur.fetchone.return_value["created_at"]
        assert re.fullmatch(r"[0-9a-f]{32}", out.token_viewer)
        assert re.fullmatch(r"[0-9a-f]{32}", out.token_writter)

        mock_conn.commit.assert_called_once()

    @patch("DAO.ConversationDAO.DBConnection")
    def test_create_raises_on_exception(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        mock_cur.execute.side_effect = Exception("DB error")
        MockDB.return_value = mock_db

        dao = ConversationDAO()
        conv = Conversation(None, "X", datetime.now(), "{}", None, None, True)

        with pytest.raises(Exception):
            dao.create(conv)

    @patch("DAO.ConversationDAO.DBConnection")
    def test_read_success(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        mock_cur.fetchone.return_value = {
            "id_conversation": 7,
            "titre": "Lu",
            "created_at": datetime(2025, 2, 2, 10, 0, 0),
            "settings_conversation": "{}",
            "token_viewer": "a" * 32,
            "token_writter": "b" * 32,
            "is_active": True,
        }
        MockDB.return_value = mock_db

        dao = ConversationDAO()
        conv = dao.read(7)

        assert conv is not None
        assert conv.id_conversation == 7
        assert conv.titre == "Lu"
        assert conv.setting_conversation == "{}"
        assert conv.token_viewer == "a" * 32
        # Vérifie la requête paramétrée
        sql, params = mock_cur.execute.call_args[0]
        assert "where id_conversation = %(id_conversation)s" in sql.lower()
        assert params["id_conversation"] == 7

    @patch("DAO.ConversationDAO.DBConnection")
    def test_read_none_when_absent(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        mock_cur.fetchone.return_value = None
        MockDB.return_value = mock_db

        dao = ConversationDAO()
        assert dao.read(999) is None

    @patch("DAO.ConversationDAO.DBConnection")
    def test_update_title_success(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        mock_cur.rowcount = 1
        MockDB.return_value = mock_db

        dao = ConversationDAO()
        ok = dao.update_title(5, "Nouveau titre")

        assert ok is True
        mock_conn.commit.assert_called_once()
        sql, params = mock_cur.execute.call_args[0]
        assert "update conversation" in sql.lower()
        assert params["id_conversation"] == 5
        assert params["titre"] == "Nouveau titre"

    @patch("DAO.ConversationDAO.DBConnection")
    def test_set_active_success(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        mock_cur.rowcount = 1
        MockDB.return_value = mock_db

        dao = ConversationDAO()
        ok = dao.set_active(5, False)
        assert ok is True
        mock_conn.commit.assert_called_once()

    @patch("DAO.ConversationDAO.DBConnection")
    def test_delete_success(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        mock_cur.rowcount = 1
        MockDB.return_value = mock_db

        dao = ConversationDAO()
        ok = dao.delete(12)
        assert ok is True
        mock_conn.commit.assert_called_once()

    @patch("DAO.ConversationDAO.DBConnection")
    def test_get_conversations_by_user(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        mock_cur.fetchall.return_value = [
            {
                "id_conversation": 1,
                "titre": "A",
                "created_at": datetime(2025, 1, 1, 10, 0, 0),
                "settings_conversation": "{}",
                "token_viewer": "a" * 32,
                "token_writter": "b" * 32,
                "is_active": True,
            },
            {
                "id_conversation": 2,
                "titre": "B",
                "created_at": datetime(2025, 1, 2, 10, 0, 0),
                "settings_conversation": "{}",
                "token_viewer": "c" * 32,
                "token_writter": "d" * 32,
                "is_active": True,
            },
        ]
        MockDB.return_value = mock_db

        dao = ConversationDAO()
        lst = dao.get_conversations_by_user(123)
        assert len(lst) == 2
        assert lst[0].titre == "A"
        # Vérifie jointure + filtre
        sql, params = mock_cur.execute.call_args[0]
        assert "join collaboration" in sql.lower()
        assert params["user_id"] == 123

    @patch("DAO.ConversationDAO.DBConnection")
    def test_search_conversations_by_title(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        mock_cur.fetchall.return_value = [
            {
                "id_conversation": 3,
                "titre": "Titre magique",
                "created_at": datetime(2025, 1, 3, 10, 0, 0),
                "settings_conversation": "{}",
                "token_viewer": "e" * 32,
                "token_writter": "f" * 32,
                "is_active": True,
            }
        ]
        MockDB.return_value = mock_db

        dao = ConversationDAO()
        lst = dao.search_conversations_by_title(321, "magique")

        assert len(lst) == 1
        assert "magique" in lst[0].titre.lower()
        sql, params = mock_cur.execute.call_args[0]
        assert "ilike" in sql.lower()
        assert params["user_id"] == 321
        assert params["title"] == "%magique%"

    @patch("DAO.ConversationDAO.DBConnection")
    def test_get_conversations_by_date(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        mock_cur.fetchall.return_value = [
            {
                "id_conversation": 11,
                "titre": "X",
                "created_at": datetime(2025, 6, 1, 11, 0, 0),
                "settings_conversation": "{}",
                "token_viewer": "0" * 32,
                "token_writter": "1" * 32,
                "is_active": True,
            }
        ]
        MockDB.return_value = mock_db

        dao = ConversationDAO()
        day = datetime(2025, 6, 1, 23, 59, 59)
        lst = dao.get_conversations_by_date(9, day)

        assert len(lst) == 1
        assert lst[0].id_conversation == 11
        sql, params = mock_cur.execute.call_args[0]
        assert "date(c.created_at) = %(target_date)s" in sql.lower()
        assert params["user_id"] == 9
        assert isinstance(params["target_date"], date)

    @patch("DAO.ConversationDAO.DBConnection")
    def test_has_access_true_false(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        # d'abord True
        mock_cur.fetchone.return_value = (1,)
        MockDB.return_value = mock_db
        dao = ConversationDAO()
        assert dao.has_access(10, 100) is True

        # puis False
        mock_cur.fetchone.return_value = None
        assert dao.has_access(99, 999) is False

    @patch("DAO.ConversationDAO.DBConnection")
    def test_has_write_access_true_false(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        mock_cur.fetchone.return_value = (1,)
        MockDB.return_value = mock_db
        dao = ConversationDAO()
        assert dao.has_write_access(10, 100) is True

        mock_cur.fetchone.return_value = None
        assert dao.has_write_access(10, 101) is False

    @patch("DAO.ConversationDAO.DBConnection")
    def test_add_user_access_upsert(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        mock_cur.rowcount = 1
        MockDB.return_value = mock_db

        dao = ConversationDAO()
        dao.add_user_access(55, 777, can_write=True)

        sql, params = mock_cur.execute.call_args[0]
        assert "insert into collaboration" in sql.lower()
        assert params["role"] == "writer"
        mock_conn.commit.assert_called_once()
