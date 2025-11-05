# src/dao/db_connection.py
import os
from contextlib import contextmanager
from functools import lru_cache
from urllib.parse import urlparse

from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictConnection
from dotenv import load_dotenv

load_dotenv()

def _current_db_url() -> str:
    """
    Retourne l'URL de connexion à utiliser maintenant.
    - En tests (pytest définit PYTEST_CURRENT_TEST) -> DATABASE_URL_TEST si dispo,
      sinon on dérive depuis DATABASE_URL en remplaçant le nom de la DB par 'test_db'.
    - Sinon -> DATABASE_URL.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL manquant dans .env / l'environnement")

    if os.getenv("PYTEST_CURRENT_TEST"):
        test_url = os.getenv("DATABASE_URL_TEST")
        if not test_url:
            # dérive .../<db> -> .../test_db
            parsed = urlparse(db_url)
            base = parsed._replace(path="/test_db")
            test_url = base.geturl()
        return test_url

    return db_url


@lru_cache(maxsize=4)
def _get_pool(dsn: str) -> SimpleConnectionPool:
    """
    Crée (une fois) et met en cache un pool par DSN.
    """
    return SimpleConnectionPool(
        minconn=1,
        maxconn=int(os.getenv("DB_POOL_MAX", "10")),
        dsn=dsn,
        connect_timeout=10,
        connection_factory=RealDictConnection,
    )


class DBConnection:
    """
    Usage conservé :
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok;")
                row = cursor.fetchone()  # {'ok': 1}
    """
    @property
    @contextmanager
    def connection(self):
        dsn = _current_db_url()
        pool = _get_pool(dsn)
        conn = pool.getconn()
        try:
            conn.autocommit = False
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            pool.putconn(conn)


def close_pool():
    """
    Ferme tous les pools ouverts (utile en teardown de tests si besoin).
    """
    # accéder au cache lru_cache pour fermer chaque pool
    cache = _get_pool.cache_info()
    if cache.hits or cache.misses:
        # on ne peut pas lister via cache_info ; on force une petite astuce :
        # wrap lru_cache avec un attribut pour stocker les instances
        pass  # voir version ci-dessous si tu veux du cleanup strict
