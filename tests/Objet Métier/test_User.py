import pytest
from datetime import datetime
from src.Objet_Metier.User import User


# Initialisation - succèss (cas explicites)
def test_init_success_minimal_required():
    user = User(None, "jdoe", "Doe", "John", "jdoe@example.com", "hash", "salt")
    assert user.id is None
    assert user.username == "jdoe"
    assert user.status == "active"
    assert user.setting_param == "Tu es un assistant utile."


def test_init_success_with_id_and_dates():
    now = datetime.now()
    user = User(
        1,
        "jdoe",
        "Doe",
        "John",
        "jdoe@example.com",
        "hash",
        "salt",
        sign_in_date=now,
        last_login=now,
        status="active",
        setting_param="param",
    )
    assert user.id == 1
    assert user.sign_in_date == now
    assert user.last_login == now
    assert user.setting_param == "param"


def test_init_success_other_allowed_statuses():
    u_inactive = User(2, "u2", "Nom", "Prenom", "u2@example.com", "h", "s", status="inactive")
    u_banni = User(3, "u3", "Nom", "Prenom", "u3@example.com", "h", "s", status="banni")
    assert u_inactive.status == "inactive"
    assert u_banni.status == "banni"


# Initialisation - échecs (types / valeurs) écrits un par un
def test_init_failure_id_not_int():
    with pytest.raises(ValueError):
        User("notint", "jdoe", "Doe", "John", "jdoe@example.com", "hash", "salt")


def test_init_failure_username_not_str():
    with pytest.raises(ValueError):
        User(1, 123, "Doe", "John", "jdoe@example.com", "hash", "salt")


def test_init_failure_nom_not_str():
    with pytest.raises(ValueError):
        User(1, "jdoe", 123, "John", "jdoe@example.com", "hash", "salt")


def test_init_failure_prenom_not_str():
    with pytest.raises(ValueError):
        User(1, "jdoe", "Doe", 123, "jdoe@example.com", "hash", "salt")


def test_init_failure_mail_not_str():
    with pytest.raises(ValueError):
        User(1, "jdoe", "Doe", "John", 123, "hash", "salt")


def test_init_failure_password_hash_not_str():
    with pytest.raises(ValueError):
        User(1, "jdoe", "Doe", "John", "jdoe@example.com", 123, "salt")


def test_init_failure_salt_not_str():
    with pytest.raises(ValueError):
        User(1, "jdoe", "Doe", "John", "jdoe@example.com", "hash", 123)


def test_init_failure_sign_in_date_wrong_type():
    with pytest.raises(ValueError):
        User(1, "jdoe", "Doe", "John", "jdoe@example.com", "hash", "salt", sign_in_date="notadate")


def test_init_failure_last_login_wrong_type():
    with pytest.raises(ValueError):
        User(1, "jdoe", "Doe", "John", "jdoe@example.com", "hash", "salt", last_login="notadate")


def test_init_failure_status_not_str():
    with pytest.raises(ValueError):
        User(1, "jdoe", "Doe", "John", "jdoe@example.com", "hash", "salt", status=123)


def test_init_failure_status_invalid_value():
    with pytest.raises(ValueError):
        User(1, "jdoe", "Doe", "John", "jdoe@example.com", "hash", "salt", status="InvalidStatus")


def test_init_failure_setting_param_not_str():
    with pytest.raises(ValueError):
        User(1, "jdoe", "Doe", "John", "jdoe@example.com", "hash", "salt", setting_param=123)


def test_init_failure_status_case_and_whitespace():
    with pytest.raises(ValueError):
        User(1, "jdoe", "Doe", "John", "jdoe@example.com", "hash", "salt", status="Active")
    with pytest.raises(ValueError):
        User(1, "jdoe", "Doe", "John", "jdoe@example.com", "hash", "salt", status=" active ")
    with pytest.raises(ValueError):
        User(1, "jdoe", "Doe", "John", "jdoe@example.com", "hash", "salt", status="BANNI")


# __eq__ - succès (cas explicites)
def test_eq_success_identical_objects_explicit():
    now = datetime.now()
    u1 = User(1, "u", "n", "p", "m", "h", "s", sign_in_date=now, last_login=now, status="active", setting_param="x")
    u2 = User(1, "u", "n", "p", "m", "h", "s", sign_in_date=now, last_login=now, status="active", setting_param="x")
    assert u1 == u2
    assert u1 == u1


# __eq__ - échecs (cas explicites)
def test_eq_failure_different_id():
    u1 = User(1, "u", "n", "p", "m", "h", "s")
    u2 = User(2, "u", "n", "p", "m", "h", "s")
    assert u1 != u2


def test_eq_failure_different_username():
    u1 = User(1, "u1", "n", "p", "m", "h", "s")
    u2 = User(1, "u2", "n", "p", "m", "h", "s")
    assert u1 != u2


def test_eq_with_other_type_returns_false():
    u = User(1, "u", "n", "p", "m", "h", "s")
    assert (u == "not a user") is False


# __str__ - succès (explicit)
def test_str_success_explicit():
    user = User(5, "alice", "A", "lice", "a@example.com", "h", "s")
    assert str(user) == "User(id=5, username='alice')


# __str__ - échecs (format inattendu) explicit checks
def test_str_contains_expected_parts():
    user = User(6, "bob", "B", "ob", "b@example.com", "h", "s")
    s = str(user)
    assert "id=6" in s
    assert "username='bob'" in s
    assert s != "User(id=None, username='bob')


# Cas limites / charge légère
def test_large_number_of_users_creation_explicit():
    users = []
    for i in range(100):
        u = User(i, f"user{i}", "Nom", "Prenom", f"user{i}@ex.com", "hash", "salt", status="active" if i % 2 else "inactive")
        users.append(u)
    assert len(users) == 100
    for i, u in enumerate(users):
        assert u.id == i
        assert u.username == f"user{i}"
        assert u.mail == f"user{i}@ex.com"
