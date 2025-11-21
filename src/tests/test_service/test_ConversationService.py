import pytest
from unittest.mock import MagicMock

from Service.ConversationService import ConversationService
from ObjetMetier.Conversation import Conversation

# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------

@pytest.fixture
def mock_conversation_dao():
    return MagicMock()

@pytest.fixture
def mock_collab_service():
    svc = MagicMock()
    svc.is_admin.return_value = False
    return svc

@pytest.fixture
def mock_user_service():
    return MagicMock()

@pytest.fixture
def mock_message_service():
    return MagicMock()

@pytest.fixture
def conv_service(
    mock_conversation_dao,
    mock_collab_service,
    mock_user_service,
    mock_message_service,
):
    return ConversationService(
        conversation_dao=mock_conversation_dao,
        collaboration_service=mock_collab_service,
        user_service=mock_user_service,
        message_service=mock_message_service,
    )

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _make_conv(conv_id=1, title="Titre", settings="{}"):
    return Conversation(
        id_conversation=conv_id,
        titre=title,
        created_at=None,
        setting_conversation=settings,
        token_viewer="tv",
        token_writter="tw",
        is_active=True,
    )

# -------------------------------------------------------------------
# create_conversation
# -------------------------------------------------------------------

def test_create_conversation_ok(conv_service, mock_user_service, mock_conversation_dao, mock_collab_service):
    mock_user_service.get_user_by_id.return_value = object()

    def fake_create(conv, user_id):
        assert user_id == 123
        conv.id_conversation = 42
        return conv

    mock_conversation_dao.create.side_effect = fake_create

    conv = conv_service.create_conversation("  Ma conv  ", user_id=123, setting_conversation='{"a":1}')

    assert isinstance(conv, Conversation)
    assert conv.id_conversation == 42
    assert conv.titre == "Ma conv"

    mock_user_service.get_user_by_id.assert_called_once_with(123)
    mock_conversation_dao.create.assert_called_once()
    mock_collab_service.create_collab.assert_called_once_with(123, 42, "admin")

def test_create_conversation_user_not_found(conv_service, mock_user_service):
    mock_user_service.get_user_by_id.return_value = None
    with pytest.raises(ValueError, match="Utilisateur introuvable"):
        conv_service.create_conversation("Titre", user_id=999)

def test_create_conversation_invalid_title(conv_service, mock_user_service):
    mock_user_service.get_user_by_id.return_value = object()
    for bad in ["", "   "]:
        with pytest.raises(ValueError, match="Titre invalide"):
            conv_service.create_conversation(bad, user_id=1)

def test_create_conversation_no_user_service(mock_conversation_dao, mock_collab_service):
    svc = ConversationService(
        conversation_dao=mock_conversation_dao,
        collaboration_service=mock_collab_service,
        user_service=None,
        message_service=None,
    )

    def fake_create(conv, user_id):
        conv.id_conversation = 7
        return conv

    mock_conversation_dao.create.side_effect = fake_create

    conv = svc.create_conversation("Titre ok", user_id=1)
    assert conv.id_conversation == 7

# -------------------------------------------------------------------
# get_conversation_by_id
# -------------------------------------------------------------------

def test_get_conversation_by_id_ok(conv_service, mock_conversation_dao):
    conv = _make_conv(10)
    mock_conversation_dao.get_by_id.return_value = conv
    mock_conversation_dao.has_access.return_value = True

    got = conv_service.get_conversation_by_id(10, user_id=5)
    assert got is conv

def test_get_conversation_by_id_invalid(conv_service):
    with pytest.raises(ValueError, match="ID de conversation invalide"):
        conv_service.get_conversation_by_id(-1, 1)

def test_get_conversation_by_id_not_found(conv_service, mock_conversation_dao):
    mock_conversation_dao.get_by_id.return_value = None
    got = conv_service.get_conversation_by_id(999, 1)
    assert got is None

def test_get_conversation_by_id_no_access(conv_service, mock_conversation_dao):
    mock_conversation_dao.get_by_id.return_value = _make_conv(10)
    mock_conversation_dao.has_access.return_value = False
    with pytest.raises(ValueError, match="Accès non autorisé"):
        conv_service.get_conversation_by_id(10, 2)

# -------------------------------------------------------------------
# list / search
# -------------------------------------------------------------------

def test_get_list_conv(conv_service, mock_conversation_dao):
    convs = [_make_conv(1), _make_conv(2)]
    mock_conversation_dao.get_conversations_by_user.return_value = convs

    got = conv_service.get_list_conv(5)
    assert got == convs

def test_get_list_conv_by_date(conv_service, mock_conversation_dao):
    from datetime import datetime
    d = datetime(2025, 1, 1)
    convs = [_make_conv(1)]
    mock_conversation_dao.get_conversations_by_date.return_value = convs

    got = conv_service.get_list_conv_by_date(3, d)
    assert got == convs

def test_get_list_conv_by_title_ok(conv_service, mock_conversation_dao):
    convs = [_make_conv(1)]
    mock_conversation_dao.search_conversations_by_title.return_value = convs

    got = conv_service.get_list_conv_by_title(7, "  projet  ")
    assert got == convs
    mock_conversation_dao.search_conversations_by_title.assert_called_once_with(7, "projet")

def test_get_list_conv_by_title_invalid(conv_service):
    with pytest.raises(ValueError, match="Critère de recherche invalide"):
        conv_service.get_list_conv_by_title(1, "   ")

# -------------------------------------------------------------------
# modify_title
# -------------------------------------------------------------------

def test_modify_title_ok(conv_service, mock_collab_service, mock_conversation_dao):
    mock_collab_service.is_admin.return_value = True
    mock_conversation_dao.has_write_access.return_value = True

    conv_service.modify_title(10, 2, "  New  ")
    mock_conversation_dao.update_title.assert_called_once_with(10, "New")

def test_modify_title_not_admin(conv_service, mock_collab_service):
    mock_collab_service.is_admin.return_value = False
    with pytest.raises(ValueError, match="Droits d'administration requis"):
        conv_service.modify_title(10, 2, "Titre")

def test_modify_title_invalid_title(conv_service, mock_collab_service):
    mock_collab_service.is_admin.return_value = True
    for bad in ["", "   "]:
        with pytest.raises(ValueError, match="Nouveau titre invalide"):
            conv_service.modify_title(1, 2, bad)

def test_modify_title_no_write(conv_service, mock_collab_service, mock_conversation_dao):
    mock_collab_service.is_admin.return_value = True
    mock_conversation_dao.has_write_access.return_value = False
    with pytest.raises(ValueError, match="Droits d'écriture requis"):
        conv_service.modify_title(10, 2, "ok")

# -------------------------------------------------------------------
# delete_conversation
# -------------------------------------------------------------------

def test_delete_conversation_ok(conv_service, mock_collab_service, mock_conversation_dao, mock_message_service):
    mock_collab_service.is_admin.return_value = True
    mock_conversation_dao.has_write_access.return_value = True

    conv_service.delete_conversation(10, 3)

    mock_message_service.delete_all_messages_by_conversation.assert_called_once_with(10)
    mock_conversation_dao.delete.assert_called_once_with(10)

def test_delete_conversation_not_admin(conv_service, mock_collab_service):
    mock_collab_service.is_admin.return_value = False
    with pytest.raises(PermissionError, match="Droits d'administration requis"):
        conv_service.delete_conversation(10, 3)

def test_delete_conversation_no_write(conv_service, mock_collab_service, mock_conversation_dao):
    mock_collab_service.is_admin.return_value = True
    mock_conversation_dao.has_write_access.return_value = False
    with pytest.raises(ValueError, match="Droits d'écriture requis"):
        conv_service.delete_conversation(10, 3)

# -------------------------------------------------------------------
# archive / restore
# -------------------------------------------------------------------

def test_archive_conversation_ok(conv_service, mock_collab_service, mock_conversation_dao):
    mock_collab_service.is_admin.return_value = True
    mock_conversation_dao.has_write_access.return_value = True

    conv_service.archive_conversation(5, 1)
    mock_conversation_dao.set_active.assert_called_once_with(5, False)

def test_archive_conversation_not_admin(conv_service, mock_collab_service):
    mock_collab_service.is_admin.return_value = False
    with pytest.raises(PermissionError, match="Droits d'administration requis"):
        conv_service.archive_conversation(5, 1)

def test_archive_conversation_no_write(conv_service, mock_collab_service, mock_conversation_dao):
    mock_collab_service.is_admin.return_value = True
    mock_conversation_dao.has_write_access.return_value = False
    with pytest.raises(ValueError, match="Droits d'écriture requis"):
        conv_service.archive_conversation(5, 1)

def test_restore_conversation_ok(conv_service, mock_collab_service, mock_conversation_dao):
    mock_collab_service.is_admin.return_value = True
    mock_conversation_dao.has_write_access.return_value = True

    conv_service.restore_conversation(8, 2)
    mock_conversation_dao.set_active.assert_called_once_with(8, True)

# -------------------------------------------------------------------
# share_conversation
# -------------------------------------------------------------------

def test_share_conversation_ok(conv_service, mock_collab_service, mock_conversation_dao, mock_user_service):
    mock_collab_service.is_admin.return_value = True
    mock_conversation_dao.has_write_access.return_value = True
    mock_user_service.get_user_by_id.return_value = object()

    conv_service.share_conversation(10, 1, 99, can_write=True)
    mock_conversation_dao.add_user_access.assert_called_once_with(10, 99, True)

def test_share_conversation_not_admin(conv_service, mock_collab_service):
    mock_collab_service.is_admin.return_value = False
    with pytest.raises(PermissionError, match="Droits d'administration requis"):
        conv_service.share_conversation(10, 1, 99)

def test_share_conversation_no_write(conv_service, mock_collab_service, mock_conversation_dao):
    mock_collab_service.is_admin.return_value = True
    mock_conversation_dao.has_write_access.return_value = False

    with pytest.raises(ValueError, match="Droits d'écriture requis"):
        conv_service.share_conversation(10, 1, 99)

def test_share_conversation_user_not_found(conv_service, mock_collab_service, mock_conversation_dao, mock_user_service):
    mock_collab_service.is_admin.return_value = True
    mock_conversation_dao.has_write_access.return_value = True
    mock_user_service.get_user_by_id.return_value = None

    with pytest.raises(ValueError, match="Utilisateur cible introuvable"):
        conv_service.share_conversation(10, 1, 2)

def test_share_conversation_no_user_service(mock_conversation_dao, mock_collab_service):
    svc = ConversationService(
        conversation_dao=mock_conversation_dao,
        collaboration_service=mock_collab_service,
        user_service=None,
        message_service=None,
    )
    mock_collab_service.is_admin.return_value = True
    mock_conversation_dao.has_write_access.return_value = True

    svc.share_conversation(10, 1, 2, can_write=False)
    mock_conversation_dao.add_user_access.assert_called_once_with(10, 2, False)

# -------------------------------------------------------------------
# update_setting
# -------------------------------------------------------------------

def test_update_setting_ok(conv_service, mock_collab_service, mock_conversation_dao):
    mock_collab_service.is_admin.return_value = True
    mock_conversation_dao.has_write_access.return_value = True

    conv_service.update_conversation_setting(11, 3, '{"lang":"fr"}')
    mock_conversation_dao.update_setting.assert_called_once_with(11, '{"lang":"fr"}')

def test_update_setting_not_admin(conv_service, mock_collab_service):
    mock_collab_service.is_admin.return_value = False
    with pytest.raises(PermissionError, match="Droits d'administration requis"):
        conv_service.update_conversation_setting(11, 3, "x")

def test_update_setting_no_write(conv_service, mock_collab_service, mock_conversation_dao):
    mock_collab_service.is_admin.return_value = True
    mock_conversation_dao.has_write_access.return_value = False
    with pytest.raises(ValueError, match="Droits d'écriture requis"):
        conv_service.update_conversation_setting(11, 3, "x")
