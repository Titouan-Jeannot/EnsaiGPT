import os
import sys
from pathlib import Path
from types import SimpleNamespace

import importlib

import pytest
import psycopg2.pool

# Ensure imports resolve and prevent real DB connections
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost/db")
PROJECT_SRC = Path(__file__).resolve().parents[2]
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

OBJET_METIER = importlib.import_module("ObjetMetier")
sys.modules.setdefault("Objet_Metier", OBJET_METIER)
sys.modules.setdefault("src.Objet_Metier", OBJET_METIER)

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

from src.ObjetMetier.Collaboration import Collaboration
from src.Service.CollaborationService import CollaborationService
from src.Utils.Singleton import Singleton


class StubCollaborationDAO:
    def __init__(self):
        self.next_id = 1
        self.by_pair = {}
        self.by_id = {}
        self.created = []
        self.deleted = []

    def create(self, collaboration: Collaboration) -> bool:
        if collaboration.id_collaboration is None:
            collaboration.id_collaboration = self.next_id
            self.next_id += 1
        self.by_pair[(collaboration.id_conversation, collaboration.id_user)] = collaboration
        self.by_id[collaboration.id_collaboration] = collaboration
        self.created.append(collaboration)
        return True

    def find_by_conversation_and_user(self, conversation_id: int, user_id: int):
        return self.by_pair.get((conversation_id, user_id))

    def find_by_conversation(self, conversation_id: int):
        return [c for c in self.by_pair.values() if c.id_conversation == conversation_id]

    def delete_by_conversation_and_user(self, conversation_id: int, user_id: int) -> bool:
        collab = self.by_pair.pop((conversation_id, user_id), None)
        if not collab:
            return False
        self.by_id.pop(collab.id_collaboration, None)
        self.deleted.append((conversation_id, user_id))
        return True

    def update_role(self, id_collaboration: int, new_role: str) -> bool:
        collab = self.by_id.get(id_collaboration)
        if not collab:
            return False
        collab.role = new_role
        return True


class StubUserDAO:
    def __init__(self, existing=None):
        self.existing = set(existing or [])
        self.calls = []

    def set_existing(self, new_ids):
        self.existing = set(new_ids)

    def read(self, user_id: int):
        self.calls.append(user_id)
        return object() if user_id in self.existing else None


class StubConversationDAO:
    def __init__(self, conversations=None):
        self.conversations = conversations or {}
        self.calls = []

    def set_conversations(self, conversations):
        self.conversations = conversations

    def read(self, conversation_id: int):
        self.calls.append(conversation_id)
        return self.conversations.get(conversation_id)


@pytest.fixture
def service_setup(monkeypatch):
    collab_dao = StubCollaborationDAO()
    user_dao = StubUserDAO({1, 2, 3})
    conversation_dao = StubConversationDAO(
        {10: SimpleNamespace(token_viewer="viewer", token_writter="writer")}
    )

    monkeypatch.setattr("src.Service.CollaborationService.CollaborationDAO", lambda: collab_dao)
    monkeypatch.setattr("src.Service.CollaborationService.UserDAO", lambda: user_dao)
    monkeypatch.setattr("src.Service.CollaborationService.ConversationDAO", lambda: conversation_dao)

    Singleton._instances.pop(CollaborationService, None)
    service = CollaborationService()

    # assure the service uses the stub instances
    service.collab_dao = collab_dao
    service.user_dao = user_dao
    service.conversation_dao = conversation_dao
    return service, collab_dao, user_dao, conversation_dao


def test_role_checks(service_setup):
    service, collab_dao, _, _ = service_setup
    collab_dao.create(Collaboration(id_conversation=10, id_user=1, role="admin"))
    collab_dao.create(Collaboration(id_conversation=10, id_user=2, role="writer"))
    collab_dao.create(Collaboration(id_conversation=10, id_user=3, role="viewer"))

    assert service.is_admin(1, 10) is True
    assert service.is_admin(4, 10) is False
    assert service.is_writer(2, 10) is True
    assert service.is_writer(1, 10) is False
    assert service.is_viewer(3, 10) is True
    assert service.is_viewer(5, 10) is False


def test_create_collab_success(service_setup):
    service, collab_dao, _, _ = service_setup

    created = service.create_collab(user_id=1, conversation_id=10, role="admin")

    assert created is True
    assert collab_dao.created
    stored = collab_dao.find_by_conversation_and_user(10, 1)
    assert stored is not None and stored.role == "admin"


def test_create_collab_missing_user(service_setup):
    service, _, user_dao, _ = service_setup
    user_dao.set_existing(set())

    assert service.create_collab(user_id=9, conversation_id=10, role="admin") is False


def test_create_collab_missing_conversation(service_setup):
    service, _, _, conversation_dao = service_setup
    conversation_dao.set_conversations({})

    assert service.create_collab(user_id=1, conversation_id=99, role="admin") is False


def test_create_collab_invalid_role(service_setup):
    service, _, _, _ = service_setup

    assert service.create_collab(user_id=1, conversation_id=10, role="invalid") is False


def test_create_collab_duplicate(service_setup):
    service, collab_dao, _, _ = service_setup
    service.create_collab(user_id=1, conversation_id=10, role="admin")

    assert service.create_collab(user_id=1, conversation_id=10, role="admin") is False
    assert len(collab_dao.created) == 1


def test_add_collaboration(service_setup):
    service, collab_dao, _, _ = service_setup
    collab = Collaboration(id_conversation=10, id_user=5, role="viewer")

    result = service.add_collaboration(collab)

    assert result is True
    assert collab_dao.find_by_conversation_and_user(10, 5) is not None


def test_list_collaborators(service_setup):
    service, collab_dao, _, _ = service_setup
    collab_dao.create(Collaboration(id_conversation=10, id_user=1, role="admin"))
    collab_dao.create(Collaboration(id_conversation=10, id_user=2, role="writer"))

    collaborators = service.list_collaborators(10)

    assert len(collaborators) == 2
    assert {c.id_user for c in collaborators} == {1, 2}


def test_delete_collaborator(service_setup):
    service, collab_dao, _, _ = service_setup
    collab_dao.create(Collaboration(id_conversation=10, id_user=2, role="viewer"))

    assert service.delete_collaborator(10, 2) is True
    assert service.delete_collaborator(10, 2) is False


def test_change_role_missing_collaboration(service_setup):
    service, _, _, _ = service_setup
    assert service.change_role(10, 5, "writer") is False


def test_change_role_success(service_setup):
    service, collab_dao, _, _ = service_setup
    collab = Collaboration(id_conversation=10, id_user=6, role="viewer")
    collab_dao.create(collab)

    assert service.change_role(10, 6, "writer") is True
    updated = collab_dao.find_by_conversation_and_user(10, 6)
    assert updated.role == "writer"


def test_verify_token_collaboration_missing_conversation(service_setup):
    service, _, _, conversation_dao = service_setup
    conversation_dao.set_conversations({})

    assert service.verify_token_collaboration(99, "viewer") is False


def test_verify_token_collaboration_match(service_setup):
    service, _, _, _ = service_setup

    assert service.verify_token_collaboration(10, "viewer") is True
    assert service.verify_token_collaboration(10, "writer") is True
    assert service.verify_token_collaboration(10, "other") is False
