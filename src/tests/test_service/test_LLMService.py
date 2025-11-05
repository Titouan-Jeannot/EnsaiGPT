import unittest
import importlib
import traceback
from unittest.mock import Mock
import datetime
from typing import List

# -----------------------------
# Import robuste de LLMService
# -----------------------------
LLMService = None
import_error = None
for module_name in ["Service.LLMService", "src.Service.LLMService"]:
    try:
        mod = importlib.import_module(module_name)
        LLMService = getattr(mod, "LLMService", None)
        if LLMService:
            print(f"[INFO] Import réussi : {module_name}")
            break
    except Exception as e:
        import_error = e
        print(f"[ERREUR] Impossible d'importer {module_name} : {e}")
        traceback.print_exc()

if LLMService is None:  # pragma: no cover
    raise ImportError(
        f"Impossible d'importer LLMService depuis Service ou src.Service.\nDernière erreur : {import_error}"
    )

# On tente d’importer la vraie classe Message pour la persistance
Message = None
for name in ["ObjetMetier.Message", "src.ObjetMetier.Message"]:
    try:
        Message = importlib.import_module(name).Message
        break
    except Exception:
        continue
if Message is None:
    raise ImportError("La classe ObjetMetier.Message est requise par LLMService (constructeur).")

_BASE = datetime.datetime(2025, 1, 1, 10, 0, 0)


class _HistMsg:
    """Petit conteneur pour simuler des messages d'historique."""
    def __init__(self, dt_min_offset: int, text: str, user_id: int, is_agent: bool = False):
        self.datetime = _BASE + datetime.timedelta(minutes=dt_min_offset)
        self.message = text
        self.is_from_agent = is_agent
        self.id_user = user_id


class TestLLMService(unittest.TestCase):
    def setUp(self):
        # --- Mocks des dépendances ---
        self.message_dao = Mock(name="MessageDAO")
        self.provider = Mock(name="Provider")  # provider.chat(...)
        self.conversation_dao = Mock(name="ConversationDAO")
        self.user_dao = Mock(name="UserDAO")
        self.banned_service = Mock(name="BannedService")

        # Historique de conversation: 3 messages (user, agent, user)
        self.history: List[_HistMsg] = [
            _HistMsg(0,  "Bonjour", user_id=1, is_agent=False),
            _HistMsg(2,  "Bonjour, comment puis-je aider ?", user_id=0, is_agent=True),
            _HistMsg(5,  "J'ai besoin d'un résumé.", user_id=1, is_agent=False),
        ]
        self.message_dao.get_messages_by_conversation.return_value = [
            self.history[2], self.history[0], self.history[1]
        ]

        # Méthode create simulée
        def _create(msg_obj):
            msg_obj.id_message = 123
            return msg_obj
        self.message_dao.create.side_effect = _create

        # Réponse LLM simulée
        self.provider.chat.return_value = {
            "content": "Voici la réponse de l’agent.",
            "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
        }

        # Par défaut, aucun contenu interdit
        self.banned_service.contains_banned.return_value = False

        self.svc = LLMService(
            message_dao=self.message_dao,
            provider=self.provider,
            conversation_dao=self.conversation_dao,
            user_dao=self.user_dao,
            banned_service=self.banned_service,
            default_system_prompt="You are a helpful assistant.",
            max_history_messages=10,
            default_temperature=0.7,
            default_max_tokens=256,
            model="test-model",
        )

    # ---------------- simple_complete ----------------
    def test_simple_complete_ok(self):
        out = self.svc.simple_complete("Dis bonjour en une phrase.")
        self.assertEqual(out, "Voici la réponse de l’agent.")
        args, kwargs = self.provider.chat.call_args
        messages = args[0]
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[-1]["role"], "user")
        self.assertIn("Dis bonjour", messages[-1]["content"])

    def test_simple_complete_banned_input_raises(self):
        self.banned_service.contains_banned.return_value = True
        with self.assertRaises(ValueError):
            self.svc.simple_complete("Contenu interdit !!!")

    def test_simple_complete_banned_output_raises(self):
        self.banned_service.contains_banned.side_effect = [False, True]
        with self.assertRaises(ValueError):
            self.svc.simple_complete("Texte OK côté entrée.")

    # ---------------- generate_agent_reply ----------------
    def test_generate_agent_reply_persists_agent_message(self):
        result = self.svc.generate_agent_reply(conversation_id=10, user_id=1)
        self.assertIsInstance(result, Message)
        self.assertEqual(result.id_message, 123)
        self.assertTrue(result.is_from_agent)
        self.assertEqual(result.id_conversation, 10)
        self.provider.chat.assert_called()
        self.message_dao.create.assert_called_once()
        created_obj = self.message_dao.create.call_args[0][0]
        self.assertTrue(created_obj.is_from_agent)
        self.assertEqual(created_obj.id_user, 0)

    def test_generate_agent_reply_uses_last_n(self):
        self.svc.max_history_messages = 2
        _ = self.svc.generate_agent_reply(conversation_id=10, user_id=1)
        messages = self.provider.chat.call_args[0][0]
        roles = [m["role"] for m in messages]
        self.assertEqual(roles.count("assistant"), 1)
        self.assertEqual(roles.count("user"), 1)
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[2]["role"], "user")

    def test_generate_agent_reply_banned_in_history_or_output(self):
        # 3 inputs user/system + 1 output
        self.banned_service.contains_banned.side_effect = [False, False, False, True]
        with self.assertRaises(ValueError):
            self.svc.generate_agent_reply(conversation_id=10, user_id=1)

    def test_generate_agent_reply_missing_create_raises(self):
        # Supprime toutes les méthodes de création
        self.message_dao.create = None
        self.message_dao.insert = None
        self.message_dao.add = None
        with self.assertRaises(RuntimeError):
            self.svc.generate_agent_reply(conversation_id=10, user_id=1)

    def test_generate_agent_reply_invalid_ids(self):
        with self.assertRaises(ValueError):
            self.svc.generate_agent_reply(conversation_id=-1, user_id=1)
        with self.assertRaises(ValueError):
            self.svc.generate_agent_reply(conversation_id=10, user_id=-2)

    # ---------------- summarize_conversation ----------------
    def test_summarize_conversation_ok(self):
        self.provider.chat.return_value = {"content": "• Point 1\\n• Point 2", "usage": {}}
        out = self.svc.summarize_conversation(conversation_id=10, bullet_points=True)
        self.assertIn("Point 1", out)
        args, kwargs = self.provider.chat.call_args
        messages = args[0]
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("Résume la conversation", messages[1]["content"])

    def test_summarize_conversation_missing_list_method_raises(self):
        self.message_dao.get_messages_by_conversation = None
        self.message_dao.get_by_conversation = None
        with self.assertRaises(RuntimeError):
            self.svc.summarize_conversation(conversation_id=10)

    # ---------------- count_tokens ----------------
    def test_count_tokens_provider(self):
        self.provider.count_tokens = Mock(return_value=123)
        self.assertEqual(self.svc.count_tokens("abc"), 123)

    def test_count_tokens_fallback(self):
        if hasattr(self.provider, "count_tokens"):
            delattr(self.provider, "count_tokens")
        self.assertEqual(self.svc.count_tokens("12345678"), 2)

    # ---------------- provider/chat errors ----------------
    def test_provider_without_chat_raises(self):
        delattr(self.provider, "chat")
        with self.assertRaises(RuntimeError):
            self.svc.simple_complete("Hello")

    def test_provider_invalid_response_raises(self):
        self.provider.chat.return_value = {"no_content": "oops"}
        with self.assertRaises(RuntimeError):
            self.svc.simple_complete("Hello")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


# pour tester, utiliser:
# pytest -q --confcutdir=src/tests/test_Service src/tests/test_Service/test_LLMService.py

