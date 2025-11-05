# src/tests/test_Service/conftest.py
# -> pas d'init DB, juste le PYTHONPATH utile
import os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC  = os.path.join(ROOT, "src")
for p in (ROOT, SRC):
    if p not in sys.path:
        sys.path.insert(0, p)

# Aucune fixture autouse ici (on neutralise simplement en n'en déclarant pas)
