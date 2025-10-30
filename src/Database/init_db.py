import psycopg2
from ..settings import settings
from .schema_sql import SCHEMA_SQL

def init_db():
    with psycopg2.connect(settings.DATABASE_URL) as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()

if __name__ == "__main__":
    init_db()
    print("✅ Schéma créé/mis à jour.")
