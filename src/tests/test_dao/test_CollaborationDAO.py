from unittest.mock import MagicMock, patch

from src.DAO.CollaborationDAO import CollaborationDAO
from src.ObjetMetier.Collaboration import Collaboration


def make_mock_db():
    """Construit une fausse connexion DB entièrement mockée."""
    mock_cursor = MagicMock()
    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.__enter__.return_value = mock_connection

    mock_db_instance = MagicMock()
    mock_db_instance.connection = mock_connection
    return mock_db_instance, mock_connection, mock_cursor


class TestCollaborationDAO:
    def test_create_success(self):
        with patch("src.DAO.CollaborationDAO.DBConnection") as MockDAO:
            mock_db_instance, mock_connection, mock_cursor = make_mock_db()
            mock_cursor.fetchone.return_value = {"id_collaboration": 1}
            MockDAO.return_value = mock_db_instance

            dao = CollaborationDAO()
            collab = Collaboration(0, 10, 100, "ADMIN")

            result = dao.create(collab)

            assert result is True
            assert collab.id_collaboration == 1
            mock_cursor.execute.assert_called_once()

    def test_create_exception(self):
        with patch("src.DAO.CollaborationDAO.DBConnection") as MockDAO:
            mock_db_instance, mock_connection, mock_cursor = make_mock_db()
            mock_cursor.execute.side_effect = Exception("DB Error")
            MockDAO.return_value = mock_db_instance

            dao = CollaborationDAO()
            collab = Collaboration(0, 10, 100, "ADMIN")

            result = dao.create(collab)

            assert result is False

    def test_delete_success(self):
        with patch("src.DAO.CollaborationDAO.DBConnection") as MockDAO:
            mock_db_instance, mock_connection, mock_cursor = make_mock_db()
            mock_cursor.rowcount = 1
            MockDAO.return_value = mock_db_instance

            dao = CollaborationDAO()
            result = dao.delete(1)

            assert result is True
            mock_cursor.execute.assert_called_once()

    def test_update_success(self):
        with patch("src.DAO.CollaborationDAO.DBConnection") as MockDAO:
            mock_db_instance, mock_connection, mock_cursor = make_mock_db()
            mock_cursor.rowcount = 1
            MockDAO.return_value = mock_db_instance

            dao = CollaborationDAO()
            collab = Collaboration(1, 10, 100, "WRITER")

            result = dao.update(collab)

            assert result is True
            mock_cursor.execute.assert_called_once()

    def test_update_role_success(self):
        with patch("src.DAO.CollaborationDAO.DBConnection") as MockDAO:
            mock_db_instance, mock_connection, mock_cursor = make_mock_db()
            mock_cursor.rowcount = 1
            MockDAO.return_value = mock_db_instance

            dao = CollaborationDAO()
            result = dao.update_role(1, "writer")

            assert result is True
            mock_cursor.execute.assert_called_once()

    def test_find_by_conversation(self):
        with patch("src.DAO.CollaborationDAO.DBConnection") as MockDAO:
            mock_db_instance, mock_connection, mock_cursor = make_mock_db()
            mock_cursor.fetchall.return_value = [
                {"id_collaboration": 1, "id_conversation": 10, "id_user": 100, "role": "ADMIN"},
                {"id_collaboration": 2, "id_conversation": 10, "id_user": 101, "role": "WRITER"},
            ]
            MockDAO.return_value = mock_db_instance

            dao = CollaborationDAO()
            collaborations = dao.find_by_conversation(10)

            assert len(collaborations) == 2
            assert collaborations[0].id_conversation == 10
            assert collaborations[1].id_user == 101

    def test_find_by_conversation_and_user(self):
        with patch("src.DAO.CollaborationDAO.DBConnection") as MockDAO:
            mock_db_instance, mock_connection, mock_cursor = make_mock_db()
            mock_cursor.fetchone.return_value = {
                "id_collaboration": 1,
                "id_conversation": 10,
                "id_user": 100,
                "role": "admin",
            }
            MockDAO.return_value = mock_db_instance

            dao = CollaborationDAO()
            collab = dao.find_by_conversation_and_user(10, 100)

            assert collab is not None
            assert collab.id_user == 100
            assert collab.role == "admin"

    def test_list_all(self):
        with patch("src.DAO.CollaborationDAO.DBConnection") as MockDAO:
            mock_db_instance, mock_connection, mock_cursor = make_mock_db()
            mock_cursor.fetchall.return_value = [
                {"id_collaboration": 1, "id_conversation": 10, "id_user": 100, "role": "ADMIN"},
                {"id_collaboration": 2, "id_conversation": 11, "id_user": 101, "role": "WRITER"},
            ]
            MockDAO.return_value = mock_db_instance

            dao = CollaborationDAO()
            collaborations = dao.list_all()

            assert len(collaborations) == 2
            assert collaborations[0].role == "admin"

    def test_count_by_conversation(self):
        with patch("src.DAO.CollaborationDAO.DBConnection") as MockDAO:
            mock_db_instance, mock_connection, mock_cursor = make_mock_db()
            mock_cursor.fetchone.return_value = {"total": 3}
            MockDAO.return_value = mock_db_instance

            dao = CollaborationDAO()
            count = dao.count_by_conversation(10)

            assert count == 3

    def test_delete_by_conversation_and_user(self):
        with patch("src.DAO.CollaborationDAO.DBConnection") as MockDAO:
            mock_db_instance, mock_connection, mock_cursor = make_mock_db()
            mock_cursor.rowcount = 1
            MockDAO.return_value = mock_db_instance

            dao = CollaborationDAO()
            result = dao.delete_by_conversation_and_user(10, 100)

            assert result is True
