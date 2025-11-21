import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from datetime import datetime, timedelta

from Service.StatisticsService import StatisticsService
from ObjetMetier.Message import Message
from ObjetMetier.Collaboration import Collaboration
from ObjetMetier.Conversation import Conversation


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_message_dao():
    return MagicMock()

@pytest.fixture
def mock_conversation_dao():
    return MagicMock()

@pytest.fixture
def mock_collaboration_dao():
    return MagicMock()

@pytest.fixture
def mock_user_dao():
    return MagicMock()

@pytest.fixture
def service(mock_message_dao, mock_conversation_dao, mock_collaboration_dao, mock_user_dao):
    return StatisticsService(
        message_dao=mock_message_dao,
        conversation_dao=mock_conversation_dao,
        collaboration_dao=mock_collaboration_dao,
        user_dao=mock_user_dao,
    )


# ---------------------------------------------------------------------------
# TEST nb_conv
# ---------------------------------------------------------------------------

def test_nb_conv_with_collab(service, mock_collaboration_dao):
    mock_collaboration_dao.find_by_user.return_value = [
        Collaboration(id_conversation=1, id_user=10, role="ADMIN"),
        Collaboration(id_conversation=2, id_user=10, role="VIEWER"),
        Collaboration(id_conversation=1, id_user=10, role="WRITER"),
    ]
    assert service.nb_conv(10) == 2


def test_nb_conv_invalid_id(service):
    with pytest.raises(ValueError):
        service.nb_conv(-2)


# ---------------------------------------------------------------------------
# TEST nb_messages
# ---------------------------------------------------------------------------

def test_nb_messages_ok(service, mock_message_dao):
    mock_message_dao.count_messages_by_user = MagicMock(return_value=8)
    assert service.nb_messages(10) == 8


def test_nb_messages_invalid_param(service):
    with pytest.raises(ValueError):
        service.nb_messages(-5)


def test_nb_messages_no_count_method(mock_conversation_dao, mock_collaboration_dao, mock_user_dao):
    """
    Si count_messages_by_user n'existe pas, ton service touche un attribut inexistant → AttributeError.
    Ce test valide CE comportement réel (on ne modifie pas ton service).
    """
    msg_dao = MagicMock()
    if hasattr(msg_dao, "count_messages_by_user"):
        delattr(msg_dao, "count_messages_by_user")

    service = StatisticsService(
        message_dao=msg_dao,
        conversation_dao=mock_conversation_dao,
        collaboration_dao=mock_collaboration_dao,
        user_dao=mock_user_dao,
    )

    with pytest.raises(AttributeError):
        service.nb_messages(10)


# ---------------------------------------------------------------------------
# average_message_length
# ---------------------------------------------------------------------------

def test_average_message_length_user(service, mock_message_dao):
    mock_message_dao.get_messages_by_user = MagicMock(
        return_value=[
            Message(id_message=1, id_conversation=1, id_user=3, datetime=datetime.now(),
                    message="hello", is_from_agent=False),
            Message(id_message=2, id_conversation=1, id_user=3, datetime=datetime.now(),
                    message="bonjour!", is_from_agent=False),
        ]
    )
    assert service.average_message_length(3) == round((5 + 8) / 2)


def test_average_message_length_empty(service, mock_message_dao):
    mock_message_dao.get_messages_by_user = MagicMock(return_value=[])
    assert service.average_message_length(3) == 0.0


def test_average_message_length_no_get_messages_method(mock_conversation_dao, mock_collaboration_dao, mock_user_dao):
    msg_dao = MagicMock()
    if hasattr(msg_dao, "get_messages_by_user"):
        delattr(msg_dao, "get_messages_by_user")

    service = StatisticsService(
        message_dao=msg_dao,
        conversation_dao=mock_conversation_dao,
        collaboration_dao=mock_collaboration_dao,
        user_dao=mock_user_dao,
    )

    with pytest.raises(AttributeError):
        service.average_message_length(user_id=3)


# ---------------------------------------------------------------------------
# nb_message_conv
# ---------------------------------------------------------------------------

def test_nb_message_conv_ok(service, mock_message_dao):
    mock_message_dao.count_messages_by_conversation = MagicMock(return_value=12)
    assert service.nb_message_conv(1) == 12


def test_nb_message_conv_invalid(service):
    with pytest.raises(ValueError):
        service.nb_message_conv(-4)


def test_nb_message_conv_no_method(mock_conversation_dao, mock_collaboration_dao, mock_user_dao):
    msg_dao = MagicMock()
    if hasattr(msg_dao, "count_messages_by_conversation"):
        delattr(msg_dao, "count_messages_by_conversation")

    service = StatisticsService(
        message_dao=msg_dao,
        conversation_dao=mock_conversation_dao,
        collaboration_dao=mock_collaboration_dao,
        user_dao=mock_user_dao,
    )

    with pytest.raises(AttributeError):
        service.nb_message_conv(10)


# ---------------------------------------------------------------------------
# nb_messages_de_user_par_conv
# ---------------------------------------------------------------------------

def test_nb_messages_de_user_par_conv_ok(service, mock_message_dao):
    mock_message_dao.count_messages_by_user_in_conversation = MagicMock(return_value=4)
    assert service.nb_messages_de_user_par_conv(2, 1) == 4


def test_nb_messages_de_user_par_conv_invalid(service):
    with pytest.raises(ValueError):
        service.nb_messages_de_user_par_conv(-1, 5)


def test_nb_messages_de_user_par_conv_no_method(mock_conversation_dao, mock_collaboration_dao, mock_user_dao):
    msg_dao = MagicMock()
    if hasattr(msg_dao, "count_messages_by_user_in_conversation"):
        delattr(msg_dao, "count_messages_by_user_in_conversation")

    service = StatisticsService(
        message_dao=msg_dao,
        conversation_dao=mock_conversation_dao,
        collaboration_dao=mock_collaboration_dao,
        user_dao=mock_user_dao,
    )

    with pytest.raises(AttributeError):
        service.nb_messages_de_user_par_conv(1, 2)


# ---------------------------------------------------------------------------
# count_collaborators_by_conv
# ---------------------------------------------------------------------------

def test_count_collaborators_by_conv(service, mock_collaboration_dao):
    mock_collaboration_dao.count_by_conversation.return_value = 7
    assert service.count_collaborators_by_conv(1) == 7


def test_count_collaborators_by_conv_invalid(service):
    with pytest.raises(ValueError):
        service.count_collaborators_by_conv(-6)
