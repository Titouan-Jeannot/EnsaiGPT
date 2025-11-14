import pytest
from ObjetMetier.Feedback import Feedback
from datetime import datetime


def test_feedback_initialization():
    feedback = Feedback(
        id_feedback=1,
        id_user=100,
        id_message=200,
        is_like=True,
        comment="Great message!",
        created_at=datetime.now()
    )
    assert feedback.id_feedback == 1
    assert feedback.id_user == 100
    assert feedback.id_message == 200
    assert feedback.is_like is True
    assert feedback.comment == "Great message!"
    assert isinstance(feedback.created_at, datetime)

def test_feedback_init_type_errors():
    with pytest.raises(ValueError):
        Feedback(id_feedback="notint", id_user=100, id_message=200, is_like=True, comment="Great message!", created_at=datetime.now())
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user="notint", id_message=200, is_like=True, comment="Great message!", created_at=datetime.now())
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=100, id_message="notint", is_like=True, comment="Great message!", created_at=datetime.now())
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=100, id_message=200, is_like="notbool", comment="Great message!", created_at=datetime.now())
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment=123, created_at=datetime.now())
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Great message!", created_at="notdatetime")
    with pytest.raises(ValueError):
        Feedback(id_feedback=None, id_user=100, id_message=200, is_like=True, comment="Great message!", created_at=datetime.now())

def test_feedback_equality():
    feedback1 = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Great message!", created_at=datetime.now())
    feedback2 = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Great message!", created_at=feedback1.created_at)
    feedback3 = Feedback(id_feedback=2, id_user=101, id_message=201, is_like=False, comment="Bad message!", created_at=datetime.now())

    assert feedback1 == feedback2
    assert feedback1 != feedback3

def test_feedback_edge_cases():
    # Test with minimum values
    feedback_min = Feedback(id_feedback=0, id_user=0, id_message=0, is_like=False, comment="", created_at=datetime.now())
    assert feedback_min.id_feedback == 0
    assert feedback_min.id_user == 0
    assert feedback_min.id_message == 0
    assert feedback_min.is_like is False
    assert feedback_min.comment == ""

    # Test with maximum values (assuming some reasonable max for integers)
    max_int = 2**31 - 1
    feedback_max = Feedback(id_feedback=max_int, id_user=max_int, id_message=max_int, is_like=True, comment="A"*1000, created_at=datetime.now())
    assert feedback_max.id_feedback == max_int
    assert feedback_max.id_user == max_int
    assert feedback_max.id_message == max_int
    assert feedback_max.is_like is True
    assert feedback_max.comment == "A"*1000

def test_feedback_special_characters_in_comment():
    special_comment = "Great message! 😊🚀 #feedback @user"
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment=special_comment, created_at=datetime.now())
    assert feedback.comment == special_comment

def test_feedback_whitespace_in_comment():
    whitespace_comment = "   Great message!   "
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment=whitespace_comment, created_at=datetime.now())
    assert feedback.comment == whitespace_comment

def test_feedback_null_comment():
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment=None, created_at=datetime.now())
    assert feedback.comment is None

def test_feedback_future_date():
    future_date = datetime(3000, 1, 1)
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Future message!", created_at=future_date)
    assert feedback.created_at == future_date

def test_feedback_past_date():
    past_date = datetime(2000, 1, 1)
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Past message!", created_at=past_date)
    assert feedback.created_at == past_date

def test_feedback_boolean_edge_cases():
    feedback_true = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Like!", created_at=datetime.now())
    feedback_false = Feedback(id_feedback=2, id_user=101, id_message=201, is_like=False, comment="Dislike!", created_at=datetime.now())
    assert feedback_true.is_like is True
    assert feedback_false.is_like is False

def test_feedback_zero_id():
    feedback = Feedback(id_feedback=0, id_user=0, id_message=0, is_like=True, comment="Zero IDs", created_at=datetime.now())
    assert feedback.id_feedback == 0
    assert feedback.id_user == 0
    assert feedback.id_message == 0

def test_feedback_negative_id():
    with pytest.raises(ValueError):
        Feedback(id_feedback=-1, id_user=-100, id_message=-200, is_like=True, comment="Negative IDs", created_at=datetime.now())

def test_feedback_large_number_of_instances():
    feedbacks = []
    for i in range(1000):
        fb = Feedback(
            id_feedback=i,
            id_user=i % 100,
            id_message=i % 200,
            is_like=(i % 2 == 0),
            comment=f"Feedback {i}",
            created_at=datetime.now()
        )
        feedbacks.append(fb)
    assert len(feedbacks) == 1000
    for i in range(1000):
        assert feedbacks[i].id_feedback == i
        assert feedbacks[i].id_user == i % 100
        assert feedbacks[i].id_message == i % 200
        assert feedbacks[i].is_like == (i % 2 == 0)
        assert feedbacks[i].comment == f"Feedback {i}"

def test_feedback_equality_different_types():
    """Test que la comparaison avec d'autres types retourne False"""
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Great message!", created_at=datetime.now())
    assert feedback != "not a feedback"
    assert feedback != 123
    assert feedback != None
    assert feedback != {"id": 1}

def test_feedback_empty_comment():
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="", created_at=datetime.now())
    assert feedback.comment == ""

def test_feedback_none_id_feedback():
    with pytest.raises(ValueError):
        Feedback(id_feedback=None, id_user=100, id_message=200, is_like=True, comment="Great message!", created_at=datetime.now())

def test_feedback_none_id_user():
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=None, id_message=200, is_like=True, comment="Great message!", created_at=datetime.now())

def test_feedback_none_id_message():
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=100, id_message=None, is_like=True, comment="Great message!", created_at=datetime.now())

def test_feedback_none_is_like():
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=100, id_message=200, is_like=None, comment="Great message!", created_at=datetime.now())

def test_feedback_none_created_at():
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Great message!", created_at=None)


def test_feedback_empty_string_comment():
    """Test that an empty string as a comment is allowed."""
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="", created_at=datetime.now())
    assert feedback.comment == ""

def test_feedback_whitespace_only_comment():
    """Test that a comment with only whitespace is allowed."""
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="   ", created_at=datetime.now())
    assert feedback.comment == "   "

def test_feedback_special_characters_in_comment():
    """Test that special characters in the comment are handled correctly."""
    special_comment = "!@#$%^&*()_+-=[]{}|;':,.<>?/`~"
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment=special_comment, created_at=datetime.now())
    assert feedback.comment == special_comment

def test_feedback_unicode_characters_in_comment():
    """Test that Unicode characters in the comment are handled correctly."""
    unicode_comment = "こんにちは世界🌏"
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment=unicode_comment, created_at=datetime.now())
    assert feedback.comment == unicode_comment

def test_feedback_large_comment():
    """Test that a very large comment is handled correctly."""
    large_comment = "A" * 10000  # 10,000 characters
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment=large_comment, created_at=datetime.now())
    assert feedback.comment == large_comment

def test_feedback_invalid_date_type():
    """Test that an invalid date type raises an error."""
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Invalid date", created_at="not a date")

def test_feedback_negative_and_zero_ids():
    """Test that negative IDs raise an error and zero IDs are allowed."""
    with pytest.raises(ValueError):
        Feedback(id_feedback=-1, id_user=100, id_message=200, is_like=True, comment="Negative ID", created_at=datetime.now())
    feedback = Feedback(id_feedback=0, id_user=0, id_message=0, is_like=True, comment="Zero IDs", created_at=datetime.now())
    assert feedback.id_feedback == 0
    assert feedback.id_user == 0
    assert feedback.id_message == 0

def test_feedback_boolean_edge_cases():
    """Test that boolean edge cases are handled correctly."""
    feedback_true = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="True case", created_at=datetime.now())
    feedback_false = Feedback(id_feedback=2, id_user=101, id_message=201, is_like=False, comment="False case", created_at=datetime.now())
    assert feedback_true.is_like is True
    assert feedback_false.is_like is False

def test_feedback_invalid_boolean_type():
    """Test that an invalid boolean type raises an error."""
    with pytest.raises(ValueError):
        Feedback(id_feedback=1, id_user=100, id_message=200, is_like="not a boolean", comment="Invalid boolean", created_at=datetime.now())

def test_feedback_equality_with_different_objects():
    """Test that equality comparison with different object types returns False."""
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Equality test", created_at=datetime.now())
    assert feedback != "string"
    assert feedback != 123
    assert feedback != None
    assert feedback != {"id_feedback": 1}

def test_feedback_large_number_of_instances():
    """Test creating a large number of Feedback instances."""
    feedbacks = []
    for i in range(1000):
        feedback = Feedback(
            id_feedback=i,
            id_user=i % 100,
            id_message=i % 200,
            is_like=(i % 2 == 0),
            comment=f"Feedback {i}",
            created_at=datetime.now()
        )
        feedbacks.append(feedback)
    assert len(feedbacks) == 1000
    for i, feedback in enumerate(feedbacks):
        assert feedback.id_feedback == i
        assert feedback.id_user == i % 100
        assert feedback.id_message == i % 200
        assert feedback.is_like == (i % 2 == 0)
        assert feedback.comment == f"Feedback {i}"

def test_feedback_future_date():
    """Test that a future date is allowed."""
    future_date = datetime(3000, 1, 1)
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Future date", created_at=future_date)
    assert feedback.created_at == future_date

def test_feedback_past_date():
    """Test that a past date is allowed."""
    past_date = datetime(1900, 1, 1)
    feedback = Feedback(id_feedback=1, id_user=100, id_message=200, is_like=True, comment="Past date", created_at=past_date)
    assert feedback.created_at == past_date
