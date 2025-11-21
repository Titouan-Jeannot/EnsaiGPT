import pytest
import time
import base64
from datetime import datetime, timezone

from Service.AuthService import AuthService
from ObjetMetier.User import User
from DAO.UserDAO import UserDAO
from DAO.DBConnector import DBConnection


# ============================================================
# Helpers DB
# ============================================================

def _table_exists(name: str) -> bool:
    try:
        with DBConnection().connection as c:
            with c.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name=%s LIMIT 1;
                """, (name,))
                return cur.fetchone() is not None
    except Exception:
        return False


def _insert_user(email, username, nom, prenom, pwd_hash, salt, status="active"):
    """
    INSERT correct respecting the real DB schema.
    sign_in_date + last_login are required → use NOW()
    """
    with DBConnection().connection as c:
        with c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users
                (username, nom, prenom, mail, password_hash,
                 sign_in_date, last_login, status, setting_param, salt)
                VALUES (%s,%s,%s,%s,%s, NOW(), NOW(), %s, %s, %s)
                RETURNING id_user;
                """,
                (username, nom, prenom, email, pwd_hash, status, "test", salt),
            )
            row = cur.fetchone()
        c.commit()

    if not row:
        raise RuntimeError(f"INSERT user failed for username={username}")

    return row["id_user"]


def _read_user(id_user: int):
    with DBConnection().connection as c:
        with c.cursor() as cur:
            cur.execute("""
                SELECT id_user, username, nom, prenom, mail,
                       password_hash, salt, status
                FROM users WHERE id_user=%s;
            """, (id_user,))
            row = cur.fetchone()

            if not row:
                return None

            return User(
                id=row["id_user"],
                username=row["username"],
                nom=row["nom"],
                prenom=row["prenom"],
                mail=row["mail"],
                password_hash=row["password_hash"],
                salt=row["salt"],
                status=row["status"],
            )


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="module")
def infra_ok():
    if not _table_exists("users"):
        pytest.fail("Table 'users' absente dans la base de tests.")
    return True


@pytest.fixture
def user_dao():
    return UserDAO()


@pytest.fixture
def auth_service(user_dao):
    return AuthService(user_dao)


# ============================================================
# Tests salt / hash
# ============================================================

def test_generate_salt_valid(auth_service):
    s = auth_service.generate_salt()
    decoded = base64.b64decode(s)
    assert isinstance(s, str)
    assert len(decoded) == auth_service.SALT_LEN


def test_hash_and_verify_password(auth_service):
    salt = auth_service.generate_salt()
    h = auth_service.hash_mdp("Bonjour123!", salt)
    assert auth_service.verify_mdp("Bonjour123!", h, salt) is True
    assert auth_service.verify_mdp("wrong", h, salt) is False


# ============================================================
# Tests authenticate() with real DB
# ============================================================

def test_authenticate_success(infra_ok, auth_service):
    salt = auth_service.generate_salt()
    h = auth_service.hash_mdp("Pwd1234!", salt)

    email = f"auth_ok_{time.time_ns()}@example.com"
    username = f"u_ok_{time.time_ns()}"

    uid = _insert_user(email, username, "Test", "User", h, salt)

    user = auth_service.authenticate(email, "Pwd1234!")
    assert user is not None
    assert user.id == uid


def test_authenticate_wrong_password(infra_ok, auth_service):
    salt = auth_service.generate_salt()
    h = auth_service.hash_mdp("CorrectPwd!", salt)

    email = f"auth_fail_{time.time_ns()}@example.com"
    username = f"u_fail_{time.time_ns()}"

    _insert_user(email, username, "x", "y", h, salt)

    got = auth_service.authenticate(email, "BADPWD")
    assert got is None
    assert email in auth_service._last_failed


def test_authenticate_missing_user_registers_failure(infra_ok, auth_service):
    email = f"unknown_{time.time_ns()}@example.com"
    got = auth_service.authenticate(email, "abc")
    assert got is None
    assert email in auth_service._last_failed


def test_authenticate_blocked_after_recent_failure(infra_ok, auth_service):
    email = f"blocked_{time.time_ns()}@example.com"
    auth_service._last_failed[email] = datetime.now(timezone.utc)

    got = auth_service.authenticate(email, "whatever")
    assert got is None


# ============================================================
# check_user_* (DB-backed)
# ============================================================

def test_check_user_exists(infra_ok, auth_service):
    salt = auth_service.generate_salt()
    h = auth_service.hash_mdp("Pwd1234!", salt)

    email = f"exists_{time.time_ns()}@example.com"
    username = f"u_exists_{time.time_ns()}"

    uid = _insert_user(email, username, "N", "P", h, salt)

    assert auth_service.check_user_exists(uid) is True


def test_check_user_exists_raises(auth_service):
    with pytest.raises(ValueError):
        auth_service.check_user_exists(9999999)


def test_check_user_password(infra_ok, auth_service):
    salt = auth_service.generate_salt()
    h = auth_service.hash_mdp("Secu123!", salt)

    email = f"pw_{time.time_ns()}@example.com"
    username = f"u_pw_{time.time_ns()}"

    uid = _insert_user(email, username, "N", "P", h, salt)

    assert auth_service.check_user_password(uid, "Secu123!") is True


def test_check_user_password_wrong(infra_ok, auth_service):
    salt = auth_service.generate_salt()
    h = auth_service.hash_mdp("GoodPass!", salt)

    email = f"badpw_{time.time_ns()}@example.com"
    username = f"u_badpw_{time.time_ns()}"

    uid = _insert_user(email, username, "N", "P", h, salt)

    with pytest.raises(ValueError):
        auth_service.check_user_password(uid, "WRONG")


def test_check_user_email_uniqueness(infra_ok, auth_service):
    salt = auth_service.generate_salt()
    h = auth_service.hash_mdp("AAaa11!!", salt)

    email1 = f"em1_{time.time_ns()}@example.com"
    email2 = f"em2_{time.time_ns()}@example.com"

    u1 = f"u_em1_{time.time_ns()}"
    u2 = f"u_em2_{time.time_ns()}"

    uid1 = _insert_user(email1, u1, "x", "y", h, salt)

    assert auth_service.check_user_email(uid1, email2) is True

    _insert_user(email2, u2, "x", "y", h, salt)
    with pytest.raises(ValueError):
        auth_service.check_user_email(uid1, email2)


def test_check_user_username_rules(infra_ok, auth_service):
    email = f"usr_{time.time_ns()}@ex.com"
    username = f"u_usr_{time.time_ns()}"

    uid = _insert_user(email, username, "n", "p", "hash", "salt")

    assert auth_service.check_user_username(uid, "valid_name") is True

    for bad in ["", "ab", "x"*31, "bad space", "ééé"]:
        with pytest.raises(ValueError):
            auth_service.check_user_username(uid, bad)


def test_check_user_nom_prenom(infra_ok, auth_service):
    email = f"np_{time.time_ns()}@ex.com"
    username = f"u_np_{time.time_ns()}"

    uid = _insert_user(email, username, "good", "good", "hash", "salt")

    assert auth_service.check_user_nom(uid, "Dupont") is True
    assert auth_service.check_user_prenom(uid, "Alice") is True

    with pytest.raises(ValueError):
        auth_service.check_user_nom(uid, "x"*60)
    with pytest.raises(ValueError):
        auth_service.check_user_prenom(uid, "x"*60)


def test_check_user_can_update_and_delete(infra_ok, auth_service):
    salt = auth_service.generate_salt()
    h = auth_service.hash_mdp("AAAaaa11!!", salt)

    email1 = f"cu_{time.time_ns()}@ex.com"
    u1 = f"u_cu_{time.time_ns()}"

    uid1 = _insert_user(email1, u1, "n", "p", h, salt, status="active")
    assert auth_service.check_user_can_update(uid1) is True
    assert auth_service.check_user_can_delete(uid1) is True

    email2 = f"ban_{time.time_ns()}@ex.com"
    u2 = f"u_ban_{time.time_ns()}"

    uid2 = _insert_user(email2, u2, "n", "p", h, salt, status="banni")
    with pytest.raises(ValueError):
        auth_service.check_user_can_update(uid2)


def test_check_user_not_banned_or_deleted(infra_ok, auth_service):
    salt = auth_service.generate_salt()
    h = auth_service.hash_mdp("AAbb11!!", salt)

    email1 = f"ok_{time.time_ns()}@ex.com"
    u1 = f"u_ok_{time.time_ns()}"

    uid1 = _insert_user(email1, u1, "n", "p", h, salt, status="active")
    assert auth_service.check_user_not_banned_or_deleted(uid1) is True

    email2 = f"bad_{time.time_ns()}@ex.com"
    u2 = f"u_bad_{time.time_ns()}"

    uid2 = _insert_user(email2, u2, "n", "p", h, salt, status="banni")
    with pytest.raises(ValueError):
        auth_service.check_user_not_banned_or_deleted(uid2)


def test_check_user_is_not_self(auth_service):
    assert auth_service.check_user_is_not_self(1, 2) is True
    with pytest.raises(ValueError):
        auth_service.check_user_is_not_self(5, 5)
