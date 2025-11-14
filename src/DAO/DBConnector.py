# src/DAO/DBConnector.py

import os
import psycopg2
from psycopg2.extensions import connection as _connection
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()


class DBConnection:
    """
    Gestion centralisée des connexions PostgreSQL via fichier .env
    """

    def __init__(self):
        self.host = os.getenv("PG_HOST")
        self.database = os.getenv("PG_DATABASE")
        self.user = os.getenv("PG_USER")
        self.password = os.getenv("PG_PASSWORD")
        self.port = int(os.getenv("PG_PORT", "5432"))

        # Vérification rapide :
        if not all([self.host, self.database, self.user, self.password]):
            raise RuntimeError("❌ Variables d'environnement PostgreSQL manquantes dans .env")

    @property
    def connection(self) -> _connection:
        return psycopg2.connect(
            host=self.host,
            dbname=self.database,
            user=self.user,
            password=self.password,
            port=self.port,
        )
