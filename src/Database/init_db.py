# src/Database/init_db.py

from DAO.DBConnector import DBConnection
from schema_sql import SCHEMA_SQL


def init_db():
    """
    Initialise le schéma PostgreSQL en utilisant DBConnection
    (qui lit les credentials dans .env).
    """
    print("Connexion à PostgreSQL pour initialiser le schéma…")
    try:
        with DBConnection().connection as conn:
            conn.autocommit = False
            try:
                with conn.cursor() as cur:
                    cur.execute(SCHEMA_SQL)
                conn.commit()
                print("✅ Schéma créé / mis à jour avec succès.")
            except Exception as e:
                conn.rollback()
                print("❌ Erreur lors de la création du schéma :", e)
    except Exception as e:
        print("❌ Impossible d'établir la connexion à la base :", e)


if __name__ == "__main__":
    # rétro-compat : permet encore `python -m src.Database.init_db`
    init_db()

