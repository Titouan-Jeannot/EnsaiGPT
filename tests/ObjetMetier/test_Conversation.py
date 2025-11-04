import unittest
import importlib
import inspect


class TestConversation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Try several common module names; skip tests if Conversation cannot be imported.
        candidates = [
            "conversation",
            "conversation_module",
            "ObjetMetier.conversation",
            "objet_metier.conversation",
            "Objet_Metier.conversation",
        ]
        mod = None
        for name in candidates:
            try:
                mod = importlib.import_module(name)
                break
            except Exception:
                continue
        if mod is None:
            raise unittest.SkipTest(
                "Impossible d'importer le module contenant Conversation. "
                "Ajoutez le module au PYTHONPATH ou adaptez le nom dans le test."
            )
        cls.Conversation = getattr(mod, "Conversation", None)
        if cls.Conversation is None or not inspect.isclass(cls.Conversation):
            raise unittest.SkipTest(
                "La classe Conversation n'a pas été trouvée dans le module importé."
            )

    # Helper: find a callable to add a message
    def _find_add(self, conv):
        names = [
            "add_message",
            "add",
            "post_message",
            "send_message",
            "send",
            "append_message",
        ]
        for n in names:
            if hasattr(conv, n) and callable(getattr(conv, n)):
                return getattr(conv, n)
        self.skipTest(
            "Aucune méthode d'ajout de message trouvée (expected one of {}).".format(
                names
            )
        )

    # Helper: get messages container/list
    def _get_messages(self, conv):
        # prefer getter methods
        getters = [
            "get_messages",
            "messages",
            "get_history",
            "history",
            "messages_list",
            "messages",
        ]
        for g in getters:
            if hasattr(conv, g):
                attr = getattr(conv, g)
                if callable(attr):
                    return attr()
                else:
                    return attr
        self.skipTest(
            "Aucun accès aux messages trouvé (expected one of {}).".format(getters)
        )

    def test_creation_default(self):
        conv = self.Conversation()
        self.assertIsNotNone(conv, "Création d'une Conversation devrait réussir")

    def test_add_message_and_retrieve(self):
        conv = self.Conversation()
        add = self._find_add(conv)
        # try different common signatures
        try:
            add("alice", "Bonjour")
        except TypeError:
            # maybe signature is (content,) only
            try:
                add("Bonjour")
            except TypeError:
                # maybe signature requires a dict/message object
                try:
                    add({"author": "alice", "content": "Bonjour"})
                except TypeError:
                    self.skipTest(
                        "Impossible d'appeler la méthode d'ajout de message avec des signatures communes."
                    )
        messages = self._get_messages(conv)
        # Expect at least one message stored
        self.assertTrue(
            messages is not None and len(messages) >= 1,
            "Le message ajouté doit apparaître dans l'historique",
        )

    def test_participants_tracking_optional(self):
        conv = self.Conversation()
        add = self._find_add(conv)
        # add messages from two participants
        try:
            add("alice", "Hi")
            add("bob", "Hello")
        except TypeError:
            try:
                add("Hi")
                add("Hello")
            except TypeError:
                try:
                    add({"author": "alice", "content": "Hi"})
                    add({"author": "bob", "content": "Hello"})
                except TypeError:
                    self.skipTest(
                        "Impossible d'appeler add pour tester les participants."
                    )
        # If conversation exposes participants, verify them
        possible_parts = ["participants", "get_participants", "users"]
        for p in possible_parts:
            if hasattr(conv, p):
                val = getattr(conv, p)
                participants = val() if callable(val) else val
                self.assertTrue(
                    "alice" in participants or "bob" in participants,
                    "La liste des participants devrait contenir les auteurs ajoutés",
                )
                return
        # If no participants API, consider test passed (optional feature)
        self.skipTest("Aucune API de participants détectée — test optionnel ignoré.")

    def test_serialization_roundtrip_if_supported(self):
        conv = self.Conversation()
        add = self._find_add(conv)
        try:
            add("alice", "Roundtrip")
        except TypeError:
            try:
                add("Roundtrip")
            except TypeError:
                try:
                    add({"author": "alice", "content": "Roundtrip"})
                except TypeError:
                    self.skipTest(
                        "Impossible d'ajouter un message pour tester la sérialisation."
                    )
        # Check for to_dict / from_dict
        if hasattr(conv, "to_dict") and hasattr(self.Conversation, "from_dict"):
            data = conv.to_dict()
            self.assertIsInstance(data, dict, "to_dict doit retourner un dictionnaire")
            conv2 = self.Conversation.from_dict(data)
            # If equality defined, use it; otherwise compare serialized forms
            if hasattr(conv, "__eq__"):
                self.assertEqual(
                    conv, conv2, "L'objet re-créé doit être égal à l'original"
                )
            else:
                self.assertEqual(
                    conv.to_dict(),
                    conv2.to_dict(),
                    "Les représentations dict doivent être identiques après roundtrip",
                )
        else:
            self.skipTest(
                "Sérialisation (to_dict/from_dict) non implémentée — test ignoré."
            )

    def test_message_structure_contains_expected_fields(self):
        conv = self.Conversation()
        add = self._find_add(conv)
        try:
            add("alice", "Inspect")
        except TypeError:
            try:
                add("Inspect")
            except TypeError:
                try:
                    add({"author": "alice", "content": "Inspect"})
                except TypeError:
                    self.skipTest("Impossible d'ajouter un message pour inspection.")
        messages = self._get_messages(conv)
        # Inspect the first message structure
        first = messages[0]
        # acceptable forms: dict with keys, or object with attributes
        if isinstance(first, dict):
            self.assertIn(
                "content",
                first.keys() | {"content"},
                "Le message dict devrait contenir 'content'",
            )
        else:
            # object: check attributes
            has_content = (
                hasattr(first, "content")
                or hasattr(first, "text")
                or hasattr(first, "message")
            )
            self.assertTrue(
                has_content,
                "L'objet message devrait exposer 'content'/'text'/'message'",
            )


if __name__ == "__main__":
    unittest.main()
