import unittest
import datetime
import importlib
import traceback
from typing import List, Optional

# -------------------------------------------------------------
# Import explicite de ExportService avec logs d'erreurs
# -------------------------------------------------------------
ExportService = None
import_error = None
for module_name in [
    "Service.ExportService",
    "src.Service.ExportService",
]:
    try:
        mod = importlib.import_module(module_name)
        ExportService = getattr(mod, "ExportService", None)
        if ExportService:
            print(f"[INFO] Import réussi : {module_name}")
            break
    except Exception as e:
        import_error = e
        print(f"[ERREUR] Impossible d'importer {module_name} : {e}")
        traceback.print_exc()

if ExportService is None:  # pragma: no cover
    raise ImportError(
        f"Impossible d'importer ExportService depuis Service ou src.Service.\nDernière erreur : {import_error}"
    )


# -------------------------------------------------------------
# Doubles d'entités minimaux
# -------------------------------------------------------------
class _Message:
    def __init__(self, id_conversation: int, id_user: int, dt: datetime.datetime, text: str, is_agent: bool = False):
        self.id_conversation = id_conversation
        self.id_user = id_user
        self.datetime = dt
        self.message = text
        self.is_from_agent = is_agent

class _Conversation:
    def __init__(self, id_conversation: int, titre: str = None, created_at: Optional[datetime.datetime] = None):
        self.id_conversation = id_conversation
        self.titre = titre
        self.created_at = created_at or datetime.datetime(2025, 1, 1, 9, 0)

class _User:
    def __init__(self, id_user: int, username: str):
        self.id_user = id_user
        self.username = username

class _Collab:
    def __init__(self, id_conversation: int, id_user: int, role: str = "viewer"):
        self.id_conversation = id_conversation
        self.id_user = id_user
        self.role = role


# -------------------------------------------------------------
# Doubles de DAO / Services
# -------------------------------------------------------------
class FakeMessageDAO:
    def __init__(self, messages: List[_Message]):
        self._messages = messages

    def get_messages_by_conversation(self, conversation_id: int) -> List[_Message]:
        return [m for m in self._messages if m.id_conversation == conversation_id]

    def get_messages_by_conversation_and_user(self, conversation_id: int, user_id: int) -> List[_Message]:
        return [m for m in self._messages if m.id_conversation == conversation_id and m.id_user == user_id]

class FakeConversationDAO:
    def __init__(self, conversations: List[_Conversation]):
        self._map = {c.id_conversation: c for c in conversations}

    def read(self, conversation_id: int) -> Optional[_Conversation]:
        return self._map.get(conversation_id)

class FakeUserDAO:
    def __init__(self, users: List[_User]):
        self._map = {u.id_user: u for u in users}

    def get_user_by_id(self, user_id: int) -> Optional[_User]:
        return self._map.get(user_id)

class FakeCollaborationDAO:
    def __init__(self, collabs: List[_Collab]):
        self._collabs = collabs

    def get_by_user_id(self, user_id: int) -> List[_Collab]:
        return [c for c in self._collabs if c.id_user == user_id]

class FakeCollaborationService:
    def __init__(self, allowed_pairs=None):
        # allowed_pairs: set of (user_id, conversation_id)
        self.allowed = set(allowed_pairs or [])

    def is_admin(self, user_id: int, conversation_id: int) -> bool:
        return (user_id, conversation_id) in self.allowed

    def is_writer(self, user_id: int, conversation_id: int) -> bool:
        return (user_id, conversation_id) in self.allowed

    def is_viewer(self, user_id: int, conversation_id: int) -> bool:
        return (user_id, conversation_id) in self.allowed


# -------------------------------------------------------------
# Outils
# -------------------------------------------------------------
_BASE = datetime.datetime(2025, 1, 1, 10, 0, 0)

def _mk_msg(min_offset: int, conv: int, user: int, text: str, agent=False) -> _Message:
    return _Message(conv, user, _BASE + datetime.timedelta(minutes=min_offset), text, agent)


# -------------------------------------------------------------
# Tests
# -------------------------------------------------------------
class TestExportService(unittest.TestCase):
    def setUp(self):
        # Conversation 10 avec 4 messages (dont 1 agent) et utilisateur 1 & 2
        self.conv10 = _Conversation(10, titre="Projet ENSAI", created_at=datetime.datetime(2025, 1, 1, 9, 30))
        self.users = [_User(1, "alice"), _User(2, "bob")]
        self.msgs = [
            _mk_msg(5, 10, 1, "Salut"),            # 10:05
            _mk_msg(0, 10, 2, "Bonjour"),          # 10:00 (désordonné pour tester le tri)
            _mk_msg(7, 10, 0, "Je suis l'agent", agent=True),  # 10:07
            _mk_msg(15, 10, 1, "OK pour moi"),     # 10:15
        ]

        self.msg_dao = FakeMessageDAO(self.msgs)
        self.conv_dao = FakeConversationDAO([self.conv10])
        self.user_dao = FakeUserDAO(self.users)
        self.collab_dao = FakeCollaborationDAO([_Collab(10, 1, "writer"), _Collab(10, 2, "viewer")])

    def _make_service(self, *, allow_pairs=None, include_usernames=True, fmt="markdown"):
        collab_service = FakeCollaborationService(allow_pairs or set())
        return ExportService(
            message_dao=self.msg_dao,
            conversation_dao=self.conv_dao,
            user_dao=self.user_dao,
            collaboration_dao=self.collab_dao,
            collaboration_service=collab_service,
            default_format=fmt,
            include_usernames=include_usernames,
            time_format="%Y-%m-%d %H:%M",
        )

    # --- Accès via CollaborationService ---
    def test_export_markdown_with_usernames_and_access_via_collab_service(self):
        svc = self._make_service(allow_pairs={(1, 10)})
        out = svc.export_conversation(10, 1, fmt="markdown")
        # vérif contenu minimal
        self.assertIn("# Projet ENSAI", out)
        self.assertIn("**ID**: 10", out)
        # tri par datetime (10:00, 10:05, 10:07, 10:15)
        idx_1000 = out.find("[2025-01-01 10:00]")
        idx_1005 = out.find("[2025-01-01 10:05]")
        idx_1007 = out.find("[2025-01-01 10:07]")
        idx_1015 = out.find("[2025-01-01 10:15]")
        self.assertTrue(0 <= idx_1000 < idx_1005 < idx_1007 < idx_1015)
        # usernames utilisés pour users, "Agent" pour agent
        self.assertIn("alice (user)", out)
        self.assertIn("bob (user)", out)
        self.assertIn("Agent (agent)", out)
        # contenu messages
        self.assertIn("Bonjour", out)
        self.assertIn("Salut", out)
        self.assertIn("Je suis l'agent", out)
        self.assertIn("OK pour moi", out)

    # --- Accès via CollaborationDAO sans service ---
    def test_export_access_via_collab_dao(self):
        svc = ExportService(
            message_dao=self.msg_dao,
            conversation_dao=self.conv_dao,
            user_dao=self.user_dao,
            collaboration_dao=self.collab_dao,
            collaboration_service=None,
            default_format="markdown",
        )
        out = svc.export_conversation(10, 2)
        self.assertIn("bob (user)", out)

    # --- Fallback: accès si l'utilisateur a un message dans la conv ---
    def test_export_access_via_fallback_user_has_message(self):
        # Retirer droits explicites
        svc = ExportService(
            message_dao=self.msg_dao,
            conversation_dao=self.conv_dao,
            user_dao=self.user_dao,
            collaboration_dao=None,
            collaboration_service=None,
            default_format="markdown",
        )
        out = svc.export_conversation(10, 1)
        self.assertIn("alice (user)", out)

    # --- Accès refusé ---
    def test_export_access_denied(self):
        svc = self._make_service(allow_pairs=set())  # aucun droit
        with self.assertRaises(PermissionError):
            svc.export_conversation(10, 999)  # user 999 n'a pas de message non plus

    # --- Format texte simple ---
    def test_export_plain_format(self):
        svc = self._make_service(allow_pairs={(1, 10)}, fmt="plain")
        out = svc.export_conversation(10, 1, fmt="plain")
        self.assertTrue(out.startswith("Projet ENSAI"))
        self.assertIn("ID: 10", out)
        self.assertIn("[2025-01-01 10:00]", out)
        self.assertIn("Agent (agent)", out)

    # --- user_dao absent => pas de username, fallback user_{id} ---
    def test_export_without_userdao(self):
        svc = ExportService(
            message_dao=self.msg_dao,
            conversation_dao=self.conv_dao,
            user_dao=None,  # pas de usernames possibles
            collaboration_dao=self.collab_dao,
            collaboration_service=FakeCollaborationService({(1, 10)}),
            default_format="markdown",
        )
        out = svc.export_conversation(10, 1)
        self.assertIn("user_1 (user)", out)
        self.assertIn("user_2 (user)", out)

    # --- IDs invalides ---
    def test_invalid_ids(self):
        svc = self._make_service(allow_pairs={(1, 10)})
        with self.assertRaises(ValueError):
            svc.export_conversation(-1, 1)
        with self.assertRaises(ValueError):
            svc.export_conversation(10, -2)

    # --- DAO messages incomplet -> RuntimeError ---
    def test_missing_message_list_method(self):
        class IncompleteMsgDAO:
            pass
        svc = self._make_service(allow_pairs={(1, 10)})
        svc.message_dao = IncompleteMsgDAO()  # override
        with self.assertRaises(RuntimeError):
            svc.export_conversation(10, 1)

    # --- time_format personnalisé ---
    def test_custom_time_format(self):
        svc = self._make_service(allow_pairs={(1, 10)})
        svc.time_format = "%d/%m/%Y %Hh%M"
        out = svc.export_conversation(10, 1)
        self.assertIn("01/01/2025 10h00", out)


if __name__ == "__main__":
    unittest.main()
