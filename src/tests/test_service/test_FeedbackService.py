import pytest
from unittest.mock import MagicMock
from datetime import datetime

from Service.FeedbackService import FeedbackService
from ObjetMetier.Feedback import Feedback


# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------

@pytest.fixture(scope="module")
def mock_dao():
    """DAO mocké partagé pour tout le module (compatible Singleton)."""
    return MagicMock()


@pytest.fixture(scope="module")
def feedback_service(mock_dao):
    """
    Instance unique de FeedbackService.

    Comme le service utilise le metaclass Singleton, on injecte le mock DAO
    dès la première instanciation pour que ce soit celui-ci qui soit utilisé
    dans tous les tests.
    """
    return FeedbackService(dao=mock_dao)


@pytest.fixture(autouse=True)
def reset_mock(mock_dao):
    """Réinitialise le mock du DAO avant chaque test."""
    mock_dao.reset_mock()
    yield


# -------------------------------------------------------------------
# Tests add_feedback
# -------------------------------------------------------------------

def test_add_feedback_success(feedback_service, mock_dao):
    mock_return = Feedback(
        id_feedback=123,
        id_user=1,
        id_message=10,
        is_like=True,
        comment="Top",
        created_at=datetime.now(),
    )
    mock_dao.create.return_value = mock_return

    fb = feedback_service.add_feedback(user_id=1, message_id=10, is_like=True, comment="Top")

    # Le service renvoie bien ce que le DAO renvoie
    assert fb is mock_return

    # Vérifie que create a été appelé une fois avec un Feedback
    mock_dao.create.assert_called_once()
    arg = mock_dao.create.call_args[0][0]
    assert isinstance(arg, Feedback)
    assert arg.id_user == 1
    assert arg.id_message == 10
    assert arg.is_like is True
    assert arg.comment == "Top"
    assert isinstance(arg.created_at, datetime)


@pytest.mark.parametrize("user_id", [-1, "a", 1.5])
def test_add_feedback_invalid_user_id(feedback_service, user_id):
    with pytest.raises(ValueError, match="user_id doit être un entier positif"):
        feedback_service.add_feedback(user_id=user_id, message_id=1, is_like=True, comment=None)


@pytest.mark.parametrize("message_id", [-1, "a", 1.5])
def test_add_feedback_invalid_message_id(feedback_service, message_id):
    with pytest.raises(ValueError, match="message_id doit être un entier positif"):
        feedback_service.add_feedback(user_id=1, message_id=message_id, is_like=True, comment=None)


@pytest.mark.parametrize("is_like", [None, 0, 1, "true"])
def test_add_feedback_invalid_is_like(feedback_service, is_like):
    with pytest.raises(ValueError, match="is_like doit être un booléen"):
        feedback_service.add_feedback(user_id=1, message_id=1, is_like=is_like, comment=None)


def test_add_feedback_invalid_comment_type(feedback_service):
    with pytest.raises(ValueError, match="comment doit être une chaîne ou None"):
        feedback_service.add_feedback(user_id=1, message_id=1, is_like=True, comment=123)


def test_add_feedback_dao_exception_is_propagated(feedback_service, mock_dao):
    mock_dao.create.side_effect = RuntimeError("DB error")

    with pytest.raises(RuntimeError, match="DB error"):
        feedback_service.add_feedback(user_id=1, message_id=1, is_like=True, comment="ok")

    mock_dao.create.assert_called_once()


# -------------------------------------------------------------------
# Tests get_feedback_by_message
# -------------------------------------------------------------------

def test_get_feedback_by_message_success(feedback_service, mock_dao):
    fb_list = [
        Feedback(1, 1, 10, True, "bien", datetime.now()),
        Feedback(2, 2, 10, False, "bof", datetime.now()),
    ]
    mock_dao.find_by_message.return_value = fb_list

    res = feedback_service.get_feedback_by_message(10)

    assert res == fb_list
    mock_dao.find_by_message.assert_called_once_with(10)


@pytest.mark.parametrize("message_id", [-1, "a", 1.5])
def test_get_feedback_by_message_invalid_id(feedback_service, message_id):
    with pytest.raises(ValueError, match="message_id doit être un entier positif"):
        feedback_service.get_feedback_by_message(message_id)


# -------------------------------------------------------------------
# Tests get_feedback_by_user
# -------------------------------------------------------------------

def test_get_feedback_by_user_success(feedback_service, mock_dao):
    fb_list = [
        Feedback(1, 5, 10, True, "cool", datetime.now()),
    ]
    mock_dao.find_by_user.return_value = fb_list

    res = feedback_service.get_feedback_by_user(5)

    assert res == fb_list
    mock_dao.find_by_user.assert_called_once_with(5)


@pytest.mark.parametrize("user_id", [-1, "a", 1.5])
def test_get_feedback_by_user_invalid_id(feedback_service, user_id):
    with pytest.raises(ValueError, match="user_id doit être un entier positif"):
        feedback_service.get_feedback_by_user(user_id)


# -------------------------------------------------------------------
# Tests count_likes / count_dislikes
# -------------------------------------------------------------------

def test_count_likes_success(feedback_service, mock_dao):
    mock_dao.count_likes.return_value = 3
    res = feedback_service.count_likes(10)
    assert res == 3
    mock_dao.count_likes.assert_called_once_with(10)


@pytest.mark.parametrize("message_id", [-1, "a", 1.5])
def test_count_likes_invalid_id(feedback_service, message_id):
    with pytest.raises(ValueError, match="message_id doit être un entier positif"):
        feedback_service.count_likes(message_id)


def test_count_dislikes_success(feedback_service, mock_dao):
    mock_dao.count_dislikes.return_value = 2
    res = feedback_service.count_dislikes(10)
    assert res == 2
    mock_dao.count_dislikes.assert_called_once_with(10)


@pytest.mark.parametrize("message_id", [-1, "a", 1.5])
def test_count_dislikes_invalid_id(feedback_service, message_id):
    with pytest.raises(ValueError, match="message_id doit être un entier positif"):
        feedback_service.count_dislikes(message_id)
