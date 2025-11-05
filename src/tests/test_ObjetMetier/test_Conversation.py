# tests/Objet Métier/test_Conversation.py
from datetime import datetime

import pytest

from src.ObjetMetier.Conversation import Conversation


def test_conversation_initialization():
    conv = Conversation(
        id_conversation=1,
        titre="Projet ENSAI",
        created_at=datetime.now(),
        setting_conversation="fr-FR|temperature=0.2",
        token_viewer="viewer-token-123",
        token_writter="writer-token-456",
        is_active=True,
    )
    assert conv.id_conversation == 1
    assert conv.titre == "Projet ENSAI"
    assert isinstance(conv.created_at, datetime)
    assert conv.setting_conversation == "fr-FR|temperature=0.2"
    assert conv.token_viewer == "viewer-token-123"
    assert conv.token_writter == "writer-token-456"
    assert conv.is_active is True


def test_conversation_init_type_errors():
    now = datetime.now()
    # id_conversation doit être int
    with pytest.raises(ValueError):
        Conversation("notint", "Titre", now, "cfg", "tv", "tw", True)
    # titre doit être str
    with pytest.raises(ValueError):
        Conversation(1, 123, now, "cfg", "tv", "tw", True)
    # created_at doit être datetime
    with pytest.raises(ValueError):
        Conversation(1, "Titre", "notdatetime", "cfg", "tv", "tw", True)
    # setting_conversation doit être str
    with pytest.raises(ValueError):
        Conversation(1, "Titre", now, 42, "tv", "tw", True)
    # token_viewer doit être str
    with pytest.raises(ValueError):
        Conversation(1, "Titre", now, "cfg", 999, "tw", True)
    # token_writter doit être str
    with pytest.raises(ValueError):
        Conversation(1, "Titre", now, "cfg", "tv", None, True)
    # is_active doit être bool
    with pytest.raises(ValueError):
        Conversation(1, "Titre", now, "cfg", "tv", "tw", "notbool")


def test_conversation_equality_like():
    """Égalité logique: on compare champ à champ (pas de __eq__ défini dans la classe)."""
    now = datetime.now()
    c1 = Conversation(1, "Titre", now, "cfg", "tv", "tw", True)
    c2 = Conversation(1, "Titre", now, "cfg", "tv", "tw", True)
    c3 = Conversation(2, "Autre", now, "cfg2", "tv2", "tw2", False)

    # champ à champ pour c1 vs c2 (identiques)
    for attr in (
        "id_conversation",
        "titre",
        "created_at",
        "setting_conversation",
        "token_viewer",
        "token_writter",
        "is_active",
    ):
        assert getattr(c1, attr) == getattr(c2, attr)

    # au moins une différence entre c1 et c3
    diffs = [
        getattr(c1, attr) != getattr(c3, attr)
        for attr in (
            "id_conversation",
            "titre",
            "created_at",
            "setting_conversation",
            "token_viewer",
            "token_writter",
            "is_active",
        )
    ]
    assert any(diffs)


def test_conversation_edge_cases():
    # valeurs minimales / vides acceptées (si tu souhaites les interdire, remplace par raises)
    conv_min = Conversation(
        id_conversation=0,
        titre="",
        created_at=datetime.now(),
        setting_conversation="",
        token_viewer="",
        token_writter="",
        is_active=False,
    )
    assert conv_min.id_conversation == 0
    assert conv_min.titre == ""
    assert conv_min.setting_conversation == ""
    assert conv_min.token_viewer == ""
    assert conv_min.token_writter == ""
    assert conv_min.is_active is False

    # valeurs maximales "raisonnables"
    max_int = 2**31 - 1
    conv_max = Conversation(
        id_conversation=max_int,
        titre="A" * 1000,
        created_at=datetime.now(),
        setting_conversation="B" * 1000,
        token_viewer="C" * 256,
        token_writter="D" * 256,
        is_active=True,
    )
    assert conv_max.id_conversation == max_int
    assert conv_max.titre == "A" * 1000
    assert conv_max.setting_conversation == "B" * 1000
    assert conv_max.token_viewer == "C" * 256
    assert conv_max.token_writter == "D" * 256
    assert conv_max.is_active is True


def test_conversation_special_characters_in_fields():
    special_title = "Projet αβγ 😊🚀 #conv"
    special_cfg = "lang=fr-FR;temp=0.1;notes=“éèà — test”"
    conv = Conversation(
        1,
        special_title,
        datetime.now(),
        special_cfg,
        "tv$-#@!",
        "tw$-#@!",
        True,
    )
    assert conv.titre == special_title
    assert conv.setting_conversation == special_cfg
    assert isinstance(conv.created_at, datetime)


def test_conversation_whitespace_in_fields():
    conv = Conversation(
        1,
        "   Mon Titre   ",
        datetime.now(),
        "   cfg   ",
        "   tv   ",
        "   tw   ",
        False,
    )
    assert conv.titre == "   Mon Titre   "
    assert conv.setting_conversation == "   cfg   "
    assert conv.token_viewer == "   tv   "
    assert conv.token_writter == "   tw   "


def test_conversation_future_date():
    future_date = datetime(3000, 1, 1)
    conv = Conversation(1, "Futur", future_date, "cfg", "tv", "tw", True)
    assert conv.created_at == future_date


def test_conversation_past_date():
    past_date = datetime(2000, 1, 1)
    conv = Conversation(1, "Passé", past_date, "cfg", "tv", "tw", False)
    assert conv.created_at == past_date


def test_conversation_boolean_edge_cases():
    conv_true = Conversation(1, "Titre", datetime.now(), "cfg", "tv", "tw", True)
    conv_false = Conversation(2, "Titre2", datetime.now(), "cfg2", "tv2", "tw2", False)
    assert conv_true.is_active is True
    assert conv_false.is_active is False
