# src/tests/test_Database/test_db_integration.py
import os
import pytest


def _expected_test_db_name():
    from urllib.parse import urlparse
    url = os.getenv("DATABASE_URL_TEST") or os.getenv("DATABASE_URL") or ""
    if os.getenv("DATABASE_URL_TEST"):
        return urlparse(os.getenv("DATABASE_URL_TEST")).path.lstrip("/") or "test_db"
    return "test_db"


@pytest.mark.db
@pytest.mark.integration
def test_current_database_is_test_db(monkeypatch):
    # Force le contexte pytest -> DB de test (voir DBConnector/_current_db_url)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")

    from DAO.DBConnector import DBConnection
    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database() AS db;")
            row = cur.fetchone()
            assert row["db"] == _expected_test_db_name()


@pytest.mark.db
@pytest.mark.integration
def test_select_and_dict_cursor(monkeypatch):
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")

    from DAO.DBConnector import DBConnection
    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok;")
            row = cur.fetchone()
            assert isinstance(row, dict)
            assert row["ok"] == 1


@pytest.mark.db
@pytest.mark.integration
def test_commit_and_rollback(monkeypatch):
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")

    from DAO.DBConnector import DBConnection

    # table technique idempotente
    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS mots_bannis(mot TEXT PRIMARY KEY);")

    # commit
    word_commit = "pytest_commit_marker"
    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO mots_bannis(mot) VALUES (%s) ON CONFLICT DO NOTHING;",
                (word_commit,),
            )
    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM mots_bannis WHERE mot=%s;", (word_commit,))
            assert cur.fetchone()["n"] >= 1

    # rollback
    word_rb = "pytest_rollback_marker"
    try:
        with DBConnection().connection as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO mots_bannis(mot) VALUES (%s);", (word_rb,))
                raise RuntimeError("boom -> rollback")
    except RuntimeError:
        pass

    with DBConnection().connection as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM mots_bannis WHERE mot=%s;", (word_rb,))
            # 👇 correction ici : fetchone() (et pas cur.fe)
            assert cur.fetchone()["n"] == 0
