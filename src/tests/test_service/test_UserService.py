# src/tests/test_service/test_UserService.py
from unittest.mock import MagicMock
import datetime
import pytest

# On importe *le module* pour accéder à la classe AuthService que UserService utilise réellement
from src.Service import UserService as USvcMod
from src.Service.UserService import UserService

try:
    from src.ObjetMetier.User import User
except Exception:
    # Backup minimal si l'import du modèle échoue
    class User:
        def __init__(
            self,
            id=None,
            username="",
            nom="",
            prenom="",
            mail="",
            password_hash="",
            salt="",
            sign_in_date=None,
            last_login=None,
            status="active",
            setting_param=None,
        ):
            self.id = id
            self.username = username
            self.nom = nom
            self.prenom = prenom
            self.mail = mail
            self.password_hash = password_hash
            self.salt = salt
            self.sign_in_date = sign_in_date or datetime.datetime.now()
            self.last_login = last_login
            self.status = status
            self.setting_param = setting_param


def make_user(
    id=1,
    mail="u@ex.com",
    username="user",
    nom="Nom",
    prenom="Prenom",
    password_hash="hash",
    salt="salt",
    status="active",
    setting_param="ok",
):
    return User(
        id=id,
        username=username,
        nom=nom,
        prenom=prenom,
        mail=mail,
        password_hash=password_hash,
        salt=salt,
        sign_in_date=datetime.datetime(2024, 1, 1),
        last_login=None,
        status=status,
        setting_param=setting_param,
    )


def real_auth():
    """
    Construit un AuthService qui est *exactement* la classe que le module UserService a importée.
    Garantit que isinstance(auth_service, AuthService) passe.
    """
    AuthCls = USvcMod.AuthService
    dao_mock = MagicMock()
    a = AuthCls(dao_mock)

    # Monkeypatch des méthodes utilisées par UserService
    a.check_user_password_strength = MagicMock()
    a.check_user_email = MagicMock()
    a.check_user_username = MagicMock()
    a.generate_salt = MagicMock()
    a.hash_mdp = MagicMock()
    a.check_user_can_update = MagicMock()
    a.check_user_can_delete = MagicMock()
    a.verify_password = MagicMock()
    return a


# -------------------------------
# create_user
# -------------------------------

def test_create_user_success():
    dao = MagicMock()
    auth = real_auth()

    # Auth checks OK
    auth.check_user_password_strength.return_value = True
    auth.check_user_email.return_value = True
    auth.check_user_username.return_value = True
    auth.generate_salt.return_value = "salt_b64"
    auth.hash_mdp.return_value = "hash_b64"

    created = make_user(
        id=42,
        mail="new@ex.com",
        username="newuser",
        password_hash="hash_b64",
        salt="salt_b64",
    )
    dao.create.return_value = created

    svc = UserService(dao, auth)
    out = svc.create_user(mail="new@ex.com", password_plain="Aa123456!", username="newuser")

    assert out.id == 42
    dao.create.assert_called_once()
    auth.check_user_password_strength.assert_called_once()
    auth.check_user_email.assert_called_once_with(None, "new@ex.com")
    auth.check_user_username.assert_called_once_with(None, "newuser")
    auth.generate_salt.assert_called_once()
    auth.hash_mdp.assert_called_once()


@pytest.mark.parametrize(
    "mail, pwd, username",
    [
        ("", "Aa123456!", "user"),
        ("a@b.com", "", "user"),
        ("a@b.com", "Aa123456!", ""),
    ],
)
def test_create_user_missing_fields(mail, pwd, username):
    dao = MagicMock()
    auth = real_auth()
    svc = UserService(dao, auth)
    with pytest.raises(ValueError):
        svc.create_user(mail=mail, password_plain=pwd, username=username)


def test_create_user_weak_password():
    dao = MagicMock()
    auth = real_auth()
    auth.check_user_password_strength.return_value = False

    svc = UserService(dao, auth)
    with pytest.raises(ValueError):
        svc.create_user(mail="a@b.com", password_plain="weak", username="user")


# -------------------------------
# update_user
# -------------------------------

def test_update_user_success_change_mail_username_password_status():
    dao = MagicMock()
    auth = real_auth()

    user = make_user(id=10, mail="old@ex.com", username="olduser")
    dao.get_user_by_id.return_value = user
    auth.check_user_can_update.return_value = True
    auth.check_user_email.return_value = True
    auth.check_user_username.return_value = True
    auth.check_user_password_strength.return_value = True
    auth.generate_salt.return_value = "newsalt"
    auth.hash_mdp.return_value = "newhash"
    dao.update.return_value = True  # <-- important : renvoyer True

    svc = UserService(dao, auth)
    ok = svc.update_user(
        user_id=10,
        mail="new@ex.com",
        username="newuser",
        password_plain="Aa123456!",
        status="inactive",
        setting_param="Nouvelle config.",
    )
    assert ok is True
    assert user.mail == "new@ex.com"
    assert user.username == "newuser"
    assert user.password_hash == "newhash"
    assert user.salt == "newsalt"
    assert user.status == "inactive"
    assert user.setting_param == "Nouvelle config."
    dao.update.assert_called_once_with(user)


def test_update_user_invalid_status_raises():
    dao = MagicMock()
    auth = real_auth()

    user = make_user(id=1)
    dao.get_user_by_id.return_value = user
    auth.check_user_can_update.return_value = True

    svc = UserService(dao, auth)
    with pytest.raises(ValueError):
        svc.update_user(user_id=1, status="WTF")  # statut invalide


def test_update_user_user_not_found():
    dao = MagicMock()
    auth = real_auth()

    dao.get_user_by_id.return_value = None

    svc = UserService(dao, auth)
    with pytest.raises(ValueError):
        svc.update_user(user_id=999, mail="x@y.com")


# -------------------------------
# get_user_by_id
# -------------------------------

def test_get_user_by_id_resolves_read():
    dao = MagicMock()
    auth = real_auth()
    user = make_user(id=7)

    # Forcer le fallback vers read() : désactiver les callables précédents
    dao.get_user_by_id = None
    dao.get_by_id = None
    dao.read.return_value = user

    svc = UserService(dao, auth)
    got = svc.get_user_by_id(7)
    assert got is user
    dao.read.assert_called_once_with(7)


# -------------------------------
# get_user_by_username
# -------------------------------

def test_get_user_by_username_uses_direct_then_list_fallback():
    dao = MagicMock()
    auth = real_auth()
    user = make_user(username="john")

    # 1) direct
    dao.get_user_by_username.return_value = user
    svc = UserService(dao, auth)
    assert svc.get_user_by_username("john") is user
    dao.get_user_by_username.assert_called_once_with("john")

    # 2) fallback via list_users
    dao.get_user_by_username.reset_mock()
    dao.get_user_by_username = None  # forcer fallback
    dao.list_users.return_value = [make_user(username="alice"), user, make_user(username="bob")]

    assert svc.get_user_by_username("john") is user
    dao.list_users.assert_called_once()


# -------------------------------
# list_users
# -------------------------------

def test_list_users_prefers_list_users_then_all_then_empty():
    dao = MagicMock()
    auth = real_auth()
    svc = UserService(dao, auth)

    # 1) list_users dispo
    ulist = [make_user(id=1), make_user(id=2)]
    dao.list_users.return_value = ulist
    assert svc.list_users() == ulist
    dao.list_users.assert_called_once()

    # 2) fallback all() -> rendre list_users non callable
    dao = MagicMock()
    svc = UserService(dao, auth)
    dao.list_users = None
    dao.all.return_value = ulist
    assert svc.list_users() == ulist
    dao.all.assert_called_once()

    # 3) sinon []
    dao = MagicMock()
    svc = UserService(dao, auth)
    dao.list_users = None
    dao.all = None
    assert svc.list_users() == []


# -------------------------------
# delete_user
# -------------------------------

def test_delete_user_calls_update_user_inactive():
    dao = MagicMock()
    auth = real_auth()
    svc = UserService(dao, auth)

    user = make_user(id=5)
    # get_user_by_id -> via dao.read (utilisé par get_user_by_id dans le service)
    dao.read.return_value = user
    auth.check_user_can_delete.return_value = True

    # Remplacer temporairement la méthode pour "espionner" l'appel sans pytest-mock
    original_update_user = svc.update_user
    try:
        svc.update_user = MagicMock(return_value=True)
        ok = svc.delete_user(5)
        assert ok is True
        svc.update_user.assert_called_once()
        args, kwargs = svc.update_user.call_args
        assert args[0] == 5
        assert kwargs.get("status") == "inactive"
    finally:
        svc.update_user = original_update_user


def test_delete_user_user_not_found_raises():
    dao = MagicMock()
    auth = real_auth()
    svc = UserService(dao, auth)

    # Forcer get_user_by_id à renvoyer None pour déclencher l'erreur
    dao.get_user_by_id = None
    dao.get_by_id = None
    dao.read.return_value = None

    with pytest.raises(ValueError):
        svc.delete_user(123)


# -------------------------------
# authenticate_user
# -------------------------------

def test_authenticate_user_success():
    dao = MagicMock()
    auth = real_auth()
    svc = UserService(dao, auth)

    user = make_user(password_hash="H", salt="S")
    dao.get_user_by_email.return_value = user
    auth.verify_password.return_value = True
    dao.update.return_value = True

    out = svc.authenticate_user("a@b.com", "secret")
    assert out is user
    assert dao.update.called  # last_login mis à jour


def test_authenticate_user_wrong_password_returns_none():
    dao = MagicMock()
    auth = real_auth()
    svc = UserService(dao, auth)

    user = make_user(password_hash="H", salt="S")
    dao.get_user_by_email.return_value = user
    auth.verify_password.return_value = False

    out = svc.authenticate_user("a@b.com", "wrong")
    assert out is None
    dao.update.assert_not_called()


def test_authenticate_user_unknown_email_returns_none():
    dao = MagicMock()
    auth = real_auth()
    svc = UserService(dao, auth)

    dao.get_user_by_email.return_value = None
    out = svc.authenticate_user("unknown@ex.com", "pw")
    assert out is None
