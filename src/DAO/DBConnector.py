# src/dao/db_connection.py
import os
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Charge .env (DATABASE_URL=postgresql://...neon.tech/...?... )
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL manquant. Ajoute-le dans .env (ex: DATABASE_URL=postgresql://...neon.tech/...)?sslmode=require"
    )

# Pool global partagé par toute l'appli
# cursor_factory=RealDictCursor => cursor.fetchall() renvoie des dicts {col: val}
POOL = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL,
    connect_timeout=10,
    cursor_factory=RealDictCursor,
)


class DBConnection:
    """
    Fournit une connexion transactionnelle depuis le pool.
    Usage :
        with DBConnection().connection as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT ...")
    """
    @property
    @contextmanager
    def connection(self):
        conn = POOL.getconn()
        try:
            conn.autocommit = False
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            POOL.putconn(conn)


def close_pool():
    """À appeler éventuellement à l'arrêt de l'appli (optionnel)."""
    try:
        POOL.closeall()
    except Exception:
        pass
