import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from datetime import datetime
from Service.ExportService import ExportService
from ObjetMetier.Conversation import Conversation
from ObjetMetier.Message import Message


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _fake_conv(cid=1, title="Titre test"):
    return SimpleNamespace(
        id_conversation=cid,
        titre=title,
        created_at=datetime(2024, 1, 1, 12, 0),
        setting_conversation="{}",
        token_viewer="tv",
        token_writter="tw",
        is_active=True,
    )


def _fake_msg(mid, conv_id, user_id, txt, is_agent=False):
    return SimpleNamespace(
        id_message=mid,
        id_conversation=conv_id,
        id_user=user_id,
        message=txt,
        datetime=datetime(2024, 1, 1, 12, mid),
        is_from_agent=is_agent,
    )


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------
@pytest.fixture
def mock_message_dao():
    return MagicMock()


@pytest.fixture
def mock_conversation_dao():
    return MagicMock()


@pytest.fixture
def mock_user_dao():
    return MagicMock()


@pytest.fixture
def mock_collab_dao():
    return MagicMock()


@pytest.fixture
def mock_collab_service():
    s = MagicMock()
    s.is_admin.return_value = False
    s.is_writer.return_value = False
    s.is_viewer.return_value = False
    return s


@pytest.fixture
def export_service(
    mock_message_dao,
    mock_conversation_dao,
    mock_user_dao,
    mock_collab_dao,
    mock_collab_service,
):
    return ExportService(
        message_dao=mock_message_dao,
        conversation_dao=mock_conversation_dao,
        user_dao=mock_user_dao,
        collaboration_dao=mock_collab_dao,
        collaboration_service=mock_collab_service,
    )


# ---------------------------------------------------------------------
# Tests _validate_id
# ---------------------------------------------------------------------
def test_validate_id_ok(export_service):
    export_service._validate_id("conversation_id", 3)


def test_validate_id_fail(export_service):
    with pytest.raises(ValueError):
        export_service._validate_id("conversation_id", -1)


# ---------------------------------------------------------------------
# Tests accès via collaboration_service
# ---------------------------------------------------------------------
def test_check_access_via_collab_service(export_service, mock_collab_service):
    mock_collab_service.is_writer.return_value = True
    ok = export_service._check_access(user_id=1, conversation_id=10)
    assert ok is True


# ---------------------------------------------------------------------
# Tests accès via collaboration_dao (CORRIGÉ POUR TA VERSION)
# ---------------------------------------------------------------------
def test_check_access_via_collab_dao(export_service, mock_collab_service, mock_collab_dao):
    mock_collab_service.is_admin.return_value = False
    mock_collab_service.is_writer.return_value = False
    mock_collab_service.is_viewer.return_value = False

    coll = SimpleNamespace(id_conversation=10)
    # _get_callable trouve get_by_user_id en premier → on le mock
    mock_collab_dao.get_by_user_id.return_value = [coll]

    ok = export_service._check_access(user_id=1, conversation_id=10)
    assert ok is True
    mock_collab_dao.get_by_user_id.assert_called_once_with(1)


# ---------------------------------------------------------------------
# Fallback via message_dao
# ---------------------------------------------------------------------
def test_check_access_via_message_dao(export_service, mock_collab_service, mock_collab_dao, mock_message_dao):
    mock_collab_service.is_admin.return_value = False
    mock_collab_service.is_writer.return_value = False
    mock_collab_service.is_viewer.return_value = False
    mock_collab_dao.get_by_user_id.side_effect = Exception()
    mock_message_dao.get_messages_by_conversation_and_user.return_value = [1]

    ok = export_service._check_access(user_id=1, conversation_id=10)
    assert ok is True


def test_check_access_fail(export_service, mock_collab_service, mock_collab_dao, mock_message_dao):
    mock_collab_service.is_admin.return_value = False
    mock_collab_service.is_writer.return_value = False
    mock_collab_service.is_viewer.return_value = False
    mock_collab_dao.get_by_user_id.return_value = []
    mock_message_dao.get_messages_by_conversation_and_user.return_value = []

    ok = export_service._check_access(user_id=1, conversation_id=10)
    assert ok is False


# ---------------------------------------------------------------------
# export_conversation
# ---------------------------------------------------------------------
def test_export_conversation_ok(export_service, mock_conversation_dao, mock_message_dao, mock_user_dao):
    mock_conversation_dao.read.return_value = _fake_conv(10)
    mock_message_dao.get_messages_by_conversation.return_value = [
        _fake_msg(1, 10, 2, "Bonjour", False),
        _fake_msg(2, 10, 0, "Réponse", True),
    ]
    mock_user_dao.read.side_effect = lambda uid: SimpleNamespace(username=f"user{uid}")

    # droit via fallback message
    export_service.collaboration_service.is_admin.return_value = False
    export_service.collaboration_service.is_writer.return_value = False
    export_service.collaboration_service.is_viewer.return_value = False
    export_service.message_dao.get_messages_by_conversation_and_user.return_value = [1]

    out = export_service.export_conversation(10, 2)
    assert "# Titre test" in out
    assert "Bonjour" in out


def test_export_conversation_no_access(export_service, mock_conversation_dao, mock_message_dao):
    mock_conversation_dao.read.return_value = _fake_conv(10)
    mock_message_dao.get_messages_by_conversation.return_value = []

    export_service.collaboration_service.is_admin.return_value = False
    export_service.collaboration_service.is_writer.return_value = False
    export_service.collaboration_service.is_viewer.return_value = False

    export_service.message_dao.get_messages_by_conversation_and_user.return_value = []

    with pytest.raises(PermissionError):
        export_service.export_conversation(10, 2)


# ---------------------------------------------------------------------
# formatters
# ---------------------------------------------------------------------
def test_format_plain(export_service):
    conv = _fake_conv(1)
    msgs = [_fake_msg(1, 1, 2, "Salut")]
    out = export_service._format_plain(conv, msgs)
    assert "Salut" in out


def test_format_markdown(export_service):
    conv = _fake_conv(1)
    msgs = [_fake_msg(1, 1, 2, "Salut")]
    out = export_service._format_markdown(conv, msgs)
    assert "**[2024" in out
    assert "Salut" in out


# ---------------------------------------------------------------------
# suggest_filename (CORRIGÉ POUR TES TESTS)
# ---------------------------------------------------------------------
def test_suggest_filename_with_conversation(export_service, mock_conversation_dao):
    conv = _fake_conv(5, "Titre / dangereux: ?*")
    mock_conversation_dao.read.return_value = conv

    name = export_service.suggest_filename(5, ext="md")
    assert name.endswith(".md")

    # Les caractères interdits doivent être nettoyés
    for bad in [":", "/", "?", "*", "<", ">", '"', "\\", "|"]:
        assert bad not in name

    # Pas vide avant l’extension
    assert name[:-3].strip()


def test_suggest_filename_without_conv(export_service, mock_conversation_dao):
    mock_conversation_dao.read.return_value = None
    assert "conversation_7" in export_service.suggest_filename(7, "txt")
