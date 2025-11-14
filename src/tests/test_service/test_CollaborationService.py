import os
import sys
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime

import importlib
import pytest
import psycopg2.pool


# --------------------------------------------------------------------
# Chemins & environnement : pointer vers le dossier 'src' du projet
# --------------------------------------------------------------------
# Ce fichier est supposé être dans: <repo>/src/tests/test_service/...
# parents[3] => <repo>/src
SRC_DIR = Path(__file__).resolve().parents[3]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Évite toute connexion réelle à une DB
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost/db")


# --------------------------------------------------------------------
# Stub de pool psycopg2 -> aucune vraie connexion n'est faite
# --------------------------------------------------------------------
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


psycopg2.pool.SimpleConnectionPool = _DummyPool  # type: ignore


# --------------------------------------------------------------------
# Imports après configuration du chemin
# --------------------------------------------------------------------
from ObjetMetier.Collaboration import Collaboration
from Service.CollaborationService import CollaborationService
from Utils.Singleton import Singleton


# --------------------------------------------------------------------
# Stubs DAO
# --------------------------------------------------------------------
class StubCollaborationDAO:
    def __init__(self):
        self.next_id = 1
        self.by_pair = {}
        self.by_id = {}
        self.created = []
        self.deleted = []

    def create(self, collaboration: Collaboration) -> bool:
        if getattr(collaboration, "id_collaboration", None) in (None, 0):
            collaboration.id_collaboration = self.next_id
            self.next_id += 1
        self.by_pair[(collaboration.id_conversation, collaboration.id_user)] = collaboration
        self.by_id[collaboration.id_collaboration] = collaboration
        self.created.append(collaboration)
        return True

    # pour compat : certains services peuvent appeler add_collaboration
    def add_collaboration(self, collaboration: Collaboration) -> bool:
        return self.create(collaboration)

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

    # au cas où le service attendrait un user courant
    def get_current_user_id(self) -> int:
        # valeur fictive mais stable
        return 1


class StubConversationDAO:
    def __init__(self, conversations=None):
        self.conversations = conversations or {}
        self.calls = []

    def set_conversations(self, conversations):
        self.conversations = conversations

    def read(self, conversation_id: int):
        self.calls.append(conversation_id)
        return self.conversations.get(conversation_id)


# --------------------------------------------------------------------
# Fixture service avec monkeypatch des DAO dans le module cible
# --------------------------------------------------------------------
@pytest.fixture
def service_setup(monkeypatch):
    collab_dao = StubCollaborationDAO()
    user_dao = StubUserDAO({1, 2, 3})
    conversation_dao = StubConversationDAO(
        {10: SimpleNamespace(token_viewer="viewer", token_writter="writer")}
    )

    # Monkeypatcher les classes importées dans le module de service
    monkeypatch.setattr("Service.CollaborationService.CollaborationDAO", lambda: collab_dao)
    monkeypatch.setattr("Service.CollaborationService.UserDAO", lambda: user_dao)
    monkeypatch.setattr("Service.CollaborationService.ConversationDAO", lambda: conversation_dao)

    # Reset le singleton si le service l'utilise
    Singleton._instances.pop(CollaborationService, None)

    service = CollaborationService()

    # Sécurité : exposer toutes les variantes potentielles de noms utilisés par le service
    service.collab_dao = collab_dao
    service.collaboration_dao = collab_dao           # parfois le code utilise ce nom
    service.collaboration_service = collab_dao       # si un appel se trompe d'attribut (ex: add_collaboration)
    service.user_dao = user_dao
    service.user_service = user_dao                  # si le service appelle get_current_user_id()
    service.conversation_dao = conversation_dao

    return service, collab_dao, user_dao, conversation_dao


# --------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------
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



# --- Tests pour add_collab_by_token -----------------------------------------

def test_add_collab_by_token_missing_conversation(service_setup):
    service, collab_dao, _, conversation_dao = service_setup
    # plus aucune conversation connue
    conversation_dao.set_conversations({})

    ok = service.add_collab_by_token(conversation_id=99, token="viewer", user_id=1)
    assert ok is False
    # rien n'a été créé
    assert collab_dao.find_by_conversation_and_user(99, 1) is None


def test_add_collab_by_token_viewer(service_setup):
    service, collab_dao, _, _ = service_setup
    # conversation 10 existe avec token_viewer="viewer" (défini dans la fixture)
    ok = service.add_collab_by_token(conversation_id=10, token="viewer", user_id=1)
    assert ok is True

    created = collab_dao.find_by_conversation_and_user(10, 1)
    assert created is not None
    assert created.role.lower() == "viewer"


def test_add_collab_by_token_writer(service_setup):
    service, collab_dao, _, _ = service_setup
    # conversation 10 existe avec token_writter="writer"
    ok = service.add_collab_by_token(conversation_id=10, token="writer", user_id=2)
    assert ok is True

    created = collab_dao.find_by_conversation_and_user(10, 2)
    assert created is not None
    assert created.role.lower() == "writer"


def test_add_collab_by_token_invalid_token(service_setup):
    service, collab_dao, _, _ = service_setup
    ok = service.add_collab_by_token(conversation_id=10, token="badtoken", user_id=3)
    assert ok is False
    assert collab_dao.find_by_conversation_and_user(10, 3) is None


def test_add_collab_by_token_user_not_found(service_setup):
    service, collab_dao, user_dao, _ = service_setup
    # fait en sorte que le user n'existe pas → create_collab renverra False
    user_dao.set_existing(set())

    ok = service.add_collab_by_token(conversation_id=10, token="viewer", user_id=999)
    assert ok is False
    assert collab_dao.find_by_conversation_and_user(10, 999) is None
