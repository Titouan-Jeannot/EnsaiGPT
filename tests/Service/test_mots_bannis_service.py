from src.Service.MotsBannisService import MotsBannisService


def test_banned_words(mots_bannis_service: MotsBannisService):
    mots_bannis_service.add_banned_word("spam")
    assert mots_bannis_service.verify_mot_ban("Ceci est du spam") is True
    mots_bannis_service.remove_banned_word("spam")
    assert mots_bannis_service.verify_mot_ban("Ceci est du spam") is False
    assert list(mots_bannis_service.list_banned_words()) == []
