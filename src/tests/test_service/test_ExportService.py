import unittest
import datetime
import importlib
import traceback
from unittest.mock import Mock

# -------------------------------------------------------------
# Import robuste de ExportService (même style que LLMService)
# -------------------------------------------------------------
ExportService = None
import_error = None
for module_name in ["Service.ExportService", "Service.ExportService"]:
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
        f"Impossible d'importer ExportService depuis Service ou Service.\nDernière erreur : {import_error}"
    )

# -------------------------------------------------------------
# Petites classes légères pour représenter les entités lues
# (pas besoin de vraies classes ORM)
# -------------------------------------------------------------
class _Message:
    def __init__(self, id_conversation: int, id_user: int, dt: datetime.datetime, text: str, is_agent: bool = False):
        self.id_conversation = id_conversation
        self.id_user = id_user
        self.datetime = dt
        self.message = text
        self.is_from_agent = is_agent

class _Conversation:
    def __init__(self, id_conversation: int, titre: str = None, created_at: datetime.datetime = None):
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


_BASE = datetime.datetime(2025, 1, 1, 10, 0, 0)
def _mk_msg(min_offset: int, conv: int, user: int, text: str, agent: bool = False) -> _Message:
    return _Message(conv, user, _BASE + datetime.timedelta(minutes=min_offset), text, agent)


class TestExportService(unittest.TestCase):
    def setUp(self):
        # Données de test
        self.conv10 = _Conversation(10, titre="Projet ENSAI", created_at=datetime.datetime(2025, 1, 1, 9, 30))
        self.users = {_u.id_user: _u for _u in (_User(1, "alice"), _User(2, "bob"))}
        # messages désordonnés pour tester le tri
        self.msgs = [
            _mk_msg(5, 10, 1, "Salut"),                          # 10:05
            _mk_msg(0, 10, 2, "Bonjour"),                        # 10:00
            _mk_msg(7, 10, 0, "Je suis l'agent", agent=True),    # 10:07
            _mk_msg(15, 10, 1, "OK pour moi"),                   # 10:15
        ]

        # ---------------- Mocks DAO/Services ----------------
        # On borne les attributs avec spec pour éviter que des noms inventés passent
        self.message_dao = Mock(
            name="MessageDAO",
            spec=[
                "get_messages_by_conversation",
                "get_messages_by_conversation_and_user",
            ],
        )
        self.conversation_dao = Mock(name="ConversationDAO", spec=["read"])
        self.user_dao = Mock(name="UserDAO", spec=["get_user_by_id"])
        self.collaboration_dao = Mock(name="CollaborationDAO", spec=["get_by_user_id"])
        self.collaboration_service = Mock(
            name="CollaborationService",
            spec=["is_admin", "is_writer", "is_viewer"],
        )

        # Comportements par défaut
        self.message_dao.get_messages_by_conversation.return_value = list(self.msgs)
        self.message_dao.get_messages_by_conversation_and_user.side_effect = (
            lambda conv_id, uid: [m for m in self.msgs if m.id_conversation == conv_id and m.id_user == uid]
        )
        self.conversation_dao.read.return_value = self.conv10
        self.user_dao.get_user_by_id.side_effect = lambda uid: self.users.get(uid)

        # Par défaut, pas d'accès via le service (on configurera test par test)
        self.collaboration_service.is_admin.return_value = False
        self.collaboration_service.is_writer.return_value = False
        self.collaboration_service.is_viewer.return_value = False

        # Instance du service sous test
        self.svc = ExportService(
            message_dao=self.message_dao,
            conversation_dao=self.conversation_dao,
            user_dao=self.user_dao,
            collaboration_dao=self.collaboration_dao,
            collaboration_service=self.collaboration_service,
            default_format="markdown",
            include_usernames=True,
            time_format="%Y-%m-%d %H:%M",
        )

    # --- Accès via CollaborationService ---
    def test_export_markdown_with_usernames_and_access_via_collab_service(self):
        # Accorder l'accès à user 1 sur conv 10 via le service
        self.collaboration_service.is_viewer.side_effect = lambda uid, cid: (uid, cid) == (1, 10)
        self.collaboration_service.is_writer.side_effect = lambda uid, cid: (uid, cid) == (1, 10)
        self.collaboration_service.is_admin.side_effect = lambda uid, cid: False

        out = self.svc.export_conversation(10, 1, fmt="markdown")
        # Titre / ID
        self.assertIn("# Projet ENSAI", out)
        self.assertIn("**ID**: 10", out)
        # Tri chronologique
        idx_1000 = out.find("[2025-01-01 10:00]")
        idx_1005 = out.find("[2025-01-01 10:05]")
        idx_1007 = out.find("[2025-01-01 10:07]")
        idx_1015 = out.find("[2025-01-01 10:15]")
        self.assertTrue(0 <= idx_1000 < idx_1005 < idx_1007 < idx_1015)
        # Usernames + Agent
        self.assertIn("alice (user)", out)
        self.assertIn("bob (user)", out)
        self.assertIn("Agent (agent)", out)
        # Contenu
        self.assertIn("Bonjour", out)
        self.assertIn("Salut", out)
        self.assertIn("Je suis l'agent", out)
        self.assertIn("OK pour moi", out)

    # --- Accès via CollaborationDAO (pas de service) ---
    def test_export_access_via_collab_dao(self):
        # Pas de service → None
        self.svc.collaboration_service = None
        # CollaborationDAO renvoie que user 2 est collab de conv 10
        self.collaboration_dao.get_by_user_id.return_value = [_Collab(10, 2, "viewer")]

        out = self.svc.export_conversation(10, 2)
        self.assertIn("bob (user)", out)

    # --- Fallback : accès si l'utilisateur a au moins un message dans la conv ---
    def test_export_access_via_fallback_user_has_message(self):
        # Ni service, ni collab DAO
        self.svc.collaboration_service = None
        self.svc.collaboration_dao = None
        # L'utilisateur 1 a des messages dans conv 10 (déjà vrai via side_effect par défaut)
        out = self.svc.export_conversation(10, 1)
        self.assertIn("alice (user)", out)

    # --- Accès refusé ---
    def test_export_access_denied(self):
        # Aucun accès via service ni collab DAO, et user 999 n'a aucun message
        self.collaboration_service.is_viewer.return_value = False
        self.collaboration_service.is_writer.return_value = False
        self.collaboration_service.is_admin.return_value = False
        self.collaboration_dao.get_by_user_id.return_value = []
        # get_messages_by_conversation_and_user renverra vide pour 999 (via side_effect)
        with self.assertRaises(PermissionError):
            self.svc.export_conversation(10, 999)

    # --- Format texte simple ---
    def test_export_plain_format(self):
        # Donner accès à user 1 via service
        self.collaboration_service.is_viewer.side_effect = lambda uid, cid: (uid, cid) == (1, 10)
        out = self.svc.export_conversation(10, 1, fmt="plain")
        self.assertTrue(out.startswith("Projet ENSAI"))
        self.assertIn("ID: 10", out)
        self.assertIn("[2025-01-01 10:00]", out)
        self.assertIn("Agent (agent)", out)

    # --- user_dao absent => pas de username, fallback user_{id} ---
    def test_export_without_userdao(self):
        self.collaboration_service.is_viewer.side_effect = lambda uid, cid: (uid, cid) == (1, 10)
        self.svc.user_dao = None  # pas de username
        out = self.svc.export_conversation(10, 1)
        self.assertIn("user_1 (user)", out)
        self.assertIn("user_2 (user)", out)

    # --- IDs invalides ---
    def test_invalid_ids(self):
        self.collaboration_service.is_viewer.side_effect = lambda uid, cid: (uid, cid) == (1, 10)
        with self.assertRaises(ValueError):
            self.svc.export_conversation(-1, 1)
        with self.assertRaises(ValueError):
            self.svc.export_conversation(10, -2)

    # --- DAO messages incomplet -> RuntimeError ---
    def test_missing_message_list_method(self):
        self.collaboration_service.is_viewer.side_effect = lambda uid, cid: (uid, cid) == (1, 10)
        class IncompleteMsgDAO:
            # pas de get_messages_by_conversation / get_by_conversation
            pass
        self.svc.message_dao = IncompleteMsgDAO()  # override
        with self.assertRaises(RuntimeError):
            self.svc.export_conversation(10, 1)

    # --- time_format personnalisé ---
    def test_custom_time_format(self):
        self.collaboration_service.is_viewer.side_effect = lambda uid, cid: (uid, cid) == (1, 10)
        self.svc.time_format = "%d/%m/%Y %Hh%M"
        out = self.svc.export_conversation(10, 1)
        self.assertIn("01/01/2025 10h00", out)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
