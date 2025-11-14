# src/tests/test_Database/test_db_unit.py
import importlib
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse
import pytest


# ======================================================
# Helpers
# ======================================================

def _reload_settings_with(monkeypatch, **env):
    """
    Recharge Database.settings avec un environnement contrôlé.
    Attention : settings.py fait load_dotenv() à l'import,
    donc certains tests patchent load_dotenv en no-op.
    """
    for k in ["DATABASE_URL", "DATABASE_URL_TEST", "PYTEST_CURRENT_TEST"]:
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        if v is None:
            monkeypatch.delenv(k, raising=False)
        else:
            monkeypatch.setenv(k, v)
    import Database.settings as settings
    importlib.reload(settings)
    return settings


# ======================================================
# Tests SETTINGS (unitaires)
# ======================================================

def test_settings_derives_test_url_when_missing(monkeypatch):
    """
    Si DATABASE_URL_TEST est absente, elle est dérivée de DATABASE_URL,
    en remplaçant le path par /test_db (peut avoir des query params).
    """
    prod = "postgres://u:p@h:5432/prod_db"
    s = _reload_settings_with(monkeypatch, DATABASE_URL=prod, DATABASE_URL_TEST=None)

    assert s.DATABASE_URL == prod
    parsed = urlparse(s.DATABASE_URL_TEST)
    # On vérifie le path (indépendant des query params de Neon)
    assert parsed.path.lstrip("/") == "test_db"


def test_settings_get_database_url_switches_with_pytest(monkeypatch):
    prod = "postgres://u:p@h:5432/prod_db"
    test = "postgres://u:p@h:5432/my_test_db"

    s = _reload_settings_with(
        monkeypatch,
        DATABASE_URL=prod,
        DATABASE_URL_TEST=test,
        PYTEST_CURRENT_TEST="1",
    )
    assert s.get_database_url() == test

    s = _reload_settings_with(
        monkeypatch,
        DATABASE_URL=prod,
        DATABASE_URL_TEST=test,
        PYTEST_CURRENT_TEST=None,
    )
    assert s.get_database_url() == prod


def test_settings_raises_if_database_url_missing(monkeypatch):
    """
    Vérifie qu'une ValueError est levée si DATABASE_URL est manquante.
    On patch load_dotenv pour éviter toute réinjection depuis .env et
    on force DATABASE_URL à "" (falsy) pour un comportement déterministe.
    """
    import importlib
    import Database.settings as settings
    from unittest.mock import patch

    # Empêche load_dotenv de toucher l'env pendant le reload
    with patch.object(settings, "load_dotenv", lambda *a, **k: None):
        # Force DATABASE_URL à chaîne vide (falsy) et retire DATABASE_URL_TEST
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.delenv("DATABASE_URL_TEST", raising=False)

        # Le reload doit lever l'erreur à l'import
        with pytest.raises(ValueError):
            importlib.reload(settings)


# ======================================================
# Tests INIT DB (unitaires via mocks)
# ======================================================

def test_init_db_executes_schema_then_commit(monkeypatch):
    import Database.init_db as initdb

    fake_cur = MagicMock()
    fake_conn_ctx = MagicMock()
    fake_conn_ctx.__enter__.return_value = fake_conn_ctx
    fake_conn_ctx.__exit__.return_value = False
    fake_conn_ctx.cursor.return_value.__enter__.return_value = fake_cur

    with patch("Database.init_db.psycopg2.connect", return_value=fake_conn_ctx):
        initdb.init_db_for_url("postgres://dsn")

    fake_cur.execute.assert_called_once()        # SCHEMA_SQL exécuté
    fake_conn_ctx.commit.assert_called_once()    # commit ok
    fake_conn_ctx.rollback.assert_not_called()


def test_init_db_rolls_back_on_error(monkeypatch):
    import Database.init_db as initdb

    fake_cur = MagicMock()
    fake_cur.execute.side_effect = RuntimeError("sql error")

    fake_conn_ctx = MagicMock()
    fake_conn_ctx.__enter__.return_value = fake_conn_ctx
    fake_conn_ctx.__exit__.return_value = False
    fake_conn_ctx.cursor.return_value.__enter__.return_value = fake_cur

    with patch("Database.init_db.psycopg2.connect", return_value=fake_conn_ctx):
        initdb.init_db_for_url("postgres://dsn")

    fake_conn_ctx.rollback.assert_called_once()
    fake_conn_ctx.commit.assert_not_called()


# ======================================================
# Tests MANAGE TEST DB (unitaires via mocks)
# ======================================================

def test_manage_test_db_ensure_exists_branches(monkeypatch):
    import Database.manage_test_db as mdb

    with patch.object(mdb, "DATABASE_URL", "postgres://u:p@h:5432/postgres"), \
         patch.object(mdb, "DATABASE_URL_TEST", "postgres://u:p@h:5432/test_db"), \
         patch.object(mdb, "dbname_from_url", return_value="test_db"):

        fake_cur = MagicMock()
        fake_conn = MagicMock()
        fake_conn.cursor.return_value = fake_cur

        # 1) DB existe déjà
        fake_cur.fetchone.return_value = (1,)
        with patch.object(mdb, "psycopg2") as mock_pg:
            mock_pg.connect.return_value = fake_conn
            mdb.ensure_test_db_exists()
            fake_cur.execute.assert_any_call(
                "SELECT 1 FROM pg_database WHERE datname = %s;", ("test_db",)
            )

        # 2) DB n'existe pas -> CREATE DATABASE ...
        fake_cur.reset_mock()
        fake_conn.reset_mock()
        fake_cur.fetchone.return_value = None
        with patch.object(mdb, "psycopg2") as mock_pg:
            mock_pg.connect.return_value = fake_conn
            mdb.ensure_test_db_exists()
            executed_sqls = " ".join(str(args[0]) for args, _ in fake_cur.execute.call_args_list)
            assert "CREATE DATABASE" in executed_sqls


def test_manage_test_db_drop_terminates_then_drop(monkeypatch):
    import Database.manage_test_db as mdb

    with patch.object(mdb, "DATABASE_URL", "postgres://u:p@h:5432/postgres"), \
         patch.object(mdb, "DATABASE_URL_TEST", "postgres://u:p@h:5432/test_db"), \
         patch.object(mdb, "dbname_from_url", return_value="test_db"):

        fake_cur = MagicMock()
        fake_conn = MagicMock()
        fake_conn.cursor.return_value = fake_cur

        with patch.object(mdb, "psycopg2") as mock_pg:
            mock_pg.connect.return_value = fake_conn
            mdb.drop_test_db()

        # 1) terminate backends
        fake_cur.execute.assert_any_call(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s;",
            ("test_db",),
        )
        # 2) drop database
        executed_sqls = " ".join(str(args[0]) for args, _ in fake_cur.execute.call_args_list)
        assert "DROP DATABASE" in executed_sqls


def test_manage_test_db_init_calls_initdb(monkeypatch):
    import Database.manage_test_db as mdb
    with patch.object(mdb, "init_db_for_url") as mock_init, \
         patch.object(mdb, "DATABASE_URL_TEST", "postgres://u:p@h:5432/test_db"):
        mdb.init_test_db()
        mock_init.assert_called_once_with("postgres://u:p@h:5432/test_db")
