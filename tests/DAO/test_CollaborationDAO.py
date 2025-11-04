import pytest
from unittest.mock import MagicMock, patch
from src.DAO.CollaborationDAO import CollaborationDAO
from src.ObjetMetier.Collaboration import Collaboration


class TestCollaborationDAO:

    @patch("src.DAO.CollaborationDAO.DBConnection")
    def test_create_success(self, mock_db_connection):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id_collaboration": 1}

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_connection.return_value.connection.__enter__.return_value = mock_connection

        dao = CollaborationDAO()
        collaboration = Collaboration(0, 10, 100, "ADMIN")

        result = dao.create(collaboration)

        assert result is True
        assert collaboration.id_collaboration == 1
        mock_cursor.execute.assert_called_once()

    @patch("src.DAO.CollaborationDAO.DBConnection")
    def test_create_exception(self, mock_db_connection):
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("DB Error")

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_connection.return_value.connection.__enter__.return_value = mock_connection

        dao = CollaborationDAO()
        collaboration = Collaboration(0, 10, 100, "ADMIN")

        result = dao.create(collaboration)

        assert result is False

    @patch("src.DAO.CollaborationDAO.DBConnection")
    def test_read_found(self, mock_db_connection):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id_collaboration": 1,
            "id_conversation": 10,
            "id_user": 100,
            "role": "ADMIN",
        }

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_connection.return_value.connection.__enter__.return_value = mock_connection

        dao = CollaborationDAO()
        collab = dao.read(1)

        assert isinstance(collab, Collaboration)
        assert collab.id_collaboration == 1
        mock_cursor.execute.assert_called_once()

    @patch("src.DAO.CollaborationDAO.DBConnection")
    def test_read_not_found(self, mock_db_connection):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_connection.return_value.connection.__enter__.return_value = mock_connection

        dao = CollaborationDAO()
        collab = dao.read(999)

        assert collab is None
        mock_cursor.execute.assert_called_once()

    @patch("src.DAO.CollaborationDAO.DBConnection")
    def test_update_success(self, mock_db_connection):
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_connection.return_value.connection.__enter__.return_value = mock_connection

        dao = CollaborationDAO()
        collab = Collaboration(1, 10, 100, "WRITER")

        result = dao.update(collab)

        assert result is True
        mock_cursor.execute.assert_called_once()

    @patch("src.DAO.CollaborationDAO.DBConnection")
    def test_delete_success(self, mock_db_connection):
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_connection.return_value.connection.__enter__.return_value = mock_connection

        dao = CollaborationDAO()
        result = dao.delete(1)

        assert result is True
        mock_cursor.execute.assert_called_once()

    @patch("src.DAO.CollaborationDAO.DBConnection")
    def test_find_by_user(self, mock_db_connection):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id_collaboration": 1, "id_conversation": 10, "id_user": 100, "role": "ADMIN"},
            {"id_collaboration": 2, "id_conversation": 11, "id_user": 100, "role": "WRITER"},
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_connection.return_value.connection.__enter__.return_value = mock_connection

        dao = CollaborationDAO()
        collaborations = dao.find_by_user(100)

        assert len(collaborations) == 2
        assert collaborations[0].role == "ADMIN"
        assert collaborations[1].role == "WRITER"
        mock_cursor.execute.assert_called_once()

    @patch("src.DAO.CollaborationDAO.DBConnection")
    def test_update_role_success(self, mock_db_connection):
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_connection.return_value.connection.__enter__.return_value = mock_connection

        dao = CollaborationDAO()

        # Note : la méthode convertit le rôle via .strip().upper()
        result = dao.update_role(1, " writer ")

        assert result is True
        mock_cursor.execute.assert_called_once()

    @patch("src.DAO.CollaborationDAO.DBConnection")
    def test_update_role_invalid_role(self, mock_db_connection):
        dao = CollaborationDAO()

        # Rôle non valide → ValueError attendu
        with pytest.raises(ValueError):
            dao.update_role(1, "not_a_role")
