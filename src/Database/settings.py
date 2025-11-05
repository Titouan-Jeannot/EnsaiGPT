# src/Database/settings.py
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL n'est pas défini dans l'environnement (.env)")

# Si aucune URL de test n'est fournie, on la déduit de DATABASE_URL en remplaçant le nom de base par 'test_db'
DATABASE_URL_TEST = os.getenv("DATABASE_URL_TEST")
if not DATABASE_URL_TEST:
    parsed = urlparse(DATABASE_URL)
    if not parsed.path or parsed.path == "/":
        # par prudence, si l'URL principale n'a pas de nom de base explicite
        DATABASE_URL_TEST = DATABASE_URL.rstrip("/") + "/test_db"
    else:
        DATABASE_URL_TEST = DATABASE_URL.replace(parsed.path, "/test_db")

def get_database_url():
    """
    Retourne l'URL de connexion selon le contexte :
    - si on est en test (pytest définit PYTEST_CURRENT_TEST), renvoie DATABASE_URL_TEST
    - sinon, renvoie DATABASE_URL
    """
    if os.getenv("PYTEST_CURRENT_TEST"):
        return DATABASE_URL_TEST
    return DATABASE_URL

def dbname_from_url(url: str) -> str:
    return urlparse(url).path.lstrip("/") or ""
