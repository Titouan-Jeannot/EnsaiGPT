import pytest

from src.ObjetMetier.Conversation import Conversation
from src.Service.FeedbackService import FeedbackService


def create_message(message_service, conversation_service, user_service):
    owner, conversation = prepare_conversation(conversation_service, user_service)
    message = message_service.send_message(conversation.id_conversation, owner.id_user, "Bonjour")
    return owner, conversation, message


def prepare_conversation(conversation_service, user_service):
    owner = user_service.create_user("alice", "alice@example.com", "password123")
    conversation = conversation_service.create_conversation(
        Conversation(
            id_conversation=None,
            titre="Projet",
            setting_conversation="",
            token_viewer="view",
            token_writter="write",
        ),
        owner.id_user,
    )
    return owner, conversation



def test_add_feedback(feedback_service: FeedbackService, message_service, conversation_service, user_service):
    owner, conversation = prepare_conversation(conversation_service, user_service)
    message = message_service.send_message(conversation.id_conversation, owner.id_user, "Bonjour")
    feedback = feedback_service.add_feedback(owner.id_user, message.id_message, True, "Bravo")
    assert feedback.id_feedback is not None
    with pytest.raises(ValueError):
        feedback_service.add_feedback(owner.id_user, 999, True)


def test_feedback_counts(feedback_service: FeedbackService, message_service, conversation_service, user_service):
    owner, conversation = prepare_conversation(conversation_service, user_service)
    message = message_service.send_message(conversation.id_conversation, owner.id_user, "Bonjour")
    feedback_service.add_feedback(owner.id_user, message.id_message, True)
    feedback_service.add_feedback(owner.id_user, message.id_message, False)
    assert feedback_service.count_likes(message.id_message) == 1
    assert feedback_service.count_dislikes(message.id_message) == 1
    assert len(feedback_service.get_feedback_by_message(message.id_message)) == 2
    assert len(feedback_service.get_feedback_by_user(owner.id_user)) == 2
