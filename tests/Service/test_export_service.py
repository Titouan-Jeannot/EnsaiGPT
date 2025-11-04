from src.ObjetMetier.Conversation import Conversation


def test_export_conversation(export_service, conversation_service, message_service, user_service):
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
    message_service.send_message(conversation.id_conversation, owner.id_user, "Bonjour")
    export = export_service.export_conversation(conversation.id_conversation, owner.id_user)
    assert "Projet" in export
    assert "Bonjour" in export
