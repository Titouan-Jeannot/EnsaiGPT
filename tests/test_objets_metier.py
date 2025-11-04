from datetime import datetime

import pytest

from src.ObjetMetier.Collaboration import Collaboration
from src.ObjetMetier.Conversation import Conversation
from src.ObjetMetier.Feedback import Feedback
from src.ObjetMetier.Message import Message
from src.ObjetMetier.User import User


def test_user_touch_login():
    user = User(
        id_user=None,
        username="alice",
        nom="",
        prenom="",
        mail="alice@example.com",
        password_hash="salt$hash",
        setting_param="",
    )
    user.touch_login()
    assert isinstance(user.last_login, datetime)


def test_conversation_deactivate():
    conversation = Conversation(
        id_conversation=None,
        titre="Projet",
        setting_conversation="",
        token_viewer="view",
        token_writter="write",
    )
    conversation.deactivate()
    assert conversation.is_active is False


def test_collaboration_roles():
    collab = Collaboration(
        id_collaboration=None,
        id_conversation=1,
        id_user=2,
        role="writer",
    )
    assert collab.can_write() is True
    assert collab.is_admin() is False
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=None, id_conversation=1, id_user=2, role="guest")


def test_message_validation():
    msg = Message(
        id_message=None,
        id_conversation=1,
        id_user=2,
        message="Bonjour",
        is_from_agent=False,
    )
    assert msg.is_from_user() is True
    with pytest.raises(ValueError):
        Message(
            id_message=None,
            id_conversation=0,
            id_user=2,
            message="",
            is_from_agent=False,
        )


def test_feedback_validation():
    feedback = Feedback(
        id_feedback=None,
        id_user=1,
        id_message=2,
        is_like=True,
        comment="",
    )
    assert feedback.is_like is True
    with pytest.raises(ValueError):
        Feedback(
            id_feedback=None,
            id_user=0,
            id_message=2,
            is_like=True,
            comment="",
        )
