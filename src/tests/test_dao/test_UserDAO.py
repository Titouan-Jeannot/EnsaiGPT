from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest

from psycopg2.errors import IntegrityError, DatabaseError

from src.DAO.UserDAO import UserDAO
from src.ObjetMetier.User import User


def make_mock_db():
    """Connexion DB entièrement mockée (pattern identique aux autres tests DAO)."""
    mock_cursor = MagicMock()
    mock_connection = MagicMock()
    # context managers
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_instance = MagicMock()
    mock_db_instance.connection = mock_connection
    return mock_db_instance, mock_connection, mock_cursor


def dummy_user(id_=None):
    return User(
        id=id_,
        username="john",
        nom="Doe",
        prenom="John",
        mail="john@example.com",
        password_hash="hash",
        salt="salt",
        sign_in_date=datetime(2025, 1, 1, 10, 0, 0),
        last_login=datetime(2025, 1, 2, 11, 0, 0),
        status="active",
        setting_param="{}",
    )


class TestUserDAOUnit:
    @patch("src.DAO.UserDAO.DBConnection")
    def test_create_success(self, MockDB):
        mock_db, mock_conn, mock_cur = make_mock_db()
        mock_cur.fetchone.return_value = {"id_user": 123}
        MockDB.return_value = mock_db

        dao = UserDAO()
        u = dummy_user()

        out = dao.create(u)

        assert out.id == 123
        # vérifie qu'on a bien passé tous les paramètres attendus
        sql, params = mock_cur.execute.call_args[0]
        assert "insert into users" in sql.lower()
        assert params["username"] == "john"
        assert params["nom"] == "Doe"
        mock_conn.commit.assert_not_called()  # commit géré par le context manager

    @patch("src.DAO.UserDAO.DBConnection")
    def test_create_integrity_error_raises_valueerror(self, MockDB):
        mock_db, _, mock_cur = make_mock_db()
        mock_cur.execute.side_effect = IntegrityError("dup")
        MockDB.return_value = mock_db

        dao = UserDAO()
        with pytest.raises(ValueError):
            dao.create(dummy_user())

    @patch("src.DAO.UserDAO.DBConnection")
    def test_create_database_error_bubbles(self, MockDB):
        mock_db, _, mock_cur = make_mock_db()
        mock_cur.execute.side_effect = DatabaseError("db down")
        MockDB.return_value = mock_db

        dao = UserDAO()
        with pytest.raises(DatabaseError):
            dao.create(dummy_user())

    @patch("src.DAO.UserDAO.DBConnection")
    def test_read_found(self, MockDB):
        mock_db, _, mock_cur = make_mock_db()
        mock_cur.fetchone.return_value = {
            "id_user": 7,
            "username": "alice",
            "nom": "Liddell",
            "prenom": "Alice",
            "mail": "alice@example.com",
            "password_hash": "h",
            "salt": "s",
            "sign_in_date": datetime(2025, 1, 1, 10, 0, 0),
            "last_login": datetime(2025, 1, 2, 11, 0, 0),
            "status": "active",
            "setting_param": "{}",
        }
        MockDB.return_value = mock_db

        dao = UserDAO()
        user = dao.read(7)

        assert user is not None
        assert user.id == 7
        assert user.username == "alice"
        sql, params = mock_cur.execute.call_args[0]
        assert "where id_user = %(id)s" in sql.lower()
        assert params["id"] == 7

    @patch("src.DAO.UserDAO.DBConnection")
    def test_read_none(self, MockDB):
        mock_db, _, mock_cur = make_mock_db()
        mock_cur.fetchone.return_value = None
        MockDB.return_value = mock_db

        dao = UserDAO()
        assert dao.read(999) is None

    @patch("src.DAO.UserDAO.DBConnection")
    def test_update_success(self, MockDB):
        mock_db, _, mock_cur = make_mock_db()
        mock_cur.rowcount = 1
        MockDB.return_value = mock_db

        dao = UserDAO()
        ok = dao.update(dummy_user(id_=5))
        assert ok is True

    @patch("src.DAO.UserDAO.DBConnection")
    def test_update_integrity_error_raises_valueerror(self, MockDB):
        mock_db, _, mock_cur = make_mock_db()
        mock_cur.execute.side_effect = IntegrityError("dup")
        MockDB.return_value = mock_db

        dao = UserDAO()
        with pytest.raises(ValueError):
            dao.update(dummy_user(id_=6))

    @patch("src.DAO.UserDAO.DBConnection")
    def test_update_database_error_bubbles(self, MockDB):
        mock_db, _, mock_cur = make_mock_db()
        mock_cur.execute.side_effect = DatabaseError("db")
        MockDB.return_value = mock_db

        dao = UserDAO()
        with pytest.raises(DatabaseError):
            dao.update(dummy_user(id_=6))

    @patch("src.DAO.UserDAO.DBConnection")
    def test_delete_success(self, MockDB):
        mock_db, _, mock_cur = make_mock_db()
        mock_cur.rowcount = 1
        MockDB.return_value = mock_db

        dao = UserDAO()
        assert dao.delete(10) is True

    @patch("src.DAO.UserDAO.DBConnection")
    def test_get_user_by_email_found(self, MockDB):
        mock_db, _, mock_cur = make_mock_db()
        mock_cur.fetchone.return_value = {
            "id_user": 9,
            "username": "bob",
            "nom": "Builder",
            "prenom": "Bob",
            "mail": "bob@example.com",
            "password_hash": "h",
            "salt": "s",
            "sign_in_date": datetime(2025, 1, 1, 10, 0, 0),
            "last_login": datetime(2025, 1, 2, 11, 0, 0),
            "status": "active",
            "setting_param": "{}",
        }
        MockDB.return_value = mock_db

        dao = UserDAO()
        u = dao.get_user_by_email("bob@example.com")
        assert u is not None and u.id == 9
        sql, params = mock_cur.execute.call_args[0]
        assert "where mail = %(email)s" in sql.lower()
        assert params["email"] == "bob@example.com"

    @patch("src.DAO.UserDAO.DBConnection")
    def test_get_user_by_email_none(self, MockDB):
        mock_db, _, mock_cur = make_mock_db()
        mock_cur.fetchone.return_value = None
        MockDB.return_value = mock_db

        dao = UserDAO()
        assert dao.get_user_by_email("nobody@example.com") is None

    @patch("src.DAO.UserDAO.DBConnection")
    def test_get_user_by_username_found(self, MockDB):
        mock_db, _, mock_cur = make_mock_db()
        mock_cur.fetchone.return_value = {
            "id_user": 4,
            "username": "eve",
            "nom": "Evans",
            "prenom": "Eve",
            "mail": "eve@example.com",
            "password_hash": "h",
            "salt": "s",
            "sign_in_date": datetime(2025, 1, 1, 10, 0, 0),
            "last_login": datetime(2025, 1, 2, 11, 0, 0),
            "status": "active",
            "setting_param": "{}",
        }
        MockDB.return_value = mock_db

        dao = UserDAO()
        u = dao.get_user_by_username("eve")
        assert u is not None and u.username == "eve"

    @patch("src.DAO.UserDAO.DBConnection")
    def test_get_user_by_username_none(self, MockDB):
        mock_db, _, mock_cur = make_mock_db()
        mock_cur.fetchone.return_value = None
        MockDB.return_value = mock_db

        dao = UserDAO()
        assert dao.get_user_by_username("ghost") is None
