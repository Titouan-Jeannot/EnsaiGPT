from src.DAO.FeedbackDAO import FeedbackDAO
from src.ObjetMetier.Feedback import Feedback


def build_feedback(user_id: int = 1, message_id: int = 1, is_like: bool = True) -> Feedback:
    return Feedback(
        id_feedback=None,
        id_user=user_id,
        id_message=message_id,
        is_like=is_like,
        comment="",
    )


def test_feedback_crud(feedback_dao: FeedbackDAO):
    created = feedback_dao.create(build_feedback())
    assert created.id_feedback is not None
    assert feedback_dao.read(created.id_feedback) == created
    created.comment = "Super"
    feedback_dao.update(created)
    assert feedback_dao.read(created.id_feedback).comment == "Super"
    assert feedback_dao.delete(created.id_feedback) is True


def test_feedback_lists(feedback_dao: FeedbackDAO):
    like = feedback_dao.create(build_feedback())
    dislike = feedback_dao.create(build_feedback(is_like=False))
    feedback_dao.create(build_feedback(user_id=2))
    by_message = feedback_dao.list_by_message(1)
    assert like in by_message and dislike in by_message and len(by_message) == 3
    by_user = feedback_dao.list_by_user(1)
    assert like in by_user and dislike in by_user and len(by_user) == 2
    assert feedback_dao.count_for_message(1, True) == 2
    assert feedback_dao.count_for_message(1, False) == 1
