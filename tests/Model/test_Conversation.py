import pytest


@pytest.fixture
def sample_conversation():
    return Conversation("user", "assistant")


def test_conversation_initialization(sample_conversation):
    assert sample_conversation.user == "user"
    assert sample_conversation.assistant == "assistant"
    assert sample_conversation.messages == []
