# src/tests/conftest.py
import os
import pytest
import psycopg2
from Database.settings import DATABASE_URL_TEST
from Database.manage_test_db import ensure_test_db_exists, init_test_db

@pytest.fixture(scope="session", autouse=True)
def _prepare_test_db():
    # on s'assure que la base test existe et est à jour
    ensure_test_db_exists()
    init_test_db()
    yield

@pytest.fixture(scope="function")
def db_conn():
    conn = psycopg2.connect(DATABASE_URL_TEST)
    conn.autocommit = False
    try:
        yield conn
    finally:
        conn.rollback()  # état propre après chaque test
        conn.close()

@pytest.fixture(scope="function")
def db_cursor(db_conn):
    cur = db_conn.cursor()
    try:
        yield cur
    finally:
        cur.close()
