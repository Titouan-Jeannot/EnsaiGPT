import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from datetime import datetime, timezone

from Service.UserService import UserService


# -------------------------------------------------------------------
# Fixtures de base : DAO + AuthService mockés + service
# -------------------------------------------------------------------

@pytest.fixture
def mock_user_dao():
    return MagicMock()

@pytest.fixture
def mock_auth_service():
    svc = MagicMock()
    # par défaut : mot de passe fort
    svc.check_user_password_strength.return_value = True
    svc.generate_salt.return_value = "SALT"
    svc.hash_mdp.return_value = "HASHED"
    return svc

@pytest.fixture
def user_service(mock_user_dao, mock_auth_service):
    return UserService(user_dao=mock_user_dao, auth_service=mock_auth_service)


# -------------------------------------------------------------------
# create_user
# -------------------------------------------------------------------

def test_create_user_ok(user_service, mock_user_dao, mock_auth_service):
    # le DAO renvoie un "User" simulé
    created = SimpleNamespace(
        id=1,
        username="bob",
        mail="bob@example.com",
        password_hash="HASHED",
        salt="SALT",
        status="active",
    )
    mock_user_dao.create.return_value = created

    user = user_service.create_user(
        mail="Bob@Example.com",
        password_plain="StrongP4ss!",
        username="bob",
        nom="Durand",
        prenom="Bob",
    )

    # retourne le résultat du DAO
    assert user is created

    # vérifie les appels à AuthService (validation + hash)
    mock_auth_service.check_user_password_strength.assert_called_once_with("StrongP4ss!")
    mock_auth_service.check_user_email.assert_called_once_with(None, "bob@example.com")
    mock_auth_service.check_user_username.assert_called_once_with(None, "bob")
    mock_auth_service.generate_salt.assert_called_once()
    mock_auth_service.hash_mdp.assert_called_once_with("StrongP4ss!", "SALT")

    # vérifie que create a bien été appelé avec un objet ayant les bonnes infos
    assert mock_user_dao.create.call_count == 1
    created_arg = mock_user_dao.create.call_args.args[0]
    assert created_arg.username == "bob"
    assert created_arg.mail == "bob@example.com"
    assert created_arg.password_hash == "HASHED"
    assert created_arg.salt == "SALT"
    assert created_arg.status == "active"
    assert created_arg.setting_param == "Tu es un assistant utile."
    assert isinstance(created_arg.sign_in_date, datetime)


def test_create_user_missing_fields(user_service, mock_auth_service, mock_user_dao):
    with pytest.raises(ValueError):
        user_service.create_user(
            mail="",
            password_plain="StrongP4ss!",
            username="bob",
        )
    with pytest.raises(ValueError):
        user_service.create_user(
            mail="bob@example.com",
            password_plain="",
            username="bob",
        )
    with pytest.raises(ValueError):
        user_service.create_user(
            mail="bob@example.com",
            password_plain="StrongP4ss!",
            username="",
        )

    # pas d'appel au DAO
    mock_user_dao.create.assert_not_called()


def test_create_user_weak_password(user_service, mock_auth_service, mock_user_dao):
    mock_auth_service.check_user_password_strength.return_value = False

    with pytest.raises(ValueError, match="mot de passe doit contenir au moins 8 caractères"):
        user_service.create_user(
            mail="bob@example.com",
            password_plain="weak",
            username="bob",
        )

    mock_user_dao.create.assert_not_called()


# -------------------------------------------------------------------
# get_user_by_id
# -------------------------------------------------------------------

def test_get_user_by_id_uses_preferred_methods_order():
    dao = MagicMock()
    u1 = SimpleNamespace(id=1)
    dao.get_user_by_id.return_value = u1

    svc = UserService(user_dao=dao, auth_service=MagicMock())
    u = svc.get_user_by_id(1)

    assert u is u1
    dao.get_user_by_id.assert_called_once_with(1)


def test_get_user_by_id_fallback_to_get_by_id():
    dao = MagicMock()
    # on force l'absence de get_user_by_id
    if hasattr(dao, "get_user_by_id"):
        delattr(dao, "get_user_by_id")

    u1 = SimpleNamespace(id=2)
    dao.get_by_id.return_value = u1

    svc = UserService(user_dao=dao, auth_service=MagicMock())
    u = svc.get_user_by_id(2)

    assert u is u1
    dao.get_by_id.assert_called_once_with(2)


def test_get_user_by_id_fallback_to_read():
    dao = MagicMock()
    for attr in ("get_user_by_id", "get_by_id"):
        if hasattr(dao, attr):
            delattr(dao, attr)

    u1 = SimpleNamespace(id=3)
    dao.read.return_value = u1

    svc = UserService(user_dao=dao, auth_service=MagicMock())
    u = svc.get_user_by_id(3)

    assert u is u1
    dao.read.assert_called_once_with(3)


def test_get_user_by_id_returns_none_if_all_fail():
    dao = MagicMock()
    for attr in ("get_user_by_id", "get_by_id", "read"):
        if hasattr(dao, attr):
            delattr(dao, attr)

    svc = UserService(user_dao=dao, auth_service=MagicMock())
    assert svc.get_user_by_id(42) is None


# -------------------------------------------------------------------
# get_user_by_username
# -------------------------------------------------------------------

def test_get_user_by_username_direct(user_service, mock_user_dao):
    u = SimpleNamespace(username="bob")
    mock_user_dao.get_user_by_username.return_value = u

    res = user_service.get_user_by_username("bob")
    assert res is u
    mock_user_dao.get_user_by_username.assert_called_once_with("bob")


def test_get_user_by_username_fallback_list(user_service, mock_user_dao):
    if hasattr(mock_user_dao, "get_user_by_username"):
        delattr(mock_user_dao, "get_user_by_username")

    u1 = SimpleNamespace(username="alice")
    u2 = SimpleNamespace(username="bob")
    mock_user_dao.list_users.return_value = [u1, u2]

    res = user_service.get_user_by_username("bob")
    assert res is u2


def test_get_user_by_username_not_found(user_service, mock_user_dao):
    if hasattr(mock_user_dao, "get_user_by_username"):
        delattr(mock_user_dao, "get_user_by_username")

    mock_user_dao.list_users.return_value = []
    assert user_service.get_user_by_username("xx") is None


# -------------------------------------------------------------------
# list_users
# -------------------------------------------------------------------

def test_list_users_prefers_list_users(user_service, mock_user_dao):
    mock_user_dao.list_users.return_value = [1, 2, 3]
    assert user_service.list_users() == [1, 2, 3]


def test_list_users_fallback_all(mock_user_dao, mock_auth_service):
    if hasattr(mock_user_dao, "list_users"):
        delattr(mock_user_dao, "list_users")

    mock_user_dao.all.return_value = [4, 5]
    svc = UserService(user_dao=mock_user_dao, auth_service=mock_auth_service)
    assert svc.list_users() == [4, 5]


def test_list_users_empty_if_no_method(mock_user_dao, mock_auth_service):
    for attr in ("list_users", "all"):
        if hasattr(mock_user_dao, attr):
            delattr(mock_user_dao, attr)

    svc = UserService(user_dao=mock_user_dao, auth_service=mock_auth_service)
    assert svc.list_users() == []


# -------------------------------------------------------------------
# update_user
# -------------------------------------------------------------------

def _fake_user(id_=1):
    return SimpleNamespace(
        id=id_,
        username="olduser",
        nom="Old",
        prenom="User",
        mail="old@example.com",
        password_hash="OLDHASH",
        salt="OLDSALT",
        sign_in_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        last_login=None,
        status="active",
        setting_param="Tu es un assistant utile.",
    )


def test_update_user_not_found(user_service):
    user_service.get_user_by_id = MagicMock(return_value=None)

    with pytest.raises(ValueError, match="Utilisateur non trouvé"):
        user_service.update_user(1, mail="x@example.com")


def test_update_user_simple_fields(user_service, mock_auth_service, mock_user_dao):
    u = _fake_user()
    user_service.get_user_by_id = MagicMock(return_value=u)

    result = user_service.update_user(
        user_id=1,
        mail="NEW@Example.com",
        username=" newuser ",
        nom=" Nouveau ",
        prenom=" Prenom ",
    )

    # check_user_can_update appelé
    mock_auth_service.check_user_can_update.assert_called_once_with(1)

    # mail et username passés à l'AuthService
    mock_auth_service.check_user_email.assert_called_once_with(1, "new@example.com")
    mock_auth_service.check_user_username.assert_called_once_with(1, "newuser")

    # l'objet user a été modifié
    assert u.mail == "new@example.com"
    assert u.username == "newuser"
    assert u.nom == "Nouveau"
    assert u.prenom == "Prenom"

    # update DAO appelé
    mock_user_dao.update.assert_called_once_with(u)
    assert result == mock_user_dao.update.return_value


def test_update_user_change_password(user_service, mock_auth_service, mock_user_dao):
    u = _fake_user()
    user_service.get_user_by_id = MagicMock(return_value=u)

    mock_auth_service.check_user_password_strength.return_value = True
    mock_auth_service.generate_salt.return_value = "NEWSALT"
    mock_auth_service.hash_mdp.return_value = "NEWHASH"

    user_service.update_user(user_id=1, password_plain="NewP4ss!")

    mock_auth_service.check_user_password_strength.assert_called_once_with("NewP4ss!")
    mock_auth_service.generate_salt.assert_called_once()
    mock_auth_service.hash_mdp.assert_called_once_with("NewP4ss!", "NEWSALT")

    assert u.password_hash == "NEWHASH"
    assert u.salt == "NEWSALT"
    mock_user_dao.update.assert_called_once_with(u)


def test_update_user_change_password_weak(user_service, mock_auth_service, mock_user_dao):
    u = _fake_user()
    user_service.get_user_by_id = MagicMock(return_value=u)

    mock_auth_service.check_user_password_strength.return_value = False

    with pytest.raises(ValueError, match="mot de passe doit contenir au moins 8 caractères"):
        user_service.update_user(user_id=1, password_plain="weak")

    mock_user_dao.update.assert_not_called()


def test_update_user_invalid_status(user_service, mock_user_dao):
    u = _fake_user()
    user_service.get_user_by_id = MagicMock(return_value=u)

    with pytest.raises(ValueError, match="Statut invalide"):
        user_service.update_user(user_id=1, status="unknown")

    mock_user_dao.update.assert_not_called()


def test_update_user_valid_status(user_service, mock_user_dao):
    u = _fake_user()
    user_service.get_user_by_id = MagicMock(return_value=u)

    user_service.update_user(user_id=1, status="banni")
    assert u.status == "banni"
    mock_user_dao.update.assert_called_once_with(u)


# 👉 ICI on garde seulement les cas qui lèvent VRAIMENT une ValueError
@pytest.mark.parametrize("bad_value, msg", [
    (123, "chaîne de caractères"),
    ("", "ne peut pas être vide"),
    ("x" * 501, "trop long"),
    ("..truc", "séquences interdites"),
])
def test_update_user_setting_param_invalid(user_service, mock_user_dao, bad_value, msg):
    u = _fake_user()
    user_service.get_user_by_id = MagicMock(return_value=u)

    with pytest.raises(ValueError, match=msg):
        user_service.update_user(user_id=1, setting_param=bad_value)

    mock_user_dao.update.assert_not_called()


def test_update_user_setting_param_sanitizes_html_and_symbols(user_service, mock_user_dao):
    """
    Vérifie le comportement RÉEL du service :
    - les caractères < > & ; / \x00 sont nettoyés par le re.sub AVANT les checks,
    - donc ces valeurs ne déclenchent PAS d'erreur mais sont simplement nettoyées.
    """
    u = _fake_user()
    user_service.get_user_by_id = MagicMock(return_value=u)

    dangerous_values = [
        "<script>alert(1)</script>",
        "abc&def",
        "abc;def",
        "//truc",
        "abc\x00def",
    ]

    for val in dangerous_values:
        mock_user_dao.update.reset_mock()
        res = user_service.update_user(user_id=1, setting_param=val)

        # DAO bien appelé
        mock_user_dao.update.assert_called_once_with(u)
        assert res == mock_user_dao.update.return_value

        # La valeur stockée est nettoyée (pas de <,>,&,;,/ ou \x00)
        stored = u.setting_param
        assert "<" not in stored
        assert ">" not in stored
        assert "&" not in stored
        assert ";" not in stored
        assert "/" not in stored
        assert "\x00" not in stored
        assert len(stored) <= 500


def test_update_user_setting_param_ok(user_service, mock_user_dao):
    u = _fake_user()
    user_service.get_user_by_id = MagicMock(return_value=u)

    s = "Prompt perso utilisateur !?"
    res = user_service.update_user(user_id=1, setting_param=s)

    assert u.setting_param == s
    mock_user_dao.update.assert_called_once_with(u)
    assert res == mock_user_dao.update.return_value


# -------------------------------------------------------------------
# delete_user
# -------------------------------------------------------------------

def test_delete_user_not_found(user_service):
    user_service.get_user_by_id = MagicMock(return_value=None)

    with pytest.raises(ValueError, match="Utilisateur non trouvé"):
        user_service.delete_user(1)


def test_delete_user_uses_auth_and_update(user_service, mock_auth_service):
    u = _fake_user()
    user_service.get_user_by_id = MagicMock(return_value=u)

    # on monkeypatch update_user pour vérifier l'appel
    user_service.update_user = MagicMock(return_value=True)

    res = user_service.delete_user(10)

    mock_auth_service.check_user_can_delete.assert_called_once_with(10)
    user_service.update_user.assert_called_once_with(10, mail=None, status="deleted")
    assert res is True


# -------------------------------------------------------------------
# authenticate_user
# -------------------------------------------------------------------

def test_authenticate_user_dao_without_email_method(mock_user_dao, mock_auth_service):
    svc = UserService(user_dao=mock_user_dao, auth_service=mock_auth_service)
    if hasattr(mock_user_dao, "get_user_by_email"):
        delattr(mock_user_dao, "get_user_by_email")

    with pytest.raises(NotImplementedError):
        svc.authenticate_user("a@b.com", "pwd")


def test_authenticate_user_no_user(user_service, mock_user_dao, mock_auth_service):
    mock_user_dao.get_user_by_email.return_value = None

    res = user_service.authenticate_user("a@b.com", "pwd")
    assert res is None
    mock_auth_service.verify_mdp.assert_not_called()


def test_authenticate_user_wrong_password(user_service, mock_user_dao, mock_auth_service):
    user = _fake_user()
    mock_user_dao.get_user_by_email.return_value = user
    mock_auth_service.verify_mdp.return_value = False

    res = user_service.authenticate_user("a@b.com", "pwd")
    assert res is None
    mock_auth_service.verify_mdp.assert_called_once_with("pwd", user.password_hash, user.salt)
    # pas de mise à jour
    user.last_login is None
    mock_user_dao.update.assert_not_called()


def test_authenticate_user_ok(user_service, mock_user_dao, mock_auth_service):
    user = _fake_user()
    mock_user_dao.get_user_by_email.return_value = user
    mock_auth_service.verify_mdp.return_value = True

    res = user_service.authenticate_user("a@b.com", "pwd")

    assert res is user
    mock_auth_service.verify_mdp.assert_called_once_with("pwd", user.password_hash, user.salt)
    # last_login mis à jour et DAO.update appelé
    assert isinstance(user.last_login, datetime)
    mock_user_dao.update.assert_called_once_with(user)
