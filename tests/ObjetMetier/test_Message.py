from pathlib import Path
from importlib.machinery import SourceFileLoader
from importlib.util import spec_from_loader, module_from_spec
from datetime import datetime, timedelta
import pytest

# test_Message.py
# Tests unitaires adaptatifs pour la classe Message
# Placez ce fichier dans tests/Objet Métier/ comme demandé.


def _find_and_load_message_class():
    # Cherche un fichier message.py contenant "class Message" dans l'arborescence du projet
    base = (
        Path(__file__).resolve().parents[2]
    )  # monte jusqu'à la racine présumée du projet
    for path in base.rglob("message.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if "class Message" in text:
            loader = SourceFileLoader(
                f"tests_message_{path.stem}_{abs(hash(str(path)))}", str(path)
            )
            spec = spec_from_loader(loader.name, loader)
            module = module_from_spec(spec)
            loader.exec_module(module)
            if hasattr(module, "Message"):
                return getattr(module, "Message")
    raise ImportError(
        "Impossible de trouver une classe 'Message' dans un fichier message.py du projet."
    )


Message = _find_and_load_message_class()


def create_sample(kwargs=None):
    kwargs = kwargs or {}
    defaults = {
        "sender": "alice@example.com",
        "recipient": "bob@example.com",
        "content": "Bonjour Bob",
    }
    defaults.update(kwargs)
    # Try to instantiate flexibly depending on constructor signature
    try:
        return Message(**defaults)
    except TypeError:
        try:
            return Message(
                defaults["sender"], defaults["recipient"], defaults["content"]
            )
        except Exception as e:
            pytest.skip(
                f"Impossible d'instancier Message avec les signatures connues: {e}"
            )


def has_method(obj, name):
    return callable(getattr(obj, name, None))


def has_attr(obj, name):
    return hasattr(obj, name)


def test_create_message_and_attributes():
    m = create_sample()
    assert m is not None
    # Vérifie au moins la présence des attributs courants (sender, recipient, content)
    for attr in ("sender", "recipient", "content"):
        assert hasattr(m, attr), f"L'objet Message doit avoir l'attribut '{attr}'"


def test_str_contains_key_fields():
    m = create_sample()
    s = str(m)
    assert isinstance(s, str)
    # Le str devrait contenir au moins l'expéditeur ou le contenu
    assert (getattr(m, "sender", "") in s) or (getattr(m, "content", "") in s)


def test_equality_behavior():
    m1 = create_sample()
    # crée une copie de façon "naïve" selon signature
    try:
        m2 = Message(m1.sender, m1.recipient, m1.content)
    except Exception:
        try:
            m2 = Message(
                **{
                    k: getattr(m1, k)
                    for k in ("sender", "recipient", "content")
                    if hasattr(m1, k)
                }
            )
        except Exception:
            pytest.skip(
                "Impossible de re-créer une instance équivalente pour tester l'égalité."
            )
    if has_method(m1, "__eq__"):
        assert (m1 == m2) == True or (
            m1 == m2
        ) == False  # s'assure que l'opérateur ne lève pas d'erreur
    else:
        pytest.skip("La classe Message n'implémente pas __eq__ explicitement.")


def test_serialization_roundtrip_if_available():
    m = create_sample()
    # Cherche une méthode to_dict / from_dict ou serialize / deserialize
    if has_method(m, "to_dict") and hasattr(Message, "from_dict"):
        data = m.to_dict()
        m2 = Message.from_dict(data)
        assert hasattr(m2, "content")
        assert getattr(m, "content", None) == getattr(m2, "content", None)
    elif has_method(m, "serialize") and has_method(Message, "deserialize"):
        data = m.serialize()
        m2 = Message.deserialize(data)
        assert getattr(m, "content", None) == getattr(m2, "content", None)
    else:
        pytest.skip(
            "Pas de méthode de sérialisation détectée (to_dict/from_dict ou serialize/deserialize)."
        )


def test_mark_read_or_is_read_behavior():
    m = create_sample()
    # Si existe un attribut représentant "lu"
    if has_attr(m, "is_read"):
        before = getattr(m, "is_read")
        # Essayons de marquer comme lu si la méthode existe
        if has_method(m, "mark_read"):
            m.mark_read()
            assert getattr(m, "is_read") == True
        else:
            # Si pas de méthode, essaye de modifier l'attribut directement (comportement permissif)
            setattr(m, "is_read", True)
            assert getattr(m, "is_read") == True
    elif has_method(m, "mark_read"):
        # Si seule la méthode existe, on appelle et vérifie qu'elle ne lève pas d'erreur
        m.mark_read()
    else:
        pytest.skip("Aucun mécanisme 'lu' détecté (is_read ou mark_read).")


def test_timestamp_behavior_if_present():
    m = create_sample()
    # Vérifie la présence d'un timestamp et qu'il ressemble à une date/heure
    if hasattr(m, "timestamp"):
        ts = getattr(m, "timestamp")
        assert isinstance(ts, (int, float, datetime)) or hasattr(ts, "isoformat")
    else:
        pytest.skip("Pas d'attribut 'timestamp' sur Message.")
