import os
import sys
from pathlib import Path
from datetime import datetime

import importlib

import pytest
import psycopg2.pool

# Ensure project modules are importable and avoid real database connections.
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost/db")
PROJECT_SRC = Path(__file__).resolve().parents[2]
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

OBJET_METIER = importlib.import_module("ObjetMetier")
sys.modules.setdefault("ObjetMetier", OBJET_METIER)
sys.modules.setdefault("src.ObjetMetier", OBJET_METIER)

UTILS_MODULE = importlib.import_module("Utils")
sys.modules.setdefault("src.Utils", UTILS_MODULE)


class _DummyCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, *args, **kwargs):
        return None

    def fetchone(self):
        return None

    def fetchall(self):
        return []


class _DummyConnection:
    def __init__(self):
        self.autocommit = False

    def cursor(self):
        return _DummyCursor()

    def commit(self):
        return None

    def rollback(self):
        return None


class _DummyPool:
    def __init__(self, *args, **kwargs):
        pass

    def closeall(self):
        return None

    def getconn(self):
        return _DummyConnection()

    def putconn(self, conn):
        return None


psycopg2.pool.SimpleConnectionPool = _DummyPool

from src.ObjetMetier.Conversation import Conversation
from src.Service.ConversationService import ConversationService


class FakeConversationDAO:
    def __init__(self):
        self.next_id = 1
        self.storage = {}
        self.access = set()
        self.write_access = set()
        self.by_user = {}
        self.by_date = {}
        self.by_title = {}
        self.updated_titles = []
        self.deleted_ids = []
        self.set_active_calls = []
        self.added_access = []

    # Helpers used by tests -------------------------------------------------
    def grant_access(self, conversation_id: int, user_id: int, can_write: bool = False):
        self.access.add((conversation_id, user_id))
        if can_write:
            self.write_access.add((conversation_id, user_id))

    # DAO API used by the service -------------------------------------------
    def create(self, conversation: Conversation, user_id: int) -> Conversation:
        if conversation.id_conversation is None:
            conversation.id_conversation = self.next_id
            self.next_id += 1
        self.storage[conversation.id_conversation] = conversation
        return conversation

    def get_by_id(self, conversation_id: int):
        return self.storage.get(conversation_id)

    def has_access(self, conversation_id: int, user_id: int) -> bool:
        return (conversation_id, user_id) in self.access

    def get_conversations_by_user(self, user_id: int):
        return self.by_user.get(user_id, [])

    def get_conversations_by_date(self, user_id: int, target_date: datetime):
        key = (user_id, target_date.date())
        return self.by_date.get(key, [])

    def search_conversations_by_title(self, user_id: int, title: str):
        key = (user_id, title)
        return self.by_title.get(key, [])

    def has_write_access(self, conversation_id: int, user_id: int) -> bool:
        return (conversation_id, user_id) in self.write_access

    def update_title(self, conversation_id: int, new_title: str) -> None:
        self.updated_titles.append((conversation_id, new_title))

    def delete(self, conversation_id: int) -> None:
        self.deleted_ids.append(conversation_id)

    def set_active(self, conversation_id: int, is_active: bool) -> None:
        self.set_active_calls.append((conversation_id, is_active))

    def add_user_access(self, conversation_id: int, user_id: int, can_write: bool) -> None:
        self.added_access.append((conversation_id, user_id, can_write))
        self.grant_access(conversation_id, user_id, can_write)


class DummyUserService:
    def __init__(self, users):
        self.users = users
        self.lookups = []

    def get_user_by_id(self, user_id: int):
        self.lookups.append(user_id)
        return self.users.get(user_id)


class DummyCollaborationService:
    def __init__(self, admins=None):
        self.admins = set(admins or [])
        self.created = []

    def is_admin(self, user_id: int, conversation_id: int) -> bool:
        return (user_id, conversation_id) in self.admins

    def create_collab(self, user_id: int, conversation_id: int, role: str) -> bool:
        self.admins.add((user_id, conversation_id))
        self.created.append((user_id, conversation_id, role))
        return True


class DummyMessageService:
    def __init__(self):
        self.deleted = []

    def delete_all_messages_by_conversation(self, conversation_id: int) -> None:
        self.deleted.append(conversation_id)


@pytest.fixture
def dao():
    return FakeConversationDAO()


@pytest.fixture
def fixed_tokens(monkeypatch):
    tokens = iter(["view-token", "write-token"])
    monkeypatch.setattr(
        "src.Service.ConversationService.secrets.token_urlsafe",
        lambda _: next(tokens),
    )


@pytest.fixture
def fixed_datetime(monkeypatch):
    fixed = datetime(2024, 1, 1, 12, 0, 0)

    class _FixedDateTime:
        @staticmethod
        def now():
            return fixed

    monkeypatch.setattr("src.Service.ConversationService.datetime", _FixedDateTime)
    return fixed


def build_conversation(**kwargs) -> Conversation:
    defaults = dict(
        id_conversation=1,
        titre="Projet ENSAI",
        created_at=datetime(2024, 1, 1, 10, 0, 0),
        setting_conversation="cfg",
        token_viewer="tv",
        token_writter="tw",
        is_active=True,
    )
    defaults.update(kwargs)
    return Conversation(**defaults)


def test_create_conversation_success(dao, fixed_tokens, fixed_datetime):
    user_service = DummyUserService({1: object()})
    collab_service = DummyCollaborationService()
    service = ConversationService(
        dao, collaboration_service=collab_service, user_service=user_service
    )

    conv = service.create_conversation("  Projet  ", user_id=1, setting_conversation="cfg")

    assert conv.id_conversation == 1
    assert conv.titre == "Projet"
    assert conv.token_viewer == "view-token"
    assert conv.token_writter == "write-token"
    assert collab_service.created == [(1, 1, "admin")]
    assert user_service.lookups == [1]


def test_create_conversation_unknown_user(dao, fixed_tokens):
    user_service = DummyUserService({})
    service = ConversationService(dao, user_service=user_service)

    with pytest.raises(ValueError, match="Utilisateur introuvable"):
        service.create_conversation("Titre", user_id=5)


def test_create_conversation_invalid_title():
    dao = FakeConversationDAO()
    service = ConversationService(dao)

    with pytest.raises(ValueError, match="Titre invalide"):
        service.create_conversation("   ", user_id=1)


def test_get_conversation_by_id_invalid_argument(dao):
    service = ConversationService(dao)

    with pytest.raises(ValueError, match="ID de conversation invalide"):
        service.get_conversation_by_id("bad", user_id=1)  # type: ignore[arg-type]


def test_get_conversation_by_id_not_found(dao):
    service = ConversationService(dao)
    assert service.get_conversation_by_id(1, user_id=99) is None


def test_get_conversation_by_id_without_access(dao):
    service = ConversationService(dao)
    dao.storage[1] = build_conversation(id_conversation=1)

    with pytest.raises(ValueError, match="Acc"):
        service.get_conversation_by_id(1, user_id=1)


def test_get_conversation_by_id_success(dao):
    service = ConversationService(dao)
    dao.storage[2] = build_conversation(id_conversation=2)
    dao.grant_access(2, 7)

    conv = service.get_conversation_by_id(2, user_id=7)
    assert conv.id_conversation == 2


def test_get_list_conv(dao):
    service = ConversationService(dao)
    expected = [build_conversation(id_conversation=5)]
    dao.by_user[3] = expected

    assert service.get_list_conv(3) == expected


def test_get_list_conv_by_date(dao):
    service = ConversationService(dao)
    date_key = datetime(2024, 5, 1, 8, 0, 0)
    convs = [build_conversation(id_conversation=8)]
    dao.by_date[(4, date_key.date())] = convs

    assert service.get_list_conv_by_date(4, date_key) == convs


def test_get_list_conv_by_title_invalid(dao):
    service = ConversationService(dao)
    with pytest.raises(ValueError, match="Crit"):
        service.get_list_conv_by_title(4, "   ")


def test_get_list_conv_by_title_success(dao):
    service = ConversationService(dao)
    convs = [build_conversation(id_conversation=9)]
    dao.by_title[(4, "Projet")] = convs

    assert service.get_list_conv_by_title(4, "Projet") == convs


def test_modify_title_requires_admin(dao):
    collab_service = DummyCollaborationService()
    service = ConversationService(dao, collaboration_service=collab_service)

    with pytest.raises(ValueError, match="Droits d'administration"):
        service.modify_title(1, user_id=2, new_title="Nouveau")


def test_modify_title_invalid_new_title(dao):
    service = ConversationService(dao)  # no collaboration service -> skip admin check
    dao.write_access.add((1, 1))

    with pytest.raises(ValueError, match="Nouveau titre invalide"):
        service.modify_title(1, user_id=1, new_title="   ")


def test_modify_title_requires_write_access(dao):
    collab_service = DummyCollaborationService(admins={(1, 1)})
    service = ConversationService(dao, collaboration_service=collab_service)

    with pytest.raises(ValueError, match="Droits"):
        service.modify_title(1, user_id=1, new_title="Titre")


def test_modify_title_success(dao):
    collab_service = DummyCollaborationService(admins={(1, 1)})
    service = ConversationService(dao, collaboration_service=collab_service)
    dao.write_access.add((1, 1))

    service.modify_title(1, user_id=1, new_title="Nouveau")

    assert dao.updated_titles == [(1, "Nouveau")]


def test_delete_conversation_requires_admin(dao):
    collab_service = DummyCollaborationService()
    service = ConversationService(dao, collaboration_service=collab_service)

    with pytest.raises(ValueError, match="Droits d'administration"):
        service.delete_conversation(1, user_id=3)


def test_delete_conversation_requires_write_access(dao):
    collab_service = DummyCollaborationService(admins={(3, 1)})
    service = ConversationService(dao, collaboration_service=collab_service)

    with pytest.raises(ValueError, match="Droits"):
        service.delete_conversation(1, user_id=3)


def test_delete_conversation_calls_message_service(dao):
    collab_service = DummyCollaborationService(admins={(4, 2)})
    message_service = DummyMessageService()
    service = ConversationService(
        dao,
        collaboration_service=collab_service,
        message_service=message_service,
    )
    dao.write_access.add((2, 4))

    service.delete_conversation(2, user_id=4)

    assert message_service.deleted == [2]
    assert dao.deleted_ids == [2]


def test_archive_conversation_requires_write_access(dao):
    service = ConversationService(dao)
    with pytest.raises(ValueError, match="Droits"):
        service.archive_conversation(1, user_id=1)


def test_archive_conversation_success(dao):
    service = ConversationService(dao)
    dao.write_access.add((1, 1))

    service.archive_conversation(1, user_id=1)

    assert dao.set_active_calls == [(1, False)]


def test_restore_conversation_requires_write_access(dao):
    service = ConversationService(dao)
    with pytest.raises(ValueError, match="Droits"):
        service.restore_conversation(1, user_id=1)


def test_restore_conversation_success(dao):
    service = ConversationService(dao)
    dao.write_access.add((1, 1))

    service.restore_conversation(1, user_id=1)

    assert dao.set_active_calls == [(1, True)]


def test_share_conversation_requires_write_access(dao):
    user_service = DummyUserService({2: object()})
    service = ConversationService(dao, user_service=user_service)
    with pytest.raises(ValueError, match="Droits"):
        service.share_conversation(1, user_id=1, target_user_id=2)


def test_share_conversation_unknown_user(dao):
    dao.write_access.add((1, 1))
    user_service = DummyUserService({})
    service = ConversationService(dao, user_service=user_service)

    with pytest.raises(ValueError, match="Utilisateur cible introuvable"):
        service.share_conversation(1, user_id=1, target_user_id=2)


def test_share_conversation_success(dao):
    dao.write_access.add((1, 1))
    user_service = DummyUserService({2: object()})
    service = ConversationService(dao, user_service=user_service)

    service.share_conversation(1, user_id=1, target_user_id=2, can_write=True)

    assert dao.added_access == [(1, 2, True)]
    assert (1, 2) in dao.write_access
