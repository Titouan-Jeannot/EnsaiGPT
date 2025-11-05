# src/Database/manage_test_db.py
import psycopg2
from psycopg2 import sql
from .settings import DATABASE_URL, DATABASE_URL_TEST, dbname_from_url
from .init_db import init_db_for_url

def ensure_test_db_exists():
    """Crée la DB de test si elle n'existe pas encore (hors transaction)."""
    test_db = dbname_from_url(DATABASE_URL_TEST) or "test_db"
    admin_conn = psycopg2.connect(DATABASE_URL)
    try:
        admin_conn.autocommit = True  # IMPORTANT: avant tout cursor/execute
        cur = admin_conn.cursor()
        try:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (test_db,))
            if cur.fetchone():
                print(f"✅ La base '{test_db}' existe déjà.")
            else:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(test_db)))
                print(f"✅ Base '{test_db}' créée.")
        finally:
            cur.close()
    finally:
        admin_conn.close()

def init_test_db():
    """Applique le schéma sur la DB de test."""
    init_db_for_url(DATABASE_URL_TEST)

def drop_test_db():
    """Supprime la DB de test (en terminant d’abord les connexions), hors transaction."""
    test_db = dbname_from_url(DATABASE_URL_TEST) or "test_db"
    admin_conn = psycopg2.connect(DATABASE_URL)
    try:
        admin_conn.autocommit = True  # IMPORTANT
        cur = admin_conn.cursor()
        try:
            # termine les connexions actives sur la DB test
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s;",
                (test_db,),
            )
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(test_db)))
            print(f"🗑️ Base '{test_db}' supprimée.")
        finally:
            cur.close()
    finally:
        admin_conn.close()

if __name__ == "__main__":
    ensure_test_db_exists()
    init_test_db()
