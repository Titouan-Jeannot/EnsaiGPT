"""Configuration de tests pour isoler les accès base de données."""
from __future__ import annotations

import sys
import types


def _ensure_dbconnector_stub() -> None:
    """Injecte un module factice pour DBConnection si nécessaire."""
    module_name = "src.DAO.DBConnector"
    if module_name in sys.modules:
        return

    module = types.ModuleType(module_name)

    class DummyDBConnection:  # pragma: no cover - utilisé uniquement en tests
        def __init__(self, *args, **kwargs):  # noqa: D401 - comportement trivial
            pass

        @property
        def connection(self):  # noqa: D401 - utilisé uniquement quand non patché
            raise RuntimeError("Connexion fictive : à patcher dans les tests.")

    def close_pool():  # pragma: no cover - aucun effet en tests
        return None

    module.DBConnection = DummyDBConnection
    module.close_pool = close_pool
    sys.modules[module_name] = module


_ensure_dbconnector_stub()
