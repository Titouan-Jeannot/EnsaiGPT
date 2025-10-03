import pytest
from src.Objet_Metier.Feedback import Feedback
from datetime import datetime


def test_feedback_initialization():
    feedback = Feedback(
        id_feedback=1,
        id_user=100,
        id_message=200,
        is_like=True,
        comment="Great message!",
        create_at=datetime.now()
    )
    assert feedback.id_feedback == 1
    assert feedback.id_user == 100
    assert feedback.id_message == 200
    assert feedback.is_like is True
    assert feedback.comment == "Great message!"
    assert isinstance(feedback.create_at, datetime)

def test_feedback_init_type_errors():
    with pytest.raises(ValueError):
        Feedback(id_feedback="notint", id_user=100, id_message=200, is_like=True, comment="Great message!", create_at=datetime.now())
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user="notint", id_message=200, is_like=True, comment="Great message!", create_at=datetime.now())
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=100, id_message="notint", is_like=True, comment="Great message!", create_at=datetime.now())
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=100, id_message=200, is_like="notbool", comment="Great message!", create_at=datetime.now())
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment=123, create_at=datetime.now())
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Great message!", create_at="notdatetime")
    with pytest.raises(ValueError):
        Feedback(id_feedback=None, id_user=100, id_message=200, is_like=True, comment="Great message!", create_at=datetime.now())

def test_feedback_equality():
    feedback1 = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Great message!", create_at=datetime.now())
    feedback2 = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Great message!", create_at=feedback1.create_at)
    feedback3 = Feedback(id_feedback=2, id_user=101, id_message=201, is_like=False, comment="Bad message!", create_at=datetime.now())

    assert feedback1 == feedback2
    assert feedback1 != feedback3

def test_feedback_edge_cases():
    # Test with minimum values
    feedback_min = Feedback(id_feedback=0, id_user=0, id_message=0, is_like=False, comment="", create_at=datetime.now())
    assert feedback_min.id_feedback == 0
    assert feedback_min.id_user == 0
    assert feedback_min.id_message == 0
    assert feedback_min.is_like is False
    assert feedback_min.comment == ""

    # Test with maximum values (assuming some reasonable max for integers)
    max_int = 2**31 - 1
    feedback_max = Feedback(id_feedback=max_int, id_user=max_int, id_message=max_int, is_like=True, comment="A"*1000, create_at=datetime.now())
    assert feedback_max.id_feedback == max_int
    assert feedback_max.id_user == max_int
    assert feedback_max.id_message == max_int
    assert feedback_max.is_like is True
    assert feedback_max.comment == "A"*1000

def test_feedback_special_characters_in_comment():
    special_comment = "Great message! 😊🚀 #feedback @user"
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment=special_comment, create_at=datetime.now())
    assert feedback.comment == special_comment

def test_feedback_whitespace_in_comment():
    whitespace_comment = "   Great message!   "
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment=whitespace_comment, create_at=datetime.now())
    assert feedback.comment == whitespace_comment

def test_feedback_null_comment():
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment=None, create_at=datetime.now())
    assert feedback.comment is None

def test_feedback_future_date():
    future_date = datetime(3000, 1, 1)
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Future message!", create_at=future_date)
    assert feedback.create_at == future_date

def test_feedback_past_date():
    past_date = datetime(2000, 1, 1)
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Past message!", create_at=past_date)
    assert feedback.create_at == past_date
