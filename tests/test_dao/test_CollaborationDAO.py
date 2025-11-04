from unittest.mock import MagicMock, patch
<<<<<<< HEAD:tests/test_dao/test_CollaborationDAO.py
from DAO.CollaborationDAO import CollaborationDAO
from Objet_Metier.Collaboration import Collaboration
=======
from src.DAO.CollaborationDAO import CollaborationDAO
from src.ObjetMetier.Collaboration import Collaboration

>>>>>>> 4a539ddaa2b9966d5d5a471305e4498bcb32683a:tests/DAO/test_CollaborationDAO.py

class TestCollaborationDAO:

    @patch('src.DAO.CollaborationDAO.DBConnection')
    def test_create_success(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id_collaboration": 1}

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection

        mock_db_connection.return_value.connection = mock_connection

        dao = CollaborationDAO()
        collaboration = Collaboration(
            id_collaboration=0,
            id_conversation=10,
            id_user=100,
            role="ADMIN"
        )

        # Act
        result = dao.create(collaboration)

        # Assert
        assert result is True
        assert collaboration.id_collaboration == 1
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.CollaborationDAO.DBConnection')
    def test_create_exception(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("DB Error")

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection

        mock_db_connection.return_value.connection = mock_connection

        dao = CollaborationDAO()
        collaboration = Collaboration(0, 10, 100, "ADMIN")

        # Act
        result = dao.create(collaboration)

        # Assert
        assert result is False

    @patch('src.DAO.CollaborationDAO.DBConnection')
    def test_read_found(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id_collaboration": 1,
            "id_conversation": 10,
            "id_user": 100,
            "role": "ADMIN"
        }

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection

        mock_db_connection.return_value.connection = mock_connection

        dao = CollaborationDAO()

        # Act
        collaboration = dao.read(1)

        # Assert
        assert collaboration is not None
        assert collaboration.id_collaboration == 1
        assert collaboration.id_conversation == 10
        assert collaboration.id_user == 100
        assert collaboration.role == "ADMIN"
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.CollaborationDAO.DBConnection')
    def test_read_not_found(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection

        mock_db_connection.return_value.connection = mock_connection

        dao = CollaborationDAO()

        # Act
        collaboration = dao.read(999)

        # Assert
        assert collaboration is None
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.CollaborationDAO.DBConnection')
    def test_find_by_user(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id_collaboration": 1, "id_conversation": 10, "id_user": 100, "role": "ADMIN"},
            {"id_collaboration": 2, "id_conversation": 11, "id_user": 100, "role": "WRITER"}
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection

        mock_db_connection.return_value.connection = mock_connection

        dao = CollaborationDAO()

        # Act
        collaborations = dao.find_by_user(100)

        # Assert
        assert len(collaborations) == 2
        assert collaborations[0].id_collaboration == 1
        assert collaborations[0].role == "ADMIN"
        assert collaborations[1].id_collaboration == 2
        assert collaborations[1].role == "WRITER"
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.CollaborationDAO.DBConnection')
    def test_delete_success(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection

        mock_db_connection.return_value.connection = mock_connection

        dao = CollaborationDAO()

        # Act
        result = dao.delete(1)

        # Assert
        assert result is True
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.CollaborationDAO.DBConnection')
    def test_update_success(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection

        mock_db_connection.return_value.connection = mock_connection

        dao = CollaborationDAO()
        collaboration = Collaboration(1, 10, 100, "WRITER")

        # Act
        result = dao.update(collaboration)

        # Assert
        assert result is True
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.CollaborationDAO.DBConnection')
    def test_update_role_success(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection

        mock_db_connection.return_value.connection = mock_connection

        dao = CollaborationDAO()

        # Act
        result = dao.update_role(1, "writer")

        # Assert
        assert result is True
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.CollaborationDAO.DBConnection')
    def test_find_by_conversation(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id_collaboration": 1, "id_conversation": 10, "id_user": 100, "role": "ADMIN"},
            {"id_collaboration": 2, "id_conversation": 10, "id_user": 101, "role": "WRITER"}
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection

        mock_db_connection.return_value.connection = mock_connection

        dao = CollaborationDAO()

        # Act
        collaborations = dao.find_by_conversation(10)

        # Assert
        assert len(collaborations) == 2
        assert collaborations[0].id_conversation == 10
        assert collaborations[1].id_conversation == 10

    @patch('src.DAO.CollaborationDAO.DBConnection')
    def test_find_by_conversation_and_user(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id_collaboration": 1,
            "id_conversation": 10,
            "id_user": 100,
            "role": "ADMIN"
        }

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection

        mock_db_connection.return_value.connection = mock_connection

        dao = CollaborationDAO()

        # Act
        collaboration = dao.find_by_conversation_and_user(10, 100)

        # Assert
        assert collaboration is not None
        assert collaboration.id_conversation == 10
        assert collaboration.id_user == 100

    @patch('src.DAO.CollaborationDAO.DBConnection')
    def test_list_all(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id_collaboration": 1, "id_conversation": 10, "id_user": 100, "role": "ADMIN"},
            {"id_collaboration": 2, "id_conversation": 11, "id_user": 101, "role": "WRITER"}
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection

        mock_db_connection.return_value.connection = mock_connection

        dao = CollaborationDAO()

        # Act
        collaborations = dao.list_all()

        # Assert
        assert len(collaborations) == 2

    @patch('src.DAO.CollaborationDAO.DBConnection')
    def test_count_by_conversation(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"total": 3}

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection

        mock_db_connection.return_value.connection = mock_connection

        dao = CollaborationDAO()

        # Act
        count = dao.count_by_conversation(10)

        # Assert
        assert count == 3

    @patch('src.DAO.CollaborationDAO.DBConnection')
    def test_delete_by_conversation_and_user(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection

        mock_db_connection.return_value.connection = mock_connection

        dao = CollaborationDAO()

        # Act
        result = dao.delete_by_conversation_and_user(10, 100)

        # Assert
        assert result is True
