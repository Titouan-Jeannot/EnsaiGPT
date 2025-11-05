from unittest.mock import MagicMock, patch

from src.ObjetMetier.Collaboration import Collaboration
from src.Service.CollaborationService import CollaborationService


class TestCollaborationService:
    # --- Vérification des rôles ---

    def test_is_admin_true(self):
        with (
            patch("src.Service.CollaborationService.CollaborationDAO") as MockCollabDAO,
            patch("src.Service.CollaborationService.UserDAO"),
            patch("src.Service.CollaborationService.ConversationDAO"),
        ):
            mock_dao = MagicMock()
            MockCollabDAO.return_value = mock_dao
            mock_dao.find_by_conversation_and_user.return_value = Collaboration(1, 10, 100, "admin")

            service = CollaborationService()
            assert service.is_admin(100, 10) is True

    def test_is_writer_false(self):
        with (
            patch("src.Service.CollaborationService.CollaborationDAO") as MockCollabDAO,
            patch("src.Service.CollaborationService.UserDAO"),
            patch("src.Service.CollaborationService.ConversationDAO"),
        ):
            mock_dao = MagicMock()
            MockCollabDAO.return_value = mock_dao
            mock_dao.find_by_conversation_and_user.return_value = None

            service = CollaborationService()
            assert service.is_writer(100, 10) is False

    def test_is_viewer_true(self):
        with (
            patch("src.Service.CollaborationService.CollaborationDAO") as MockCollabDAO,
            patch("src.Service.CollaborationService.UserDAO"),
            patch("src.Service.CollaborationService.ConversationDAO"),
        ):
            mock_dao = MagicMock()
            MockCollabDAO.return_value = mock_dao
            mock_dao.find_by_conversation_and_user.return_value = Collaboration(
                1, 10, 100, "viewer"
            )

            service = CollaborationService()
            assert service.is_viewer(100, 10) is True

    # --- Création d’une collaboration ---

    def test_create_collab_success(self):
        with (
            patch("src.Service.CollaborationService.CollaborationDAO") as MockCollabDAO,
            patch("src.Service.CollaborationService.UserDAO") as MockUserDAO,
            patch("src.Service.CollaborationService.ConversationDAO") as MockConvDAO,
        ):
            mock_collab_dao = MagicMock()
            mock_user_dao = MagicMock()
            mock_conv_dao = MagicMock()
            MockCollabDAO.return_value = mock_collab_dao
            MockUserDAO.return_value = mock_user_dao
            MockConvDAO.return_value = mock_conv_dao

            # Config mocks
            mock_user_dao.read.return_value = True
            mock_conv_dao.read.return_value = True
            mock_collab_dao.find_by_conversation_and_user.return_value = None
            mock_collab_dao.create.return_value = True

            service = CollaborationService()
            result = service.create_collab(100, 10, "writer")

            assert result is True
            mock_collab_dao.create.assert_called_once()

    def test_create_collab_invalid_role(self):
        with (
            patch("src.Service.CollaborationService.CollaborationDAO") as MockCollabDAO,
            patch("src.Service.CollaborationService.UserDAO") as MockUserDAO,
            patch("src.Service.CollaborationService.ConversationDAO") as MockConvDAO,
        ):
            mock_collab_dao = MagicMock()
            mock_user_dao = MagicMock()
            mock_conv_dao = MagicMock()
            MockCollabDAO.return_value = mock_collab_dao
            MockUserDAO.return_value = mock_user_dao
            MockConvDAO.return_value = mock_conv_dao

            mock_user_dao.read.return_value = True
            mock_conv_dao.read.return_value = True

            service = CollaborationService()
            result = service.create_collab(100, 10, "INVALID_ROLE")

            assert result is False  # Exception attrapée => False

    def test_create_collab_already_exists(self):
        with (
            patch("src.Service.CollaborationService.CollaborationDAO") as MockCollabDAO,
            patch("src.Service.CollaborationService.UserDAO") as MockUserDAO,
            patch("src.Service.CollaborationService.ConversationDAO") as MockConvDAO,
        ):
            mock_collab_dao = MagicMock()
            MockCollabDAO.return_value = mock_collab_dao
            MockUserDAO.return_value = MagicMock(read=lambda x: True)
            MockConvDAO.return_value = MagicMock(read=lambda x: True)

            mock_collab_dao.find_by_conversation_and_user.return_value = Collaboration(
                1, 10, 100, "writer"
            )

            service = CollaborationService()
            result = service.create_collab(100, 10, "writer")

            assert result is False  # car collaboration déjà existante

    # --- Ajout direct d’une collaboration ---

    def test_add_collaboration(self):
        with (
            patch("src.Service.CollaborationService.CollaborationDAO") as MockCollabDAO,
            patch("src.Service.CollaborationService.UserDAO"),
            patch("src.Service.CollaborationService.ConversationDAO"),
        ):
            mock_collab_dao = MagicMock()
            MockCollabDAO.return_value = mock_collab_dao
            mock_collab_dao.create.return_value = True

            service = CollaborationService()
            collab = Collaboration(1, 10, 100, "writer")

            result = service.add_collaboration(collab)

            assert result is True
            mock_collab_dao.create.assert_called_once_with(collab)

    # --- Listing des collaborateurs ---

    def test_list_collaborators(self):
        with (
            patch("src.Service.CollaborationService.CollaborationDAO") as MockCollabDAO,
            patch("src.Service.CollaborationService.UserDAO"),
            patch("src.Service.CollaborationService.ConversationDAO"),
        ):
            mock_collab_dao = MagicMock()
            MockCollabDAO.return_value = mock_collab_dao
            mock_collab_dao.find_by_conversation.return_value = [
                Collaboration(1, 10, 100, "admin"),
                Collaboration(2, 10, 101, "writer"),
            ]

            service = CollaborationService()
            result = service.list_collaborators(10)

            assert len(result) == 2
            assert result[0].role == "admin"
            assert result[1].id_user == 101

    # --- Suppression et mise à jour ---

    def test_delete_collaborator(self):
        with (
            patch("src.Service.CollaborationService.CollaborationDAO") as MockCollabDAO,
            patch("src.Service.CollaborationService.UserDAO"),
            patch("src.Service.CollaborationService.ConversationDAO"),
        ):
            mock_collab_dao = MagicMock()
            MockCollabDAO.return_value = mock_collab_dao
            mock_collab_dao.delete_by_conversation_and_user.return_value = True

            service = CollaborationService()
            result = service.delete_collaborator(10, 100)

            assert result is True

    def test_change_role_success(self):
        with (
            patch("src.Service.CollaborationService.CollaborationDAO") as MockCollabDAO,
            patch("src.Service.CollaborationService.UserDAO"),
            patch("src.Service.CollaborationService.ConversationDAO"),
        ):
            mock_collab_dao = MagicMock()
            MockCollabDAO.return_value = mock_collab_dao
            collab = Collaboration(1, 10, 100, "writer")
            mock_collab_dao.find_by_conversation_and_user.return_value = collab
            mock_collab_dao.update_role.return_value = True

            service = CollaborationService()
            assert service.change_role(10, 100, "admin") is True

    def test_change_role_not_found(self):
        with (
            patch("src.Service.CollaborationService.CollaborationDAO") as MockCollabDAO,
            patch("src.Service.CollaborationService.UserDAO"),
            patch("src.Service.CollaborationService.ConversationDAO"),
        ):
            mock_collab_dao = MagicMock()
            MockCollabDAO.return_value = mock_collab_dao
            mock_collab_dao.find_by_conversation_and_user.return_value = None

            service = CollaborationService()
            assert service.change_role(10, 100, "admin") is False

    # --- Vérification token ---

    def test_verify_token_collaboration_success(self):
        with (
            patch("src.Service.CollaborationService.CollaborationDAO"),
            patch("src.Service.CollaborationService.UserDAO"),
            patch("src.Service.CollaborationService.ConversationDAO") as MockConvDAO,
        ):
            mock_conv_dao = MagicMock()
            MockConvDAO.return_value = mock_conv_dao
            mock_conv_dao.read.return_value = MagicMock(
                token_viewer="token123", token_writter="token456"
            )

            service = CollaborationService()
            assert service.verify_token_collaboration(10, "token123") is True
            assert service.verify_token_collaboration(10, "token456") is True
            assert service.verify_token_collaboration(10, "invalid") is False

    def test_verify_token_collaboration_invalid_conversation(self):
        with (
            patch("src.Service.CollaborationService.CollaborationDAO"),
            patch("src.Service.CollaborationService.UserDAO"),
            patch("src.Service.CollaborationService.ConversationDAO") as MockConvDAO,
        ):
            mock_conv_dao = MagicMock()
            MockConvDAO.return_value = mock_conv_dao
            mock_conv_dao.read.return_value = None

            service = CollaborationService()
            assert service.verify_token_collaboration(10, "token123") is False
