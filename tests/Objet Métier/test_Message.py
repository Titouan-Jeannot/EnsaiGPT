import pytest
from datetime import datetime
from src.Objet_Metier.Message import Message


class TestMessage:
    """Tests pour la classe Message"""

    @pytest.fixture
    def sample_message(self):
        """Fixture qui crée un objet Message de test"""
        return Message(
            id_message=1,
            id_conversation=101,
            id_user=10,
            datetime=datetime(2023, 10, 1, 12, 0),
            message="Hello, how can I help you?",
            is_from_agent=True,
        )

    def test_message_initialization(self, sample_message):
        """Vérifie que les attributs sont correctement initialisés"""
        assert sample_message.id_message == 1
        assert sample_message.id_conversation == 101
        assert sample_message.id_user == 10
        assert sample_message.datetime == datetime(2023, 10, 1, 12, 0)
        assert sample_message.message == "Hello, how can I help you?"
        assert sample_message.is_from_agent is True

    def test_toggle_is_from_agent(self, sample_message):
        """Vérifie que l’attribut is_from_agent peut être modifié"""
        sample_message.is_from_agent = False
        assert sample_message.is_from_agent is False

        sample_message.is_from_agent = True
        assert sample_message.is_from_agent is True

    def test_invalid_id_message_raises_error(self):
        """Vérifie que id_message doit être entier ou None"""
        with pytest.raises(ValueError):
            Message(
                id_message="not int",
                id_conversation=101,
                id_user=10,
                datetime=datetime.now(),
                message="Erreur",
                is_from_agent=False,
            )

    def test_str_representation(self, sample_message):
        """Vérifie l'affichage en chaîne (méthode __str__)"""
        result = str(sample_message)
        assert "Agent(10)" in result
        assert "Hello, how can I help you?" in result
