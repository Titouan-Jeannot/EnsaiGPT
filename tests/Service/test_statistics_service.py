from datetime import datetime, timedelta

from src.ObjetMetier.Conversation import Conversation
from src.ObjetMetier.Message import Message


def prepare_data(user_service, conversation_service, collaboration_service, message_dao):
    owner = user_service.create_user("alice", "alice@example.com", "password123")
    member = user_service.create_user("bob", "bob@example.com", "password123")
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
    collaboration_service.create_collab(member.id_user, conversation.id_conversation, "writer")
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    message_dao.create(
        Message(
            id_message=None,
            id_conversation=conversation.id_conversation,
            id_user=owner.id_user,
            message="Bonjour",
            datetime_sent=base_time,
            is_from_agent=False,
        )
    )
    message_dao.create(
        Message(
            id_message=None,
            id_conversation=conversation.id_conversation,
            id_user=owner.id_user,
            message="Compte rendu détaillé",
            datetime_sent=base_time + timedelta(minutes=10),
            is_from_agent=False,
        )
    )
    message_dao.create(
        Message(
            id_message=None,
            id_conversation=conversation.id_conversation,
            id_user=member.id_user,
            message="Réponse",
            datetime_sent=base_time + timedelta(minutes=15),
            is_from_agent=False,
        )
    )
    return owner, member, conversation


def test_statistics(statistics_service, user_service, conversation_service, collaboration_service, message_dao):
    owner, member, conversation = prepare_data(
        user_service, conversation_service, collaboration_service, message_dao
    )
    assert statistics_service.nb_conv(owner.id_user) == 1
    assert statistics_service.nb_messages(owner.id_user) == 2
    assert (
        statistics_service.nb_messages_de_user_par_conv(owner.id_user, conversation.id_conversation)
        == 2
    )
    assert statistics_service.nb_message_conv(conversation.id_conversation) == 3
    assert statistics_service.temps_passe_par_conv(owner.id_user, conversation.id_conversation) == timedelta(minutes=10)
    assert statistics_service.temps_passe(owner.id_user) == timedelta(minutes=10)
    top_users = statistics_service.top_active_users()
    assert top_users[0].id_user == owner.id_user
    assert statistics_service.average_message_length() > 0


def test_average_without_messages(statistics_service):
    assert statistics_service.average_message_length() == 0.0
