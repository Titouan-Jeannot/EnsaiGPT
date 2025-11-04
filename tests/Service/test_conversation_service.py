import pytest

from src.ObjetMetier.Conversation import Conversation
from src.Service.ConversationService import ConversationService


def build_conversation(title: str = "Projet") -> Conversation:
    return Conversation(
        id_conversation=None,
        titre=title,
        setting_conversation="",
        token_viewer="view",
        token_writter="write",
    )


def test_create_conversation(conversation_service: ConversationService, collaboration_dao):
    conversation = conversation_service.create_conversation(build_conversation(), owner_id=1)
    assert conversation.id_conversation is not None
    collabs = collaboration_dao.list_by_conversation(conversation.id_conversation)
    assert collabs[0].is_admin() is True


def test_get_lists(conversation_service: ConversationService, collaboration_dao):
    first = conversation_service.create_conversation(build_conversation("Analyse"), owner_id=1)
    second = conversation_service.create_conversation(build_conversation("Développement"), owner_id=1)
    conversations = conversation_service.get_list_conv(1)
    assert {conv.titre for conv in conversations} == {"Analyse", "Développement"}
    by_date = conversation_service.get_list_conv_by_date(1, first.created_at)
    assert len(by_date) == 2
    by_title = conversation_service.get_list_conv_by_title(1, "dévelop")
    assert by_title == [second]


def test_modify_title_requires_permission(conversation_service: ConversationService, collaboration_dao):
    conversation = conversation_service.create_conversation(build_conversation(), owner_id=1)
    updated = conversation_service.modify_title(conversation.id_conversation, "Nouveau", actor_id=1)
    assert updated.titre == "Nouveau"
    with pytest.raises(PermissionError):
        conversation_service.modify_title(conversation.id_conversation, "test", actor_id=2)
    with pytest.raises(ValueError):
        conversation_service.modify_title(conversation.id_conversation, "", actor_id=1)


def test_delete_conversation(conversation_service: ConversationService):
    conversation = conversation_service.create_conversation(build_conversation(), owner_id=1)
    assert conversation_service.delete_conversation(conversation.id_conversation, actor_id=1) is True
    with pytest.raises(PermissionError):
        conversation_service.delete_conversation(conversation.id_conversation, actor_id=2)
