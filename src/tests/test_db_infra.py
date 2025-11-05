from urllib.parse import urlparse
import os
import psycopg2
from DAO.DBConnector import DBConnection

def _expected_test_db_name():
    url = os.getenv("DATABASE_URL_TEST") or os.getenv("DATABASE_URL")
    if os.getenv("DATABASE_URL_TEST"):
        return urlparse(os.getenv("DATABASE_URL_TEST")).path.lstrip("/") or "test_db"
    # si pas de DATABASE_URL_TEST, on s'attend à "test_db" (dérivé)
    return "test_db"

def test_switch_to_test_db_under_pytest():
    # doit pointer sur la DB de test
    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database() AS db;")
            row = cur.fetchone()
            assert row["db"] == _expected_test_db_name()

def test_realdictcursor_and_select_works():
    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok;")
            row = cur.fetchone()
            assert isinstance(row, dict)
            assert row["ok"] == 1

def test_rollback_on_exception():
    """
    On insère dans mots_bannis, puis on force une exception pour déclencher un rollback
    (grâce au context manager de DBConnection). À la fin, la ligne ne doit pas exister.
    """
    test_word = "pytest_rollback_marker"

    # 1) tentative d'insert + exception => rollback
    try:
        with DBConnection().connection as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO mots_bannis(mot) VALUES (%s);", (test_word,))
                # on force une exception pour déclencher rollback dans __exit__
                raise RuntimeError("boom -> rollback")
    except RuntimeError:
        pass

    # 2) vérifier qu'il n'y a PAS de ligne (car rollback)
    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM mots_bannis WHERE mot=%s;", (test_word,))
            assert cur.fetchone()["n"] == 0
