import pytest
from unittest.mock import MagicMock
from Service.CollaborationService import CollaborationService
from ObjetMetier.Collaboration import Collaboration

@pytest.fixture
def service():
    s = CollaborationService()

    # mock DAO
    s.user_dao = MagicMock()
    s.conversation_dao = MagicMock()
    s.collab_dao = MagicMock()

    return s


# ----------------------------------------------------------
# TEST _normalize_role
# ----------------------------------------------------------

def test_normalize_role_valid(service):
    assert service._normalize_role("Admin") == "admin"
    assert service._normalize_role(" viewer ") == "viewer"

def test_normalize_role_invalid(service):
    with pytest.raises(ValueError):
        service._normalize_role("root")


# ----------------------------------------------------------
# TEST _require_collaboration
# ----------------------------------------------------------

def test_require_collaboration_ok(service):
    fake = Collaboration(id_user=1, id_conversation=2, role="admin")
    service.collab_dao.find_by_conversation_and_user.return_value = fake
    assert service._require_collaboration(2, 1) is fake

def test_require_collaboration_denied(service):
    service.collab_dao.find_by_conversation_and_user.return_value = None
    with pytest.raises(PermissionError):
        service._require_collaboration(10, 12)


# ----------------------------------------------------------
# TEST _require_admin
# ----------------------------------------------------------

def test_require_admin_ok(service):
    fake = Collaboration(id_user=1, id_conversation=2, role="admin")
    service.collab_dao.find_by_conversation_and_user.return_value = fake
    assert service._require_admin(2, 1) is fake

def test_require_admin_not_admin(service):
    fake = Collaboration(id_user=1, id_conversation=2, role="viewer")
    service.collab_dao.find_by_conversation_and_user.return_value = fake
    with pytest.raises(PermissionError):
        service._require_admin(2, 1)


# ----------------------------------------------------------
# TEST is_admin, is_writer, is_viewer, is_banni
# ----------------------------------------------------------

def test_roles_checks(service):
    c = Collaboration(id_user=1, id_conversation=2, role="writer")
    service.collab_dao.find_by_conversation_and_user.return_value = c

    assert service.is_writer(1, 2) is True
    assert service.is_admin(1, 2) is False
    assert service.is_viewer(1, 2) is False
    assert service.is_banni(1, 2) is False

    c2 = Collaboration(id_user=1, id_conversation=2, role="banni")
    service.collab_dao.find_by_conversation_and_user.return_value = c2
    assert service.is_banni(1, 2) is True


# ----------------------------------------------------------
# TEST create_collab
# ----------------------------------------------------------

def test_create_collab_success(service):
    service.user_dao.read.return_value = object()
    service.conversation_dao.read.return_value = object()
    service.collab_dao.find_by_conversation_and_user.return_value = None
    service.collab_dao.create.return_value = True

    ok = service.create_collab(1, 2, "writer")
    assert ok is True


def test_create_collab_existing(service):
    service.user_dao.read.return_value = object()
    service.conversation_dao.read.return_value = object()
    service.collab_dao.find_by_conversation_and_user.return_value = Collaboration(
        id_user=1, id_conversation=2, role="viewer"
    )

    ok = service.create_collab(1, 2, "writer")
    assert ok is False  # because an exception happens inside

def test_create_collab_invalid_role(service):
    service.user_dao.read.return_value = object()
    service.conversation_dao.read.return_value = object()
    service.collab_dao.find_by_conversation_and_user.return_value = None

    ok = service.create_collab(1, 2, "root")
    assert ok is False


# ----------------------------------------------------------
# TEST list_collaborators + list_collaborators_for_user
# ----------------------------------------------------------

def test_list_collaborators(service):
    fake_list = [
        Collaboration(id_user=1, id_conversation=2, role="admin"),
        Collaboration(id_user=3, id_conversation=2, role="viewer")
    ]
    service.collab_dao.find_by_conversation.return_value = fake_list
    assert service.list_collaborators(2) == fake_list


def test_list_collaborators_for_user_ok(service):
    service.collab_dao.find_by_conversation_and_user.return_value = Collaboration(
        id_user=99, id_conversation=2, role="viewer"
    )
    fake_list = [Collaboration(id_user=1, id_conversation=2, role="admin")]
    service.collab_dao.find_by_conversation.return_value = fake_list

    assert service.list_collaborators_for_user(2, 99) == fake_list


def test_list_collaborators_for_user_denied(service):
    service.collab_dao.find_by_conversation_and_user.return_value = None
    with pytest.raises(PermissionError):
        service.list_collaborators_for_user(2, 99)


# ----------------------------------------------------------
# TEST delete_collaborator
# ----------------------------------------------------------

def test_delete_collaborator_ok(service):
    # requester admin
    service.collab_dao.find_by_conversation_and_user.side_effect = [
        Collaboration(id_user=10, id_conversation=1, role="admin"),   # require_admin
        Collaboration(id_user=5, id_conversation=1, role="viewer"),   # target found
    ]
    service.collab_dao.delete_by_conversation_and_user.return_value = True

    ok = service.delete_collaborator(1, 5, 10)
    assert ok is True


def test_delete_collaborator_target_not_found(service):
    service.collab_dao.find_by_conversation_and_user.return_value = Collaboration(
        id_user=10, id_conversation=1, role="admin"
    )
    service.collab_dao.find_by_conversation_and_user.side_effect = [
        Collaboration(id_user=10, id_conversation=1, role="admin"),
        None
    ]

    with pytest.raises(ValueError):
        service.delete_collaborator(1, 99, 10)


def test_delete_collaborator_self_single_user(service):
    # admin deleting himself while he is the only collab
    service.collab_dao.find_by_conversation.return_value = [
        Collaboration(id_user=10, id_conversation=1, role="admin")
    ]

    service.collab_dao.find_by_conversation_and_user.side_effect = [
        Collaboration(id_user=10, id_conversation=1, role="admin"),
        Collaboration(id_user=10, id_conversation=1, role="admin"),
    ]

    with pytest.raises(ValueError):
        service.delete_collaborator(1, 10, 10)


# ----------------------------------------------------------
# TEST change_role
# ----------------------------------------------------------

def test_change_role_ok(service):
    service.collab_dao.find_by_conversation_and_user.side_effect = [
        Collaboration(id_user=10, id_conversation=1, role="admin"),
        Collaboration(id_user=5, id_conversation=1, role="viewer"),
    ]
    service.collab_dao.update_role.return_value = True

    ok = service.change_role(1, 5, "writer", 10)
    assert ok is True


def test_change_role_not_found(service):
    service.collab_dao.find_by_conversation_and_user.side_effect = [
        Collaboration(id_user=10, id_conversation=1, role="admin"),
        None
    ]
    with pytest.raises(ValueError):
        service.change_role(1, 5, "writer", 10)


def test_change_role_invalid_role(service):
    service.collab_dao.find_by_conversation_and_user.return_value = Collaboration(
        id_user=10, id_conversation=1, role="admin"
    )
    with pytest.raises(ValueError):
        service.change_role(1, 10, "root", 10)


def test_change_role_self_single_user(service):
    service.collab_dao.find_by_conversation.return_value = [
        Collaboration(id_user=10, id_conversation=1, role="admin")
    ]
    service.collab_dao.find_by_conversation_and_user.side_effect = [
        Collaboration(id_user=10, id_conversation=1, role="admin"),
        Collaboration(id_user=10, id_conversation=1, role="admin"),
    ]

    with pytest.raises(ValueError):
        service.change_role(1, 10, "viewer", 10)


# ----------------------------------------------------------
# TEST verify_token_collaboration
# ----------------------------------------------------------

def test_verify_token_collaboration_ok(service):
    conv = MagicMock()
    conv.token_viewer = "tv"
    conv.token_writter = "tw"

    service.conversation_dao.read.return_value = conv

    assert service.verify_token_collaboration(1, "tv") is True
    assert service.verify_token_collaboration(1, "tw") is True
    assert service.verify_token_collaboration(1, "xxx") is False

def test_verify_token_collaboration_no_conv(service):
    service.conversation_dao.read.return_value = None
    assert service.verify_token_collaboration(1, "tv") is False


# ----------------------------------------------------------
# TEST add_collab_by_token
# ----------------------------------------------------------

def test_add_collab_by_token_viewer(service):
    conv = MagicMock()
    conv.token_viewer = "tv"
    conv.token_writter = "tw"
    service.conversation_dao.read.return_value = conv

    service.collab_dao.find_by_conversation_and_user.return_value = None
    service.create_collab = MagicMock(return_value=True)

    assert service.add_collab_by_token(1, "tv", 5) is True


def test_add_collab_by_token_writer(service):
    conv = MagicMock()
    conv.token_viewer = "tv"
    conv.token_writter = "tw"
    service.conversation_dao.read.return_value = conv

    service.collab_dao.find_by_conversation_and_user.return_value = None
    service.create_collab = MagicMock(return_value=True)

    assert service.add_collab_by_token(1, "tw", 5) is True


def test_add_collab_by_token_invalid_token(service):
    conv = MagicMock()
    conv.token_viewer = "tv"
    conv.token_writter = "tw"
    service.conversation_dao.read.return_value = conv

    service.collab_dao.find_by_conversation_and_user.return_value = None

    assert service.add_collab_by_token(1, "xxx", 5) is False


def test_add_collab_by_token_existing(service):
    conv = MagicMock()
    service.conversation_dao.read.return_value = conv

    existing = Collaboration(id_user=5, id_conversation=1, role="viewer")
    service.collab_dao.find_by_conversation_and_user.return_value = existing

    assert service.add_collab_by_token(1, "tv", 5) is False


def test_add_collab_by_token_no_conv(service):
    service.conversation_dao.read.return_value = None
    assert service.add_collab_by_token(1, "tv", 5) is False
