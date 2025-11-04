# src/dao/db_connection.py
import os
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictConnection  # <<- clé : impose RealDictCursor par défaut
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL manquant dans .env")

# Pool global : chaque connexion est une RealDictConnection
POOL = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL,
    connect_timeout=10,
    connection_factory=RealDictConnection,  # <<- IMPORTANT
)

class DBConnection:
    """
    Fournit une connexion transactionnelle depuis le pool.
    Usage existant conservé :
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:  # <-- renvoie un RealDictCursor automatiquement
                cursor.execute("SELECT 1 AS ok;")
                row = cursor.fetchone()  # {'ok': 1}
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
    try:
        POOL.closeall()
    except Exception:
        pass
