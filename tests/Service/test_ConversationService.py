from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.ObjetMetier.Conversation import Conversation
from src.Service.ConversationService import ConversationService


def _make_conversation():
    return Conversation(
        id_conversation=1,
        titre="Titre",
        created_at=datetime.now(),
        setting_conversation="",
        token_viewer="token_v",
        token_writter="token_w",
        is_active=True,
    )


@patch("src.Service.ConversationService.secrets.token_urlsafe", side_effect=["viewer", "writer"])
def test_create_conversation_success(mock_token):
    conversation_dao = MagicMock()
    user_service = MagicMock()
    user_service.get_user_by_id.return_value = object()
    created_conversation = _make_conversation()
    conversation_dao.create.return_value = created_conversation
    collaboration_service = MagicMock()

    service = ConversationService(
        conversation_dao=conversation_dao,
        collaboration_service=collaboration_service,
        user_service=user_service,
    )

    result = service.create_conversation("  Mon titre  ", user_id=5, setting_conversation="contexte")

    assert result is created_conversation
    conversation_dao.create.assert_called_once()
    collaboration_service.create_collab.assert_called_once_with(5, 1, "admin")
    conversation_argument = conversation_dao.create.call_args[0][0]
    assert conversation_argument.titre == "Mon titre"
    assert conversation_argument.token_viewer == "viewer"
    assert conversation_argument.token_writter == "writer"


def test_create_conversation_user_missing():
    conversation_dao = MagicMock()
    user_service = MagicMock()
    user_service.get_user_by_id.return_value = None

    service = ConversationService(
        conversation_dao=conversation_dao,
        user_service=user_service,
    )

    with pytest.raises(ValueError):
        service.create_conversation("Titre", user_id=99)


def test_get_conversation_by_id_access_denied():
    conversation = _make_conversation()
    conversation_dao = MagicMock()
    conversation_dao.get_by_id.return_value = conversation
    conversation_dao.has_access.return_value = False

    service = ConversationService(conversation_dao=conversation_dao)

    with pytest.raises(ValueError):
        service.get_conversation_by_id(1, 2)


def test_get_conversation_by_id_success():
    conversation = _make_conversation()
    conversation_dao = MagicMock()
    conversation_dao.get_by_id.return_value = conversation
    conversation_dao.has_access.return_value = True

    service = ConversationService(conversation_dao=conversation_dao)

    assert service.get_conversation_by_id(1, 2) is conversation


def test_get_list_conv_by_title_invalid():
    conversation_dao = MagicMock()

    service = ConversationService(conversation_dao=conversation_dao)

    with pytest.raises(ValueError):
        service.get_list_conv_by_title(1, "   ")


def test_get_list_conv_success():
    conversation_dao = MagicMock()
    conversation_dao.get_conversations_by_user.return_value = ["conv"]

    service = ConversationService(conversation_dao=conversation_dao)

    assert service.get_list_conv(1) == ["conv"]


def test_get_list_conv_by_date_success():
    conversation_dao = MagicMock()
    expected = ["conv"]
    conversation_dao.get_conversations_by_date.return_value = expected

    service = ConversationService(conversation_dao=conversation_dao)

    assert service.get_list_conv_by_date(1, datetime.now()) is expected


def test_modify_title_requires_admin():
    conversation_dao = MagicMock()
    collab_service = MagicMock()
    collab_service.is_admin.return_value = False

    service = ConversationService(
        conversation_dao=conversation_dao,
        collaboration_service=collab_service,
    )

    with pytest.raises(ValueError):
        service.modify_title(1, 2, "Nouveau")


def test_modify_title_success():
    conversation_dao = MagicMock()
    conversation_dao.has_write_access.return_value = True
    conversation_dao.update_title.return_value = True
    collab_service = MagicMock()
    collab_service.is_admin.return_value = True

    service = ConversationService(
        conversation_dao=conversation_dao,
        collaboration_service=collab_service,
    )

    service.modify_title(1, 2, "Nouveau")
    conversation_dao.update_title.assert_called_once_with(1, "Nouveau")


def test_delete_conversation_success():
    conversation_dao = MagicMock()
    conversation_dao.has_write_access.return_value = True
    conversation_dao.delete.return_value = True
    collab_service = MagicMock()
    collab_service.is_admin.return_value = True
    message_service = MagicMock()

    service = ConversationService(
        conversation_dao=conversation_dao,
        collaboration_service=collab_service,
        message_service=message_service,
    )

    service.delete_conversation(10, 3)

    message_service.delete_all_messages_by_conversation.assert_called_once_with(10)
    conversation_dao.delete.assert_called_once_with(10)


def test_delete_conversation_without_rights():
    conversation_dao = MagicMock()
    conversation_dao.has_write_access.return_value = False
    collab_service = MagicMock()
    collab_service.is_admin.return_value = True

    service = ConversationService(
        conversation_dao=conversation_dao,
        collaboration_service=collab_service,
    )

    with pytest.raises(ValueError):
        service.delete_conversation(10, 3)


def test_archive_conversation_no_write_access():
    conversation_dao = MagicMock()
    conversation_dao.has_write_access.return_value = False

    service = ConversationService(conversation_dao=conversation_dao)

    with pytest.raises(ValueError):
        service.archive_conversation(1, 2)


def test_archive_conversation_failure():
    conversation_dao = MagicMock()
    conversation_dao.has_write_access.return_value = True
    conversation_dao.set_active.return_value = False

    service = ConversationService(conversation_dao=conversation_dao)

    with pytest.raises(ValueError):
        service.archive_conversation(1, 2)


def test_restore_conversation_success():
    conversation_dao = MagicMock()
    conversation_dao.has_write_access.return_value = True
    conversation_dao.set_active.return_value = True

    service = ConversationService(conversation_dao=conversation_dao)

    service.restore_conversation(1, 2)
    conversation_dao.set_active.assert_called_once_with(1, True)


def test_share_conversation_success():
    conversation_dao = MagicMock()
    conversation_dao.has_write_access.return_value = True
    conversation_dao.add_user_access.return_value = True
    collab_service = MagicMock()
    collab_service.is_admin.return_value = True
    user_service = MagicMock()
    user_service.get_user_by_id.return_value = object()

    service = ConversationService(
        conversation_dao=conversation_dao,
        collaboration_service=collab_service,
        user_service=user_service,
    )

    service.share_conversation(1, 2, 3, can_write=True)
    conversation_dao.add_user_access.assert_called_once_with(1, 3, True)


def test_share_conversation_failure():
    conversation_dao = MagicMock()
    conversation_dao.has_write_access.return_value = True
    conversation_dao.add_user_access.return_value = False
    collab_service = MagicMock()
    collab_service.is_admin.return_value = True
    user_service = MagicMock()
    user_service.get_user_by_id.return_value = object()

    service = ConversationService(
        conversation_dao=conversation_dao,
        collaboration_service=collab_service,
        user_service=user_service,
    )

    with pytest.raises(ValueError):
        service.share_conversation(1, 2, 3)


def test_share_conversation_user_missing():
    conversation_dao = MagicMock()
    conversation_dao.has_write_access.return_value = True
    collab_service = MagicMock()
    collab_service.is_admin.return_value = True
    user_service = MagicMock()
    user_service.get_user_by_id.return_value = None

    service = ConversationService(
        conversation_dao=conversation_dao,
        collaboration_service=collab_service,
        user_service=user_service,
    )

    with pytest.raises(ValueError):
        service.share_conversation(1, 2, 3)
