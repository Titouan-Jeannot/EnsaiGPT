from src.ObjetMetier.Conversation import Conversation
from src.ObjetMetier.Message import Message


def test_generate_response(llm_service):
    response = llm_service.generate_reponse("Bonjour", temperature=0.5, max_tokens=5, model_version="mock")
    assert "mock" in response


def test_summarize_conversation(llm_service, conversation_dao, message_dao):
    conversation = conversation_dao.create(
        Conversation(
            id_conversation=None,
            titre="Projet",
            setting_conversation="",
            token_viewer="view",
            token_writter="write",
        )
    )
    message_dao.create(
        Message(
            id_message=None,
            id_conversation=conversation.id_conversation,
            id_user=1,
            message="Premier message",
            is_from_agent=False,
        )
    )
    summary = llm_service.summarize_conversation(conversation.id_conversation)
    assert "Résumé" in summary


def test_summarize_empty(llm_service):
    assert llm_service.summarize_conversation(999) == "Conversation vide."
