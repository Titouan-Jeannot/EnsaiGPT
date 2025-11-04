import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL n'est pas défini dans le fichier .env")

print(f"✅ DATABASE_URL chargé : {DATABASE_URL}")
