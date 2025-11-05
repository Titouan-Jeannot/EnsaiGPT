# src/tests/test_Service/conftest.py
# -> garde le PYTHONPATH utile + neutralise l'init DB du conftest parent
import os, sys
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC  = os.path.join(ROOT, "src")
for p in (ROOT, SRC):
    if p not in sys.path:
        sys.path.insert(0, p)

print("[test_Service] conftest local chargé")  # debug visible pendant la collecte

@pytest.fixture(scope="session", autouse=True)
def _prepare_test_db():
    """
    Shadow la fixture autouse du conftest parent pour éviter toute connexion DB
    dans ce sous-dossier (tests unitaires).
    """
    yield
