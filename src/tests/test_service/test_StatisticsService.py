import unittest
import datetime
from typing import List, Optional

# -------------------------------------------------------------
# Import explicite du StatisticsService avec affichage des erreurs
# -------------------------------------------------------------
import importlib
import traceback

StatisticsService = None
import_error = None

for module_name in [
    "Service.StatisticsService",
    "src.Service.StatisticsService",
]:
    try:
        mod = importlib.import_module(module_name)
        StatisticsService = getattr(mod, "StatisticsService", None)
        if StatisticsService:
            print(f"[INFO] Import réussi : {module_name}")
            break
    except Exception as e:
        import_error = e
        print(f"[ERREUR] Impossible d'importer {module_name} : {e}")
        traceback.print_exc()

if StatisticsService is None:
    raise ImportError(
        f"Impossible d'importer StatisticsService "
        f"depuis Service ou src.Service.\nDernière erreur : {import_error}"
    )


if StatisticsService is None:  # pragma: no cover
    raise unittest.SkipTest(
        "Impossible d'importer StatisticsService. Ajoutez le module au PYTHONPATH ou adaptez l'import dans le test."
    )


# -------------------------------------------------------------
# Double de données minimal pour Message / Collaboration
# -------------------------------------------------------------
class _Message:
    def __init__(self, id_message, id_conversation, id_user, dt, message, is_from_agent=False):
        self.id_message = id_message
        self.id_conversation = id_conversation
        self.id_user = id_user
        self.datetime = dt
        self.message = message
        self.is_from_agent = is_from_agent


class _Collab:
    def __init__(self, id_conversation, id_user):
        self.id_conversation = id_conversation
        self.id_user = id_user


# -------------------------------------------------------------
# Doubles de DAO pour les tests
# -------------------------------------------------------------
class FakeMessageDAO:
    def __init__(self, messages: Optional[List[_Message]] = None):
        self._messages = messages or []

    def count_messages_by_user(self, user_id: int) -> int:
        return sum(1 for m in self._messages if m.id_user == user_id)

    def count_messages_by_conversation(self, conversation_id: int) -> int:
        return sum(1 for m in self._messages if m.id_conversation == conversation_id)

    def count_messages_user_in_conversation(self, user_id: int, conversation_id: int) -> int:
        return sum(1 for m in self._messages if m.id_user == user_id and m.id_conversation == conversation_id)

    def get_messages_by_user(self, user_id: int) -> List[_Message]:
        return [m for m in self._messages if m.id_user == user_id]

    def get_messages_by_conversation(self, conversation_id: int) -> List[_Message]:
        return [m for m in self._messages if m.id_conversation == conversation_id]

    def get_messages_by_conversation_and_user(self, conversation_id: int, user_id: int) -> List[_Message]:
        return [m for m in self._messages if m.id_conversation == conversation_id and m.id_user == user_id]

    def get_all_messages_minimal(self) -> List[_Message]:
        return list(self._messages)

    def get_average_message_length(self) -> float:
        if not self._messages:
            return 0.0
        total = sum(len(m.message) for m in self._messages)
        return total / len(self._messages)


class FakeCollaborationDAO:
    def __init__(self, collaborations: Optional[List[_Collab]] = None):
        self._collabs = collaborations or []

    def get_by_user_id(self, user_id: int) -> List[_Collab]:
        return [c for c in self._collabs if c.id_user == user_id]

    def count_conversations_by_user(self, user_id: int) -> int:
        return len({c.id_conversation for c in self.get_by_user_id(user_id)})


# -------------------------------------------------------------
# Fabrique utilitaire pour messages datés
# -------------------------------------------------------------
_DEF_BASE = datetime.datetime(2025, 1, 1, 10, 0, 0)


def _mk(dt_offset_minutes: int, conv: int, user: int, txt: str = "hi") -> _Message:
    return _Message(
        id_message=None,
        id_conversation=conv,
        id_user=user,
        dt=_DEF_BASE + datetime.timedelta(minutes=dt_offset_minutes),
        message=txt,
    )


# -------------------------------------------------------------
# Les tests
# -------------------------------------------------------------
class TestStatisticsService(unittest.TestCase):
    def setUp(self):
        self.messages = [
            _mk(0, 10, 1, "a"),
            _mk(5, 10, 1, "bb"),
            _mk(9, 10, 1, "ccc"),
            _mk(40, 10, 1, "dddd"),
            _mk(50, 10, 1, "eeeee"),
            _mk(12, 10, 2, "z"),
            _mk(13, 10, 2, "zz"),
            _mk(60, 20, 1, "yyy"),
        ]
        self.msg_dao = FakeMessageDAO(self.messages)
        self.collab_dao = FakeCollaborationDAO([
            _Collab(10, 1),
            _Collab(20, 1),
            _Collab(10, 2),
        ])
        self.svc = StatisticsService(
            message_dao=self.msg_dao,
            collaboration_dao=self.collab_dao,
            idle_threshold=datetime.timedelta(minutes=10),
        )

    def test_nb_conv(self):
        self.assertEqual(self.svc.nb_conv(1), 2)
        self.assertEqual(self.svc.nb_conv(2), 1)

    def test_nb_messages(self):
        self.assertEqual(self.svc.nb_messages(1), 6)
        self.assertEqual(self.svc.nb_messages(2), 2)

    def test_nb_message_conv(self):
        self.assertEqual(self.svc.nb_message_conv(10), 7)
        self.assertEqual(self.svc.nb_message_conv(20), 1)

    def test_nb_messages_de_user_par_conv(self):
        self.assertEqual(self.svc.nb_messages_de_user_par_conv(1, 10), 5)
        self.assertEqual(self.svc.nb_messages_de_user_par_conv(2, 10), 2)
        self.assertEqual(self.svc.nb_messages_de_user_par_conv(1, 20), 1)

    def test_temps_passe_sessions(self):
        dt = self.svc.temps_passe(1)
        self.assertEqual(dt, datetime.timedelta(minutes=19))

    def test_temps_passe_simple_window(self):
        dt = self.svc.temps_passe(1, simple_window=True)
        self.assertEqual(dt, datetime.timedelta(minutes=60))

    def test_temps_passe_par_conv(self):
        dt10 = self.svc.temps_passe_par_conv(1, 10)
        self.assertEqual(dt10, datetime.timedelta(minutes=19))
        dt20 = self.svc.temps_passe_par_conv(1, 20)
        self.assertEqual(dt20, datetime.timedelta(minutes=0))

    def test_top_active_users(self):
        top = self.svc.top_active_users(limit=2)
        self.assertEqual(top, [(1, 6), (2, 2)])

    def test_average_message_length(self):
        avg = self.svc.average_message_length()
        self.assertAlmostEqual(avg, 21/8, places=6)

    def test_invalid_ids(self):
        with self.assertRaises(ValueError):
            self.svc.nb_conv(-1)
        with self.assertRaises(ValueError):
            self.svc.nb_message_conv(-2)
        with self.assertRaises(ValueError):
            self.svc.nb_messages_de_user_par_conv(-1, 10)
        with self.assertRaises(ValueError):
            self.svc.nb_messages_de_user_par_conv(1, -10)


if __name__ == "__main__":
    unittest.main()
