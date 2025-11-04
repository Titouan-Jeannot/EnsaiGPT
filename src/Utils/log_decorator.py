import logging
from functools import wraps

# Configuration du système de logs (modifiable selon ton besoin)
logging.basicConfig(
    level=logging.INFO,  # Niveau minimal (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log(func):
    """
    Décorateur qui journalise automatiquement les appels de fonctions.
    Permet de tracer les exécutions et les erreurs.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Appel de {func.__name__} avec args={args} kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logging.info(f"Succès de {func.__name__}")
            return result
        except Exception as e:
            logging.error(f"Erreur dans {func.__name__} : {e}", exc_info=True)
            raise
    return wrapper
