import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from datetime import datetime

from Service.SearchService import SearchService


# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------

@pytest.fixture
def mock_message_dao():
    return MagicMock()


@pytest.fixture
def mock_conversation_dao():
    return MagicMock()


@pytest.fixture
def mock_collaboration_dao():
    return MagicMock()


@pytest.fixture
def search_service(mock_message_dao, mock_conversation_dao, mock_collaboration_dao):
    return SearchService(
        message_dao=mock_message_dao,
        conversation_dao=mock_conversation_dao,
        collaboration_dao=mock_collaboration_dao,
    )


# -------------------------------------------------------------------
# _get_user_accessible_conversation_ids
# -------------------------------------------------------------------

def test_get_user_accessible_conversation_ids_roles(search_service, mock_collaboration_dao):
    collabs = [
        SimpleNamespace(id_conversation=1, role="admin"),
        SimpleNamespace(id_conversation=2, role="WRITER"),
        SimpleNamespace(id_conversation=3, role="viewer"),
        SimpleNamespace(id_conversation=4, role="reader"),  # ignoré par SearchService actuel
        SimpleNamespace(id_conversation=5, role="banni"),
        SimpleNamespace(id_conversation=6, role=None),
    ]
    mock_collaboration_dao.find_by_user.return_value = collabs

    ids = search_service._get_user_accessible_conversation_ids(user_id=10)

    # Avec la version actuelle : seuls admin / writer / viewer sont pris
    assert set(ids) == {1, 2, 3}
    mock_collaboration_dao.find_by_user.assert_called_once_with(10)


# -------------------------------------------------------------------
# search_messages_by_keyword
# -------------------------------------------------------------------

def test_search_messages_by_keyword_empty_keyword(search_service, mock_message_dao, mock_collaboration_dao):
    res = search_service.search_messages_by_keyword(user_id=1, keyword="")
    assert res == []
    mock_collaboration_dao.find_by_user.assert_not_called()
    mock_message_dao.search_by_keyword.assert_not_called()


def test_search_messages_by_keyword_no_accessible(search_service, mock_message_dao, mock_collaboration_dao):
    mock_collaboration_dao.find_by_user.return_value = []
    res = search_service.search_messages_by_keyword(user_id=1, keyword="test")
    assert res == []
    mock_message_dao.search_by_keyword.assert_not_called()


def test_search_messages_by_keyword_ok(search_service, mock_message_dao, mock_collaboration_dao):
    collabs = [
        SimpleNamespace(id_conversation=10, role="admin"),
        SimpleNamespace(id_conversation=11, role="banni"),
        SimpleNamespace(id_conversation=12, role="viewer"),
    ]
    mock_collaboration_dao.find_by_user.return_value = collabs

    msgs = [SimpleNamespace(id_message=1), SimpleNamespace(id_message=2)]
    mock_message_dao.search_by_keyword.return_value = msgs

    res = search_service.search_messages_by_keyword(user_id=5, keyword="hello")

    mock_message_dao.search_by_keyword.assert_called_once_with(
        "hello", [10, 12]
    )
    assert res == msgs


# -------------------------------------------------------------------
# search_messages_by_date
# -------------------------------------------------------------------

def test_search_messages_by_date_no_accessible(search_service, mock_message_dao, mock_collaboration_dao):
    mock_collaboration_dao.find_by_user.return_value = []
    d = datetime(2024, 1, 1)
    res = search_service.search_messages_by_date(user_id=1, target_date=d)
    assert res == []
    mock_message_dao.search_by_date.assert_not_called()


def test_search_messages_by_date_ok(search_service, mock_message_dao, mock_collaboration_dao):
    collabs = [
        SimpleNamespace(id_conversation=2, role="viewer"),
        SimpleNamespace(id_conversation=3, role="banni"),
    ]
    mock_collaboration_dao.find_by_user.return_value = collabs
    d = datetime(2024, 1, 1)

    msgs = [SimpleNamespace(id_message=7)]
    mock_message_dao.search_by_date.return_value = msgs

    res = search_service.search_messages_by_date(user_id=1, target_date=d)

    mock_message_dao.search_by_date.assert_called_once_with(d, [2])
    assert res == msgs


# -------------------------------------------------------------------
# search_conversations_by_keyword
# -------------------------------------------------------------------

@pytest.mark.parametrize("kw", ["", "   "])
def test_search_conversations_by_keyword_invalid_keyword(
    search_service, kw, mock_conversation_dao, mock_message_dao, mock_collaboration_dao
):
    res = search_service.search_conversations_by_keyword(user_id=1, keyword=kw)
    assert res == []
    mock_conversation_dao.search_conversations_by_title.assert_not_called()
    mock_message_dao.search_by_keyword.assert_not_called()
    mock_collaboration_dao.find_by_user.assert_not_called()


def test_search_conversations_by_keyword_title_only(
    search_service, mock_conversation_dao, mock_collaboration_dao, mock_message_dao
):
    # Deux convs, dont une dupliquée
    c1 = SimpleNamespace(id_conversation=10, titre="A")
    c2 = SimpleNamespace(id_conversation=11, titre="B")
    c_dup = SimpleNamespace(id_conversation=10, titre="A bis")

    mock_conversation_dao.search_conversations_by_title.return_value = [c1, c2, c_dup]

    # Pas d'accès -> _get_user_accessible_conversation_ids renvoie []
    mock_collaboration_dao.find_by_user.return_value = []

    res = search_service.search_conversations_by_keyword(user_id=3, keyword="test")

    # On garde l'ordre sans doublon
    assert res == [c1, c2]
    mock_message_dao.search_by_keyword.assert_not_called()


def test_search_conversations_by_keyword_with_messages_and_get_by_id(
    search_service, mock_conversation_dao, mock_collaboration_dao, mock_message_dao
):
    # 1) Résultats de titre
    c1 = SimpleNamespace(id_conversation=10, titre="Conv titre")
    mock_conversation_dao.search_conversations_by_title.return_value = [c1]

    # 2) conversations accessibles via collab
    collabs = [
        SimpleNamespace(id_conversation=10, role="admin"),
        SimpleNamespace(id_conversation=20, role="viewer"),
    ]
    mock_collaboration_dao.find_by_user.return_value = collabs

    # 3) messages contenant le mot-clé
    m1 = SimpleNamespace(id_conversation=10)  # déjà dans seen_ids -> ignoré
    m2 = SimpleNamespace(id_conversation=20)  # nouvelle conversation
    mock_message_dao.search_by_keyword.return_value = [m1, m2]

    c2 = SimpleNamespace(id_conversation=20, titre="Conv via messages")
    mock_conversation_dao.get_by_id.return_value = c2

    res = search_service.search_conversations_by_keyword(user_id=7, keyword="python")

    mock_message_dao.search_by_keyword.assert_called_once_with(
        "python", [10, 20]
    )
    mock_conversation_dao.get_by_id.assert_called_once_with(20)
    assert res == [c1, c2]


def test_search_conversations_by_keyword_conv_getter_missing(
    search_service, mock_conversation_dao, mock_collaboration_dao, mock_message_dao, monkeypatch
):
    # 1) Résultats de titre
    c1 = SimpleNamespace(id_conversation=10, titre="T")
    mock_conversation_dao.search_conversations_by_title.return_value = [c1]

    # 2) collaborations accessibles
    collabs = [
        SimpleNamespace(id_conversation=10, role="admin"),
        SimpleNamespace(id_conversation=20, role="viewer"),
    ]
    mock_collaboration_dao.find_by_user.return_value = collabs

    # 3) messages
    m2 = SimpleNamespace(id_conversation=20)
    mock_message_dao.search_by_keyword.return_value = [m2]

    # supprimer get_by_id et read -> conv_getter non callable
    monkeypatch.delattr(mock_conversation_dao, "get_by_id", raising=False)
    monkeypatch.delattr(mock_conversation_dao, "read", raising=False)

    res = search_service.search_conversations_by_keyword(user_id=1, keyword="k")

    # On ne rajoute pas la conv obtenue via messages
    assert res == [c1]


def test_search_conversations_by_keyword_conv_getter_exception(
    search_service, mock_conversation_dao, mock_collaboration_dao, mock_message_dao
):
    c1 = SimpleNamespace(id_conversation=1, titre="T")
    mock_conversation_dao.search_conversations_by_title.return_value = [c1]

    collabs = [SimpleNamespace(id_conversation=2, role="viewer")]
    mock_collaboration_dao.find_by_user.return_value = collabs

    m = SimpleNamespace(id_conversation=2)
    mock_message_dao.search_by_keyword.return_value = [m]

    def boom(_id):
        raise RuntimeError("DB error")

    mock_conversation_dao.get_by_id.side_effect = boom

    res = search_service.search_conversations_by_keyword(user_id=1, keyword="x")

    # On garde seulement c1, car get_by_id a levé une exception
    assert res == [c1]


def test_search_conversations_by_keyword_conv_getter_returns_none(
    search_service, mock_conversation_dao, mock_collaboration_dao, mock_message_dao
):
    c1 = SimpleNamespace(id_conversation=1, titre="T")
    mock_conversation_dao.search_conversations_by_title.return_value = [c1]

    collabs = [SimpleNamespace(id_conversation=2, role="viewer")]
    mock_collaboration_dao.find_by_user.return_value = collabs

    m = SimpleNamespace(id_conversation=2)
    mock_message_dao.search_by_keyword.return_value = [m]

    mock_conversation_dao.get_by_id.return_value = None

    res = search_service.search_conversations_by_keyword(user_id=1, keyword="x")

    # La conversation 2 n'est pas ajoutée car conv_getter retourne None
    assert res == [c1]


# -------------------------------------------------------------------
# search_conversations_by_date
# -------------------------------------------------------------------

def test_search_conversations_by_date_ok(search_service, mock_conversation_dao):
    d = datetime(2024, 2, 1)
    convs = [SimpleNamespace(id_conversation=1), SimpleNamespace(id_conversation=2)]
    mock_conversation_dao.get_conversations_by_date.return_value = convs

    res = search_service.search_conversations_by_date(user_id=10, target_date=d)

    mock_conversation_dao.get_conversations_by_date.assert_called_once_with(10, d)
    assert res == convs
