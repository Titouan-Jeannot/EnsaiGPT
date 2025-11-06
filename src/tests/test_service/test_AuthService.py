# src/tests/test_service/test_AuthService.py
import base64
import re
import time
import pytest
from unittest.mock import MagicMock

from src.Service.AuthService import AuthService

# Petit helper pour fabriquer un "user" léger
class DummyUser:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# -----------------------------
# Tests sel / hash / verify_mdp
# -----------------------------
def test_generate_salt_is_base64_and_len():
    svc = AuthService(user_dao=MagicMock())
    s = svc.generate_salt()
    # base64 décodable
    decoded = base64.b64decode(s)
    # longueur du sel conforme
    assert isinstance(s, str)
    assert len(decoded) == svc.SALT_LEN


def test_hash_mdp_and_verify_ok():
    svc = AuthService(user_dao=MagicMock())
    salt = svc.generate_salt()
    h = svc.hash_mdp("Secret123!", salt)
    # bien en base64
    base64.b64decode(h)
    assert svc.verify_mdp("Secret123!", h, salt) is True
    assert svc.verify_mdp("mauvais", h, salt) is False


def test_hash_mdp_invalid_inputs():
    svc = AuthService(user_dao=MagicMock())
    with pytest.raises(ValueError):
        svc.hash_mdp("", svc.generate_salt())
    with pytest.raises(ValueError):
        svc.hash_mdp("ok", "###pas-base64###")


# -----------------------------
# Tests _get_user_by_mail
# -----------------------------
def test_get_user_by_mail_calls_dao_when_valid_email():
    mock_dao = MagicMock()
    user = DummyUser(id=1, mail="test@example.com")
    mock_dao.get_user_by_email.return_value = user

    svc = AuthService(mock_dao)
    got = svc._get_user_by_mail("test@example.com")
    mock_dao.get_user_by_email.assert_called_once_with("test@example.com")
    assert got is user


def test_get_user_by_mail_invalid_empty_returns_none():
    mock_dao = MagicMock()
    svc = AuthService(mock_dao)
    assert svc._get_user_by_mail("") is None
    mock_dao.get_user_by_email.assert_not_called()


# -----------------------------
# Tests authenticate
# -----------------------------
def test_authenticate_success_updates_last_login_and_clears_fail():
    mock_dao = MagicMock()
    svc = AuthService(mock_dao)

    # Prépare user avec hash/salt cohérents
    salt = svc.generate_salt()
    pwd = "StrongPwd!42"
    h = svc.hash_mdp(pwd, salt)
    user = DummyUser(id=7, mail="ok@example.com", password_hash=h, salt=salt, status="active")

    mock_dao.get_user_by_email.return_value = user

    # Simule un échec antérieur pour vérifier qu'il se nettoie après succès
    svc._last_failed["ok@example.com"] = time.time() - (svc.RETRY_DELAY_SECONDS + 1)

    got = svc.authenticate("ok@example.com", pwd)
    assert got is user
    mock_dao.update.assert_called_once()  # mise à jour last_login
    assert "ok@example.com" not in svc._last_failed


def test_authenticate_rejects_invalid_email_format():
    mock_dao = MagicMock()
    svc = AuthService(mock_dao)
    assert svc.authenticate("not-an-email", "whatever") is None
    mock_dao.get_user_by_email.assert_not_called()


def test_authenticate_unknown_user_registers_failure_and_blocks_retry(monkeypatch):
    mock_dao = MagicMock()
    mock_dao.get_user_by_email.return_value = None
    svc = AuthService(mock_dao)

    # 1er essai: user inconnu => échec + enregistre le timestamp
    t0 = 1000.0
    monkeypatch.setattr("time.time", lambda: t0)
    assert svc.authenticate("ghost@example.com", "pwd") is None
    assert svc._last_failed.get("ghost@example.com") == t0

    # 2e essai trop tôt: doit refuser sans même appeler le DAO
    mock_dao.reset_mock()
    t1 = t0 + svc.RETRY_DELAY_SECONDS - 1
    monkeypatch.setattr("time.time", lambda: t1)
    assert svc.authenticate("ghost@example.com", "pwd") is None
    mock_dao.get_user_by_email.assert_not_called()


def test_authenticate_missing_hash_or_salt_is_failure(monkeypatch):
    mock_dao = MagicMock()
    user = DummyUser(id=1, mail="u@example.com", password_hash=None, salt="abc")
    mock_dao.get_user_by_email.return_value = user
    svc = AuthService(mock_dao)

    # Pas de hash
    assert svc.authenticate("u@example.com", "x") is None
    # Ajout du hash mais pas de salt
    user.password_hash = "deadbeef"
    user.salt = None
    assert svc.authenticate("u@example.com", "x") is None


def test_authenticate_wrong_password_registers_failure(monkeypatch):
    mock_dao = MagicMock()
    svc = AuthService(mock_dao)
    salt = svc.generate_salt()
    h = svc.hash_mdp("CorrectPwd!1", salt)
    user = DummyUser(id=2, mail="u2@example.com", password_hash=h, salt=salt)
    mock_dao.get_user_by_email.return_value = user

    t0 = 2000.0
    monkeypatch.setattr("time.time", lambda: t0)
    assert svc.authenticate("u2@example.com", "badpwd") is None
    assert svc._last_failed.get("u2@example.com") == t0


# -----------------------------
# Tests helpers check_*
# -----------------------------
def test_check_user_exists_ok_with_read():
    mock_dao = MagicMock()
    mock_dao.read.return_value = DummyUser(id=10)
    svc = AuthService(mock_dao)
    assert svc.check_user_exists(10) is True
    mock_dao.read.assert_called_once_with(10)


def test_check_user_exists_raises_if_absent():
    mock_dao = MagicMock()
    mock_dao.read.return_value = None
    svc = AuthService(mock_dao)
    with pytest.raises(ValueError):
        svc.check_user_exists(99)


def test_check_user_password_ok():
    mock_dao = MagicMock()
    svc = AuthService(mock_dao)
    salt = svc.generate_salt()
    h = svc.hash_mdp("OkPass!9", salt)
    mock_dao.read.return_value = DummyUser(id=5, password_hash=h, salt=salt)
    assert svc.check_user_password(5, "OkPass!9") is True


def test_check_user_password_raises_on_missing_or_wrong():
    mock_dao = MagicMock()
    svc = AuthService(mock_dao)
    # Pas d'utilisateur
    mock_dao.read.return_value = None
    with pytest.raises(ValueError):
        svc.check_user_password(1, "x")

    # Pas de hash/salt
    mock_dao.read.return_value = DummyUser(id=1, password_hash=None, salt=None)
    with pytest.raises(ValueError):
        svc.check_user_password(1, "x")

    # Mauvais mot de passe
    salt = svc.generate_salt()
    h = svc.hash_mdp("GoodOne!3", salt)
    mock_dao.read.return_value = DummyUser(id=1, password_hash=h, salt=salt)
    with pytest.raises(ValueError):
        svc.check_user_password(1, "WrongOne")


def test_check_user_email_ok_and_uniqueness():
    mock_dao = MagicMock()
    mock_dao.get_user_by_email.return_value = None
    svc = AuthService(mock_dao)
    assert svc.check_user_email(10, "free@example.com") is True

    # déjà utilisé par un autre
    mock_dao.get_user_by_email.return_value = DummyUser(id=11)
    with pytest.raises(ValueError):
        svc.check_user_email(10, "busy@example.com")

    # email invalide
    with pytest.raises(ValueError):
        svc.check_user_email(10, "not-an-email")


def test_check_user_username_rules_and_uniqueness():
    mock_dao = MagicMock()
    svc = AuthService(mock_dao)

    # invalides
    with pytest.raises(ValueError):
        svc.check_user_username(1, "")
    with pytest.raises(ValueError):
        svc.check_user_username(1, "ab")  # trop court
    with pytest.raises(ValueError):
        svc.check_user_username(1, "x" * 31)  # trop long
    with pytest.raises(ValueError):
        svc.check_user_username(1, "bad space")
    with pytest.raises(ValueError):
        svc.check_user_username(1, "éèà")  # non autorisé

    # uniqueness
    mock_dao.get_user_by_username.return_value = DummyUser(id=99)
    with pytest.raises(ValueError):
        svc.check_user_username(1, "existing_ok")

    # ok (libre)
    mock_dao.get_user_by_username.return_value = None
    assert svc.check_user_username(1, "valid.name_123") is True


def test_check_user_nom_and_prenom_rules():
    svc = AuthService(MagicMock())
    assert svc.check_user_nom(1, None) is True
    assert svc.check_user_prenom(1, None) is True

    assert svc.check_user_nom(1, "Dupont") is True
    assert svc.check_user_prenom(1, "Alice") is True

    with pytest.raises(ValueError):
        svc.check_user_nom(1, "x" * 51)
    with pytest.raises(ValueError):
        svc.check_user_prenom(1, "x" * 51)
    with pytest.raises(ValueError):
        svc.check_user_nom(1, 123)  # mauvais type
    with pytest.raises(ValueError):
        svc.check_user_prenom(1, 123)  # mauvais type


def test_check_user_can_update_and_delete_status():
    mock_dao = MagicMock()
    svc = AuthService(mock_dao)

    # user actif OK
    mock_dao.read.return_value = DummyUser(id=1, status="active")
    assert svc.check_user_can_update(1) is True
    assert svc.check_user_can_delete(1) is True  # délégué

    # user banni
    mock_dao.read.return_value = DummyUser(id=2, status="banni")
    with pytest.raises(ValueError):
        svc.check_user_can_update(2)

    # user inactif/inactive
    mock_dao.read.return_value = DummyUser(id=3, status="inactive")
    with pytest.raises(ValueError):
        svc.check_user_can_update(3)

    # user introuvable
    mock_dao.read.return_value = None
    with pytest.raises(ValueError):
        svc.check_user_can_update(9)


def test_check_user_not_banned_or_deleted():
    mock_dao = MagicMock()
    svc = AuthService(mock_dao)

    mock_dao.read.return_value = DummyUser(id=1, status="active")
    assert svc.check_user_not_banned_or_deleted(1) is True

    mock_dao.read.return_value = DummyUser(id=2, status="banni")
    with pytest.raises(ValueError):
        svc.check_user_not_banned_or_deleted(2)

    mock_dao.read.return_value = None
    with pytest.raises(ValueError):
        svc.check_user_not_banned_or_deleted(42)


def test_check_user_is_not_self():
    svc = AuthService(MagicMock())
    assert svc.check_user_is_not_self(1, 2) is True
    with pytest.raises(ValueError):
        svc.check_user_is_not_self(5, 5)
