from datetime import datetime

from src.ObjetMetier.Collaboration import Collaboration
from src.ObjetMetier.Conversation import Conversation


def prepare_environment(
    user_service,
    conversation_service,
    collaboration_service,
    message_service,
):
    owner = user_service.create_user("alice", "alice@example.com", "password123")
    conversation = conversation_service.create_conversation(
        Conversation(
            id_conversation=None,
            titre="Projet Alpha",
            setting_conversation="",
            token_viewer="view",
            token_writter="write",
        ),
        owner.id_user,
    )
    collaborator = user_service.create_user("bob", "bob@example.com", "password123")
    collaboration_service.create_collab(collaborator.id_user, conversation.id_conversation, "writer")
    message_service.send_message(conversation.id_conversation, owner.id_user, "Compte rendu Alpha")
    message_service.send_message(conversation.id_conversation, collaborator.id_user, "Analyse Alpha")
    # conversation bannie pour couvrir la branche
    banned_conv = conversation_service.create_conversation(
        Conversation(
            id_conversation=None,
            titre="Projet Beta",
            setting_conversation="",
            token_viewer="view2",
            token_writter="write2",
        ),
        owner.id_user,
    )
    collaboration_service.add_collaboration(
        Collaboration(
            id_collaboration=None,
            id_conversation=banned_conv.id_conversation,
            id_user=collaborator.id_user,
            role="BANNED",
        )
    )
    return owner, collaborator, conversation


def test_search_services(search_service, user_service, conversation_service, collaboration_service, message_service):
    owner, collaborator, conversation = prepare_environment(
        user_service, conversation_service, collaboration_service, message_service
    )
    messages = search_service.search_messages_by_keyword(owner.id_user, "alpha")
    assert len(messages) == 2
    messages_by_date = search_service.search_messages_by_date(owner.id_user, datetime.utcnow())
    assert len(messages_by_date) == 2
    convs = search_service.search_conversations_by_keyword(owner.id_user, "projet")
    assert len(convs) == 2
    collaborator_msgs = search_service.search_messages_by_keyword(collaborator.id_user, "analyse")
    assert any("Analyse" in msg.message for msg in collaborator_msgs)
    collaborator_convs = search_service.search_conversations_by_keyword(collaborator.id_user, "projet")
    assert len(collaborator_convs) == 1
