import psycopg2
from .settings import DATABASE_URL
from .schema_sql import SCHEMA_SQL

def init_db():
    print("Connexion à PostgreSQL…")
    with psycopg2.connect(DATABASE_URL) as conn:
        conn.autocommit = False
        try:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
            conn.commit()
            print("✅ Schéma créé / mis à jour avec succès.")
        except Exception as e:
            conn.rollback()
            print("❌ Erreur lors de la création du schéma :", e)

if __name__ == "__main__":
    init_db()
