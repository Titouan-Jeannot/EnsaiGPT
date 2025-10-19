import pytest
from datetime import datetime

# Import du DAO et du modèle User en tenant compte du chemin du projet
try:
    from DAO.user_DAO import UserDAO
    from Objet_Metier.User import User
except Exception:
    from src.DAO.user_DAO import UserDAO
    from src.Objet_Metier.User import User


class FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None,
                 raise_on_execute=False, rowcount=1):
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result
        self.raise_on_execute = raise_on_execute
        self.rowcount = rowcount
        self.last_query = None
        self.last_params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=None):
        self.last_query = query
        self.last_params = params
        if self.raise_on_execute:
            raise Exception("db execute error")

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result


class FakeConnection:
    def __init__(self, cursor_obj: FakeCursor):
        self._cursor_obj = cursor_obj
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self, *args, **kwargs):
        # Retourne l'objet cursor configuré
        return self._cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def make_user(id=1, username="u1"):
    return User(
        id,
        username,
        "Nom",
        "Prenom",
        "mail@example.com",
        "hash",
        "salt",
        datetime(2020, 1, 1),
        datetime(2020, 1, 2),
        "active",
        "param",
    )


def make_dao_with_cursor(cursor: FakeCursor):
    conn = FakeConnection(cursor)
    return UserDAO(conn=conn), conn, cursor


def test_init_requires_conn_or_dsn():
    with pytest.raises(ValueError):
        UserDAO()


def test_create_user_success():
    # setup: fetchone returns assigned id and timestamps
    row = {"id": 10, "sign_in_date": datetime(2021, 1, 1), "last_login": None}
    cur = FakeCursor(fetchone_result=row)
    dao, conn, cursor = make_dao_with_cursor(cur)

    u = make_user(id=0)
    created = dao.create_user(u)

    assert created is not None
    assert created.id == 10
    # commit called once
    assert conn.commits == 1
    assert conn.rollbacks == 0


def test_create_user_no_row_returns_none():
    cur = FakeCursor(fetchone_result=None)
    dao, conn, cursor = make_dao_with_cursor(cur)
    u = make_user(id=0)
    created = dao.create_user(u)
    assert created is None
    assert conn.commits == 1
    assert conn.rollbacks == 0


def test_create_user_exception_rolls_back():
    cur = FakeCursor(raise_on_execute=True)
    dao, conn, cursor = make_dao_with_cursor(cur)
    with pytest.raises(Exception):
        dao.create_user(make_user(id=0))
    assert conn.commits == 0
    assert conn.rollbacks == 1


def test_get_by_id_found():
    row = {"id": 5, "username": "u5", "nom": "N", "prenom": "P", "mail": "a@b",
           "password_hash": "h", "salt": "s", "sign_in_date": None, "last_login": None,
           "status": "active", "setting_param": "p"}
    cur = FakeCursor(fetchone_result=row)
    dao, conn, cursor = make_dao_with_cursor(cur)
    u = dao.get_by_id(5)
    assert u is not None
    assert u.id == 5
    assert u.username == "u5"


def test_get_by_id_not_found():
    cur = FakeCursor(fetchone_result=None)
    dao, conn, cursor = make_dao_with_cursor(cur)
    u = dao.get_by_id(999)
    assert u is None


def test_get_by_username_found():
    row = {"id": 6, "username": "u6", "nom": "N", "prenom": "P", "mail": "c@d",
           "password_hash": "h", "salt": "s", "sign_in_date": None, "last_login": None,
           "status": "active", "setting_param": "p"}
    cur = FakeCursor(fetchone_result=row)
    dao, conn, cursor = make_dao_with_cursor(cur)
    u = dao.get_by_username("u6")
    assert u is not None
    assert u.username == "u6"


def test_update_user_success_and_failure():
    # success
    cur_success = FakeCursor(rowcount=1)
    dao_succ, conn_succ, cur = make_dao_with_cursor(cur_success)
    ok = dao_succ.update_user(make_user(id=2))
    assert ok is True
    assert conn_succ.commits == 1
    assert conn_succ.rollbacks == 0

    # failure (rowcount 0)
    cur_fail = FakeCursor(rowcount=0)
    dao_fail, conn_fail, curf = make_dao_with_cursor(cur_fail)
    ok2 = dao_fail.update_user(make_user(id=2))
    assert ok2 is False
    assert conn_fail.commits == 1


def test_update_user_exception_rolls_back():
    cur = FakeCursor(raise_on_execute=True)
    dao, conn, cursor = make_dao_with_cursor(cur)
    with pytest.raises(Exception):
        dao.update_user(make_user(id=3))
    assert conn.rollbacks == 1


def test_delete_user_success_and_failure():
    cur_success = FakeCursor(rowcount=1)
    dao_s, conn_s, _ = make_dao_with_cursor(cur_success)
    assert dao_s.delete_user(1) is True
    assert conn_s.commits == 1

    cur_fail = FakeCursor(rowcount=0)
    dao_f, conn_f, _ = make_dao_with_cursor(cur_fail)
    assert dao_f.delete_user(999) is False
    assert conn_f.commits == 1


def test_delete_user_exception_rolls_back():
    cur = FakeCursor(raise_on_execute=True)
    dao, conn, _ = make_dao_with_cursor(cur)
    with pytest.raises(Exception):
        dao.delete_user(1)
    assert conn.rollbacks == 1


def test_list_users_returns_list():
    rows = [
        {"id": 1, "username": "a", "nom": "N", "prenom": "P", "mail": "a@b",
         "password_hash": "h", "salt": "s", "sign_in_date": None, "last_login": None,
         "status": "active", "setting_param": "p"},
        {"id": 2, "username": "b", "nom": "N", "prenom": "P", "mail": "b@b",
         "password_hash": "h", "salt": "s", "sign_in_date": None, "last_login": None,
         "status": "active", "setting_param": "p"},
    ]
    cur = FakeCursor(fetchall_result=rows)
    dao, conn, _ = make_dao_with_cursor(cur)
    lst = dao.list_users()
    assert isinstance(lst, list)
    assert len(lst) == 2
    assert lst[0].id == 1
    assert lst[1].username == "b"


def test_row_to_user_conversion():
    row = {"id": 7, "username": "u7", "nom": None, "prenom": None, "mail": "x@y",
           "password_hash": "h", "salt": "s", "sign_in_date": None, "last_login": None,
           "status": None, "setting_param": None}
    cur = FakeCursor()
    dao, conn, _ = make_dao_with_cursor(cur)
    u = dao._row_to_user(row)
    assert u.id == 7
    assert u.nom == ""
    assert u.status == ""
