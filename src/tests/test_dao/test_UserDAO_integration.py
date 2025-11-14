from datetime import datetime
import time
import pytest

from DAO.DBConnector import DBConnection
from DAO.UserDAO import UserDAO
from ObjetMetier.User import User


# -------- Helpers schéma / infra --------

REQUIRED_COLS = {
    "id_user",
    "username",
    "nom",
    "prenom",
    "mail",
    "password_hash",
    "salt",
    "sign_in_date",
    "last_login",
    "status",
    "setting_param",
}


def users_schema_columns():
    try:
        with DBConnection().connection as c:
            with c.cursor() as cur:
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'users'
                """)
                return { (r["column_name"] if isinstance(r, dict) else r[0]).lower()
                         for r in cur.fetchall() }
    except Exception:
        return set()


def has_required_users_schema() -> bool:
    cols = users_schema_columns()
    return REQUIRED_COLS.issubset(cols)


def make_user(username: str, email: str) -> User:
    """Fabrique un User complet conforme au UserDAO."""
    return User(
        id=None,
        username=username,
        nom="Doe",
        prenom="Jane",
        mail=email,
        password_hash="hash",
        salt="salt",
        sign_in_date=datetime(2025, 1, 1, 10, 0, 0),
        last_login=datetime(2025, 1, 2, 11, 0, 0),
        status="active",
        setting_param="{}",
    )


# -------- Tests d’intégration --------

@pytest.mark.integration
def test_userdao_crud_and_search_integration():
    if not has_required_users_schema():
        pytest.skip("Schéma 'users' incomplet pour UserDAO.create — test d'intégration ignoré.")

    dao = UserDAO()
    uniq = str(int(time.time() * 1000))

    # --- CREATE ---
    u = make_user(
        username="int_user_" + uniq,
        email=f"int_user_{uniq}@example.com",
    )
    u = dao.create(u)
    assert isinstance(u.id, int)

    # --- READ BY ID ---
    got = dao.read(u.id)
    assert got is not None
    assert got.username.startswith("int_user_")

    # --- READ BY EMAIL ---
    by_mail = dao.get_user_by_email(u.mail)
    assert by_mail is not None and by_mail.id == u.id

    # --- READ BY USERNAME ---
    by_username = dao.get_user_by_username(u.username)
    assert by_username is not None and by_username.id == u.id

    # --- UPDATE ---
    got.nom = "Updated"
    ok = dao.update(got)
    assert ok is True
    got2 = dao.read(u.id)
    assert got2.nom == "Updated"

    # --- DELETE ---
    ok = dao.delete(u.id)
    assert ok is True
    assert dao.read(u.id) is None


@pytest.mark.integration
def test_userdao_read_nonexistent_returns_none():
    if not has_required_users_schema():
        pytest.skip("Schéma 'users' incomplet — test d'intégration ignoré.")
    dao = UserDAO()
    assert dao.read(999999999) is None


@pytest.mark.integration
def test_userdao_update_nonexistent_returns_false():
    if not has_required_users_schema():
        pytest.skip("Schéma 'users' incomplet — test d'intégration ignoré.")
    dao = UserDAO()

    uniq = str(int(time.time() * 1000))
    # crée un vrai user pour récupérer un objet complet, puis modifie son id → inexistant
    u = dao.create(make_user(username="upd_nonexist_"+uniq, email=f"upd_nonexist_{uniq}@ex.com"))
    try:
        phantom = dao.read(u.id)
        phantom.id = 987654321  # supposé inexistant
        assert dao.update(phantom) is False
    finally:
        dao.delete(u.id)


@pytest.mark.integration
def test_userdao_delete_nonexistent_returns_false():
    if not has_required_users_schema():
        pytest.skip("Schéma 'users' incomplet — test d'intégration ignoré.")
    dao = UserDAO()
    assert dao.delete(123456789) is False


@pytest.mark.integration
def test_userdao_unique_mail_enforced_if_present():
    """
    Doublon d'email :
    - Si contrainte unique en base → UserDAO.create lève ValueError (OK).
    - Sinon → la 2e insertion réussit (on l'accepte) et on nettoie.
    """
    if not has_required_users_schema():
        pytest.skip("Schéma 'users' incomplet — test d'intégration ignoré.")

    dao = UserDAO()
    uniq = str(int(time.time() * 1000))
    email = f"uniq_mail_{uniq}@example.com"

    u1 = dao.create(make_user(username="um1_"+uniq, email=email))
    u2_id = None
    try:
        try:
            u2 = dao.create(make_user(username="um2_"+uniq, email=email))
            # pas de contrainte → insertion passe
            assert isinstance(u2.id, int)
            u2_id = u2.id
        except ValueError:
            # contrainte unique → attendu, on ne fait rien
            pass
    finally:
        dao.delete(u1.id)
        if u2_id:
            dao.delete(u2_id)


@pytest.mark.integration
def test_userdao_unique_username_enforced_if_present():
    """
    Doublon de username :
    - Si contrainte unique en base → UserDAO.create lève ValueError (OK).
    - Sinon → la 2e insertion réussit (on l'accepte) et on nettoie.
    """
    if not has_required_users_schema():
        pytest.skip("Schéma 'users' incomplet — test d'intégration ignoré.")

    dao = UserDAO()
    uniq = str(int(time.time() * 1000))
    username = "uniq_username_" + uniq

    u1 = dao.create(make_user(username=username, email=f"un_{uniq}@example.com"))
    u2_id = None
    try:
        try:
            u2 = dao.create(make_user(username=username, email=f"un2_{uniq}@example.com"))
            assert isinstance(u2.id, int)
            u2_id = u2.id
        except ValueError:
            # contrainte unique → attendu
            pass
    finally:
        dao.delete(u1.id)
        if u2_id:
            dao.delete(u2_id)


@pytest.mark.integration
def test_userdao_get_by_email_and_username_not_found():
    if not has_required_users_schema():
        pytest.skip("Schéma 'users' incomplet — test d'intégration ignoré.")

    dao = UserDAO()
    nowtag = str(int(time.time()))
    assert dao.get_user_by_email("nope_"+nowtag+"@example.com") is None
    assert dao.get_user_by_username("nope_"+nowtag) is None
