import pytest
from DAO.CollaborationDAO import CollaborationDAO
from ObjetMetier.Collaboration import Collaboration
from DAO.DBConnector import DBConnection

# Rôles (enum minuscule)
ROLE_ADMIN = "admin"
ROLE_WRITER = "writer"
ROLE_VIEWER = "viewer"
ROLE_BANNI = "banni"

# -----------------------------
# Fixtures d'initialisation
# -----------------------------

@pytest.fixture(scope="function", autouse=True)
def clean_tables():
    """
    État propre avant chaque test (respect des FK).
    """
    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE collaboration RESTART IDENTITY CASCADE;")
            cur.execute("TRUNCATE TABLE feedback RESTART IDENTITY CASCADE;")
            cur.execute("TRUNCATE TABLE message RESTART IDENTITY CASCADE;")
            cur.execute("TRUNCATE TABLE conversation RESTART IDENTITY CASCADE;")
            cur.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")
    yield

@pytest.fixture
def one_user():
    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, nom, prenom, mail, password_hash)
                VALUES ('u1','Nom','Prenom','u1@example.com','x')
                RETURNING id_user;
            """)
            return cur.fetchone()["id_user"]

@pytest.fixture
def another_user():
    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, nom, prenom, mail, password_hash)
                VALUES ('u2','Nom','Prenom','u2@example.com','x')
                RETURNING id_user;
            """)
            return cur.fetchone()["id_user"]

@pytest.fixture
def one_conversation():
    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conversation (titre)
                VALUES ('conv 1')
                RETURNING id_conversation;
            """)
            return cur.fetchone()["id_conversation"]

@pytest.fixture
def another_conversation():
    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conversation (titre)
                VALUES ('conv 2')
                RETURNING id_conversation;
            """)
            return cur.fetchone()["id_conversation"]

# -----------------------------
# Happy-path CRUD / finders
# -----------------------------

def test_create_and_read(one_user, one_conversation):
    dao = CollaborationDAO()
    c = Collaboration(0, one_conversation, one_user, ROLE_ADMIN)
    assert dao.create(c) is True
    assert c.id_collaboration > 0

    got = dao.read(c.id_collaboration)
    assert got is not None
    assert got.id_user == one_user
    assert got.id_conversation == one_conversation
    assert got.role == ROLE_ADMIN  # normalisé en minuscule

def test_list_and_finders(one_user, another_user, one_conversation):
    dao = CollaborationDAO()
    assert dao.create(Collaboration(0, one_conversation, one_user, ROLE_ADMIN))
    assert dao.create(Collaboration(0, one_conversation, another_user, ROLE_WRITER))

    # list_all
    all_rows = dao.list_all()
    assert len(all_rows) >= 2

    # find_by_conversation
    by_conv = dao.find_by_conversation(one_conversation)
    assert len(by_conv) == 2
    assert {r.id_user for r in by_conv} == {one_user, another_user}

    # find_by_user
    by_user = dao.find_by_user(one_user)
    assert len(by_user) == 1
    assert by_user[0].id_conversation == one_conversation
    assert by_user[0].role == ROLE_ADMIN

    # find_by_conversation_and_user
    one = dao.find_by_conversation_and_user(one_conversation, another_user)
    assert one is not None
    assert one.role == ROLE_WRITER

def test_update_and_update_role(one_user, one_conversation):
    dao = CollaborationDAO()
    c = Collaboration(0, one_conversation, one_user, ROLE_ADMIN)
    assert dao.create(c)

    # update complet
    c.role = ROLE_WRITER
    assert dao.update(c) is True
    got = dao.read(c.id_collaboration)
    assert got.role == ROLE_WRITER

    # update_role (doit écrire en minuscule pour l'enum)
    assert dao.update_role(c.id_collaboration, ROLE_ADMIN) is True
    got = dao.read(c.id_collaboration)
    assert got.role == ROLE_ADMIN

def test_count_and_deletes(one_user, one_conversation):
    dao = CollaborationDAO()
    c = Collaboration(0, one_conversation, one_user, ROLE_ADMIN)
    assert dao.create(c)

    total = dao.count_by_conversation(one_conversation)
    assert total == 1

    # delete par paire
    assert dao.delete_by_conversation_and_user(one_conversation, one_user) is True
    assert dao.find_by_conversation_and_user(one_conversation, one_user) is None

    # réinsère puis delete par id
    assert dao.create(c)
    assert dao.delete(c.id_collaboration) is True
    assert dao.read(c.id_collaboration) is None

# -----------------------------
# MUST-HAVE (robustesse)
# -----------------------------

def test_create_fk_violation():
    """
    FK inexistantes -> la création doit échouer proprement (False, pas d'exception non gérée).
    """
    dao = CollaborationDAO()
    bad = Collaboration(0, id_conversation=999999, id_user=999999, role=ROLE_ADMIN)
    assert dao.create(bad) is False

def test_unique_pair_violation(one_user, one_conversation):
    """
    Unicité (id_conversation, id_user) : le doublon doit échouer.
    """
    dao = CollaborationDAO()
    assert dao.create(Collaboration(0, one_conversation, one_user, ROLE_ADMIN))
    assert dao.create(Collaboration(0, one_conversation, one_user, ROLE_WRITER)) is False

def test_update_role_invalid(one_user, one_conversation):
    """
    update_role doit refuser un rôle hors enum et retourner False.
    """
    dao = CollaborationDAO()
    c = Collaboration(0, one_conversation, one_user, ROLE_ADMIN)
    assert dao.create(c)

    assert dao.update_role(c.id_collaboration, "superuser") is False
    # rôle inchangé
    got = dao.read(c.id_collaboration)
    assert got.role == ROLE_ADMIN

def test_delete_nonexistent():
    assert CollaborationDAO().delete(99999999) is False

def test_update_nonexistent(one_user, one_conversation):
    c = Collaboration(12345678, one_conversation, one_user, ROLE_WRITER)
    assert CollaborationDAO().update(c) is False

def test_role_normalization_on_create(one_user, one_conversation):
    """
    Même si on passe une casse bizarre, on doit écrire en minuscule en base.
    """
    dao = CollaborationDAO()
    c = Collaboration(0, one_conversation, one_user, "AdMiN")
    assert dao.create(c)
    got = dao.read(c.id_collaboration)
    assert got.role == ROLE_ADMIN

# -----------------------------
# NICE-TO-HAVE (confort)
# -----------------------------

def test_ordering_in_finders(one_user, another_user, one_conversation, another_conversation):
    """
    Vérifie les ORDER BY annoncés (id_user dans find_by_conversation, id_conversation dans find_by_user).
    """
    dao = CollaborationDAO()
    # même conversation, 2 users
    assert dao.create(Collaboration(0, one_conversation, another_user, ROLE_WRITER))
    assert dao.create(Collaboration(0, one_conversation, one_user, ROLE_ADMIN))

    # autre conversation pour one_user (pour tester l'ordre par id_conversation dans find_by_user)
    assert dao.create(Collaboration(0, another_conversation, one_user, ROLE_VIEWER))

    by_conv = dao.find_by_conversation(one_conversation)
    assert [r.id_user for r in by_conv] == sorted([one_user, another_user])

    by_user = dao.find_by_user(one_user)
    assert [r.id_conversation for r in by_user] == sorted([one_conversation, another_conversation])

def test_delete_by_pair_noop(one_user, one_conversation):
    """
    Supprimer une paire inexistante -> False, pas d'exception.
    """
    dao = CollaborationDAO()
    assert dao.delete_by_conversation_and_user(one_conversation, one_user) is False

def test_count_zero(one_conversation):
    """
    Pas de collaborateurs -> count == 0
    """
    assert CollaborationDAO().count_by_conversation(one_conversation) == 0
