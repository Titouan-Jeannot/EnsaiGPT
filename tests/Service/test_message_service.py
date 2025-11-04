import pytest

from src.ObjetMetier.Conversation import Conversation
from src.Service.MessageService import MessageService


def prepare_conversation(conversation_service, user_service):
    owner = user_service.create_user("alice", "alice@example.com", "password123")
    conversation = Conversation(
        id_conversation=None,
        titre="Projet",
        setting_conversation="",
        token_viewer="view",
        token_writter="write",
    )
    created = conversation_service.create_conversation(conversation, owner.id_user)
    return owner, created


def test_send_message_success(message_service: MessageService, conversation_service, user_service):
    owner, conversation = prepare_conversation(conversation_service, user_service)
    message = message_service.send_message(conversation.id_conversation, owner.id_user, "Bonjour")
    assert message.id_message is not None
    assert message_service.get_messages(conversation.id_conversation)[0].message == "Bonjour"


def test_send_message_without_rights(message_service: MessageService, conversation_service, user_service):
    owner, conversation = prepare_conversation(conversation_service, user_service)
    stranger = user_service.create_user("bob", "bob@example.com", "password123")
    with pytest.raises(PermissionError):
        message_service.send_message(conversation.id_conversation, stranger.id_user, "Salut")
    with pytest.raises(ValueError):
        message_service.send_message(conversation.id_conversation, owner.id_user, "   ")


def test_send_agent_message(message_service: MessageService, conversation_service, user_service):
    owner, conversation = prepare_conversation(conversation_service, user_service)
    agent = user_service.create_user("agent", "agent@example.com", "password123")
    message_service.send_message(
        conversation.id_conversation,
        agent.id_user,
        "Réponse",
        is_from_agent=True,
    )
    messages = message_service.get_messages(conversation.id_conversation)
    assert len(messages) == 1
    assert messages[0].is_from_agent is True


def test_delete_messages(message_service: MessageService, conversation_service, user_service):
    owner, conversation = prepare_conversation(conversation_service, user_service)
    message_service.send_message(conversation.id_conversation, owner.id_user, "Bonjour")
    deleted = message_service.delete_all_messages_by_conversation(conversation.id_conversation)
    assert deleted == 1


def test_send_message_inactive_conversation(message_service: MessageService, conversation_service, user_service, conversation_dao):
    owner, conversation = prepare_conversation(conversation_service, user_service)
    conversation.deactivate()
    conversation_dao.update(conversation)
    with pytest.raises(ValueError):
        message_service.send_message(conversation.id_conversation, owner.id_user, "Test")
