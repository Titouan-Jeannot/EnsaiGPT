# src/tests/test_service/test_FeedbackService.py
from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest

from src.Service.FeedbackService import FeedbackService
from src.ObjetMetier.Feedback import Feedback
from src.Utils.Singleton import Singleton


def make_feedback(**kw):
    now = kw.pop("created_at", datetime(2025, 1, 1, 12))
    return Feedback(
        id_feedback=kw.get("id_feedback", 1),
        id_user=kw.get("id_user", 10),
        id_message=kw.get("id_message", 20),
        is_like=kw.get("is_like", True),
        comment=kw.get("comment", "ok"),
        created_at=now,
    )


def _fresh_service_with_mockdao(MockDAO):
    """
    Réinitialise le Singleton et renvoie (service, dao_mock).
    On fixe aussi s.dao = dao_mock pour être 100% sûr.
    """
    Singleton._instances.pop(FeedbackService, None)
    dao = MockDAO.return_value
    s = FeedbackService()
    s.dao = dao
    return s, dao


def test_add_feedback_success():
    with patch("src.Service.FeedbackService.FeedbackDAO") as MockDAO:
        s, dao = _fresh_service_with_mockdao(MockDAO)
        dao.create.return_value = make_feedback(id_feedback=123, is_like=True, comment="nice")

        fb = s.add_feedback(10, 20, True, "nice")

        assert isinstance(fb, Feedback)
        assert fb.id_feedback == 123
        dao.create.assert_called_once()
        created = dao.create.call_args.args[0]
        assert isinstance(created, Feedback)
        assert created.id_user == 10 and created.id_message == 20 and created.is_like is True


@pytest.mark.parametrize(
    "user_id,message_id,is_like,comment",
    [
        (-1, 1, True, None),
        (1, -2, True, None),
        (1, 2, "yes", None),   # type: ignore
        (1, 2, True, 123),     # type: ignore
    ],
)
def test_add_feedback_validations(user_id, message_id, is_like, comment):
    # Validation pure, pas besoin de mocker la DAO
    Singleton._instances.pop(FeedbackService, None)
    s = FeedbackService()
    with pytest.raises(ValueError):
        s.add_feedback(user_id, message_id, is_like, comment)  # type: ignore


def test_get_feedback_by_message():
    with patch("src.Service.FeedbackService.FeedbackDAO") as MockDAO:
        s, dao = _fresh_service_with_mockdao(MockDAO)
        dao.find_by_message.return_value = [
            make_feedback(id_feedback=1, id_message=99, is_like=True),
            make_feedback(id_feedback=2, id_message=99, is_like=False),
        ]

        out = s.get_feedback_by_message(99)

        assert isinstance(out, list)
        assert len(out) == 2 and out[0].id_feedback == 1
        dao.find_by_message.assert_called_once_with(99)


def test_get_feedback_by_user():
    with patch("src.Service.FeedbackService.FeedbackDAO") as MockDAO:
        s, dao = _fresh_service_with_mockdao(MockDAO)
        dao.find_by_user.return_value = [make_feedback(id_feedback=7, id_user=5)]

        out = s.get_feedback_by_user(5)

        assert isinstance(out, list)
        assert len(out) == 1 and out[0].id_user == 5
        dao.find_by_user.assert_called_once_with(5)


def test_counts():
    with patch("src.Service.FeedbackService.FeedbackDAO") as MockDAO:
        s, dao = _fresh_service_with_mockdao(MockDAO)
        dao.count_likes.return_value = 3
        dao.count_dislikes.return_value = 1

        assert s.count_likes(42) == 3
        assert s.count_dislikes(42) == 1

        dao.count_likes.assert_called_once_with(42)
        dao.count_dislikes.assert_called_once_with(42)
