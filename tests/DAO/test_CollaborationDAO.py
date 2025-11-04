from unittest.mock import MagicMock, patch
from src.DAO.CollaborationDAO import CollaborationDAO
from src.ObjetMetier.Collaboration import Collaboration

class TestCollaborationDAO:

    @patch('src.DAO.Collaboration_DAO.DBConnection')
    def test_creer_succes(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id_collaboration": 1}

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_db_connection.return_value.connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_db_connection.return_value.connection.__exit__ = MagicMock(return_value=None)

        dao = CollaborationDAO()
        collaboration = Collaboration(
            id_collaboration=0,
            id_conversation=10,
            id_user=100,
            role="admin"
        )

        # Act
        result = dao.creer(collaboration)

        # Assert
        assert result is True
        assert collaboration.id_collaboration == 1
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.Collaboration_DAO.DBConnection')
    def test_creer_exception(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("DB Error")

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_db_connection.return_value.connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_db_connection.return_value.connection.__exit__ = MagicMock(return_value=None)

        dao = CollaborationDAO()
        collaboration = Collaboration(
            id_collaboration=0,
            id_conversation=10,
            id_user=100,
            role="admin"
        )

        # Act & Assert
        try:
            dao.creer(collaboration)
            assert False, "Une exception aurait dû être levée"
        except Exception as e:
            assert "DB Error" in str(e)

    @patch('src.DAO.Collaboration_DAO.DBConnection')
    def test_trouver_par_id_trouve(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id_collaboration": 1,
            "id_conversation": 10,
            "id_user": 100,
            "role": "admin"
        }

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_db_connection.return_value.connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_db_connection.return_value.connection.__exit__ = MagicMock(return_value=None)

        dao = CollaborationDAO()

        # Act
        collaboration = dao.trouver_par_id(1)

        # Assert
        assert collaboration is not None
        assert collaboration.id_collaboration == 1
        assert collaboration.id_conversation == 10
        assert collaboration.id_user == 100
        assert collaboration.role == "admin"
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.Collaboration_DAO.DBConnection')
    def test_trouver_par_id_non_trouve(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_db_connection.return_value.connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_db_connection.return_value.connection.__exit__ = MagicMock(return_value=None)

        dao = CollaborationDAO()

        # Act
        collaboration = dao.trouver_par_id(999)

        # Assert
        assert collaboration is None
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.Collaboration_DAO.DBConnection')
    def test_trouver_par_utilisateur_trouve(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id_collaboration": 1,
                "id_conversation": 10,
                "id_user": 100,
                "role": "admin"
            },
            {
                "id_collaboration": 2,
                "id_conversation": 11,
                "id_user": 100,
                "role": "writer"
            }
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_db_connection.return_value.connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_db_connection.return_value.connection.__exit__ = MagicMock(return_value=None)

        dao = CollaborationDAO()

        # Act
        collaborations = dao.trouver_par_utilisateur(100)

        # Assert
        assert len(collaborations) == 2
        assert collaborations[0].id_collaboration == 1
        assert collaborations[1].id_collaboration == 2
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.Collaboration_DAO.DBConnection')
    def test_supprimer_succes(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_db_connection.return_value.connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_db_connection.return_value.connection.__exit__ = MagicMock(return_value=None)

        dao = CollaborationDAO()
        collaboration = Collaboration(
            id_collaboration=1,
            id_conversation=10,
            id_user=100,
            role="admin"
        )

        # Act
        result = dao.supprimer(collaboration)

        # Assert
        assert result is True
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.Collaboration_DAO.DBConnection')
    def test_supprimer_non_trouve(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_db_connection.return_value.connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_db_connection.return_value.connection.__exit__ = MagicMock(return_value=None)

        dao = CollaborationDAO()
        collaboration = Collaboration(
            id_collaboration=999,
            id_conversation=10,
            id_user=100,
            role="admin"
        )

        # Act
        result = dao.supprimer(collaboration)

        # Assert
        assert result is False
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.Collaboration_DAO.DBConnection')
    def test_modifier_succes(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_db_connection.return_value.connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_db_connection.return_value.connection.__exit__ = MagicMock(return_value=None)

        dao = CollaborationDAO()
        collaboration = Collaboration(
            id_collaboration=1,
            id_conversation=10,
            id_user=100,
            role="writer"  # rôle modifié
        )

        # Act
        result = dao.modifier(collaboration)

        # Assert
        assert result is True
        mock_cursor.execute.assert_called_once()

    @patch('src.DAO.Collaboration_DAO.DBConnection')
    def test_modifier_role_succes(self, mock_db_connection):
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_db_connection.return_value.connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_db_connection.return_value.connection.__exit__ = MagicMock(return_value=None)

        dao = CollaborationDAO()

        # Act
        result = dao.modifier_role(1, "admin")

        # Assert
        assert result is True
        mock_cursor.execute.assert_called_once()
