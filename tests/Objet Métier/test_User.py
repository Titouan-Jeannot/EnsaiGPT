import pytest
from datetime import datetime
from src.Objet_Metier.User import User


def test_user_initialization_with_id_and_dates():
    now = datetime.now()
    user = User(
        id=1,
        username="jdoe",
        nom="Doe",
        prenom="John",
        mail="jdoe@example.com",
        password_hash="hash",
        salt="salt",
        sign_in_date=now,
        last_login=now,
        status="active",
        setting_param="param",
    )
    assert user.id == 1
    assert user.username == "jdoe"
    assert user.nom == "Doe"
    assert user.prenom == "John"
    assert user.mail == "jdoe@example.com"
    assert user.password_hash == "hash"
    assert user.salt == "salt"
    assert user.sign_in_date == now
    assert user.last_login == now
    assert user.status == "active"
    assert user.setting_param == "param"


def test_user_initialization_with_id_none_allowed():
    user = User(
        id=None,
        username="anon",
        nom="An",
        prenom="On",
        mail="anon@example.com",
        password_hash="h",
        salt="s",
    )
    assert user.id is None
    assert user.status == "active"
    assert isinstance(user.setting_param, str)


def test_user_init_type_errors_and_invalid_status():
    now = datetime.now()
    with pytest.raises(ValueError):
        User(
            id="notint",
            username="u",
            nom="n",
            prenom="p",
            mail="m",
            password_hash="h",
            salt="s",
        )
    with pytest.raises(ValueError):
        User(
            id=1,
            username=123,
            nom="n",
            prenom="p",
            mail="m",
            password_hash="h",
            salt="s",
        )
    with pytest.raises(ValueError):
        User(
            id=1,
            username="u",
            nom=123,
            prenom="p",
            mail="m",
            password_hash="h",
            salt="s",
        )
    with pytest.raises(ValueError):
        User(
            id=1,
            username="u",
            nom="n",
            prenom=123,
            mail="m",
            password_hash="h",
            salt="s",
        )
    with pytest.raises(ValueError):
        User(
            id=1,
            username="u",
            nom="n",
            prenom="p",
            mail=123,
            password_hash="h",
            salt="s",
        )
    with pytest.raises(ValueError):
        User(
            id=1,
            username="u",
            nom="n",
            prenom="p",
            mail="m",
            password_hash=123,
            salt="s",
        )
    with pytest.raises(ValueError):
        User(
            id=1,
            username="u",
            nom="n",
            prenom="p",
            mail="m",
            password_hash="h",
            salt=123,
        )
    with pytest.raises(ValueError):
        User(
            id=1,
            username="u",
            nom="n",
            prenom="p",
            mail="m",
            password_hash="h",
            salt="s",
            sign_in_date="notadate",
        )
    with pytest.raises(ValueError):
        User(
            id=1,
            username="u",
            nom="n",
            prenom="p",
            mail="m",
            password_hash="h",
            salt="s",
            last_login="notadate",
        )
    with pytest.raises(ValueError):
        User(
            id=1,
            username="u",
            nom="n",
            prenom="p",
            mail="m",
            password_hash="h",
            salt="s",
            status=123,
        )
    with pytest.raises(ValueError):
        User(
            id=1,
            username="u",
            nom="n",
            prenom="p",
            mail="m",
            password_hash="h",
            salt="s",
            status="invalid",
        )
    with pytest.raises(ValueError):
        User(
            id=1,
            username="u",
            nom="n",
            prenom="p",
            mail="m",
            password_hash="h",
            salt="s",
            setting_param=123,
        )


def test_user_equality_and_inequality():
    now = datetime.now()
    u1 = User(
        1,
        "u",
        "n",
        "p",
        "m",
        "h",
        "s",
        sign_in_date=now,
        last_login=now,
        status="active",
        setting_param="x",
    )
    u2 = User(
        1,
        "u",
        "n",
        "p",
        "m",
        "h",
        "s",
        sign_in_date=now,
        last_login=now,
        status="active",
        setting_param="x",
    )
    u3 = User(2, "u2", "n2", "p2", "m2", "h2", "s2")
    assert u1 == u2
    assert u1 != u3
    assert not (u1 == "not a user")


def test_str_representation():
    user = User(5, "alice", "A", "lice", "a@example.com", "h", "s")
    assert str(user) == "User(id=5, username='alice')"


def test_default_values_and_edge_cases():
    # defaults
    user = User(10, "bob", "B", "ob", "b@example.com", "h", "s")
    assert user.sign_in_date is None
    assert user.last_login is None
    assert user.status == "active"
    assert user.setting_param == "Tu es un assistant utile."

    # large id values
    max_int = 2**31 - 1
    u_max = User(
        max_int, "big", "N", "Big", "big@example.com", "h", "s", status="banni"
    )
    assert u_max.id == max_int
    assert u_max.status == "banni"


def test_status_case_and_whitespace_handling():
    with pytest.raises(ValueError):
        User(1, "u", "n", "p", "m", "h", "s", status="Active")
    with pytest.raises(ValueError):
        User(1, "u", "n", "p", "m", "h", "s", status=" active ")
    with pytest.raises(ValueError):
        User(1, "u", "n", "p", "m", "h", "s", status="BANNI")


def test_large_number_of_users_creation():
    users = []
    for i in range(200):  # reduced to 200 for test speed while still checking scale
        u = User(
            i,
            f"user{i}",
            "Nom",
            "Prenom",
            f"user{i}@ex.com",
            "hash",
            "salt",
            status="viewer" if i % 2 == 0 else "active",
        )
        users.append(u)
    assert len(users) == 200
    for i, u in enumerate(users):
        assert u.id == i
        assert u.username == f"user{i}"
        assert u.mail == f"user{i}@ex.com"
