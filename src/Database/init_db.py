# src/Database/init_db.py
import psycopg2
from .schema_sql import SCHEMA_SQL

def init_db_for_url(db_url: str):
    print(f"Connexion à PostgreSQL pour initialiser le schéma…")
    with psycopg2.connect(db_url) as conn:
        conn.autocommit = False
        try:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
            conn.commit()
            print("✅ Schéma créé / mis à jour avec succès.")
        except Exception as e:
            conn.rollback()
            print("❌ Erreur lors de la création du schéma :", e)

# rétro-compat : permet encore `python -m Database.init_db` pour la base principale
if __name__ == "__main__":
    from .settings import DATABASE_URL
    init_db_for_url(DATABASE_URL)

