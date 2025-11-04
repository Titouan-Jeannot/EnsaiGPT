import pytest

from src.ObjetMetier.Conversation import Conversation
from src.ObjetMetier.Collaboration import Collaboration
from src.Service.CollaborationService import CollaborationService


def create_conversation(conversation_service, owner_id: int):
    conversation = Conversation(
        id_conversation=None,
        titre="Projet",
        setting_conversation="",
        token_viewer="view",
        token_writter="write",
    )
    return conversation_service.create_conversation(conversation, owner_id)


def test_collaboration_roles(
    collaboration_service: CollaborationService,
    conversation_service,
    user_service,
):
    owner = user_service.create_user("alice", "alice@example.com", "password123")
    conversation = create_conversation(conversation_service, owner.id_user)
    assert collaboration_service.is_admin(owner.id_user, conversation.id_conversation)
    new_user = user_service.create_user("bob", "bob@example.com", "password123")
    collab = collaboration_service.create_collab(new_user.id_user, conversation.id_conversation, "writer")
    assert collaboration_service.is_writer(new_user.id_user, conversation.id_conversation)
    assert collaboration_service.is_viewer(new_user.id_user, conversation.id_conversation)
    with pytest.raises(ValueError):
        collaboration_service.create_collab(999, conversation.id_conversation, "viewer")


def test_verify_token_and_add(collaboration_service, conversation_service, user_service):
    owner = user_service.create_user("alice", "alice@example.com", "password123")
    conversation = create_conversation(conversation_service, owner.id_user)
    newcomer = user_service.create_user("charlie", "charlie@example.com", "password123")
    assert collaboration_service.verify_token_collaboration(conversation.id_conversation, "view")
    assert collaboration_service.verify_token_collaboration(conversation.id_conversation, "invalid") is False
    collab = Collaboration(
        id_collaboration=None,
        id_conversation=conversation.id_conversation,
        id_user=newcomer.id_user,
        role="VIEWER",
    )
    created = collaboration_service.add_collaboration(collab)
    assert created.id_collaboration is not None
    with pytest.raises(ValueError):
        collaboration_service.add_collaboration(collab)


def test_delete_and_change_role(collaboration_service, conversation_service, user_service):
    owner = user_service.create_user("alice", "alice@example.com", "password123")
    conversation = create_conversation(conversation_service, owner.id_user)
    member = user_service.create_user("bob", "bob@example.com", "password123")
    collab = collaboration_service.create_collab(member.id_user, conversation.id_conversation, "viewer")
    updated = collaboration_service.change_role(conversation.id_conversation, member.id_user, "writer")
    assert updated.role == "WRITER"
    with pytest.raises(ValueError):
        collaboration_service.change_role(conversation.id_conversation, member.id_user, "guest")
    assert collaboration_service.delete_collaborator(conversation.id_conversation, member.id_user) is True
    assert collaboration_service.delete_collaborator(conversation.id_conversation, member.id_user) is False
