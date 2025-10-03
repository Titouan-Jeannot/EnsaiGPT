import pytest
from ...src.Model.User import User
# from datetime import datetime


def test_user_initialization():
    user = User(
        id=1,
        username="testuser",
        nom="Nom",
        prenom="Prenom",
        mail="test@mail.com",
        password_hash="hashedpassword",
        salt="randomsalt"
    )
    assert user.id == 1
    assert user.username == "testuser"
    assert user.nom == "Nom"
    assert user.prenom == "Prenom"
    assert user.mail == "test@mail.com"
    assert user.password_hash == "hashedpassword"
    assert user.salt == "randomsalt"
    assert user.status == "active"
    assert user.setting_param == "Tu es un assistant utile."


def test_user_init_type_errors():
    with pytest.raises(ValueError):
        User(id="notint", username="testuser", nom="Nom", prenom="Prenom", mail="test@mail.com", password_hash="hashedpassword", salt="randomsalt")
    with pytest.raises(ValueError):
        User(id=1, username=123, nom="Nom", prenom="Prenom", mail="test@mail.com", password_hash="hashedpassword", salt="randomsalt")
    with pytest.raises(ValueError):
        User(id=1, username="testuser", nom=123, prenom="Prenom", mail="test@mail.com", password_hash="hashedpassword", salt="randomsalt")
    with pytest.raises(ValueError):
        User(id=1, username="testuser", nom="Nom", prenom=123, mail="test@mail.com", password_hash="hashedpassword", salt="randomsalt")
    with pytest.raises(ValueError):
        User(id=1, username="testuser", nom="Nom", prenom="Prenom", mail=123, password_hash="hashedpassword", salt="randomsalt")
    with pytest.raises(ValueError):
        User(id=1, username="testuser", nom="Nom", prenom="Prenom", mail="test@mail.com", password_hash=123, salt="randomsalt")
    with pytest.raises(ValueError):
        User(id=1, username="testuser", nom="Nom", prenom="Prenom", mail="test@mail.com", password_hash="hashedpassword", salt=123)
    with pytest.raises(ValueError):
        User(id=1, username="testuser", nom="Nom", prenom="Prenom", mail="test@mail.com", password_hash="hashedpassword", salt="randomsalt", sign_in_date="notadate")
    with pytest.raises(ValueError):
        User(id=1, username="testuser", nom="Nom", prenom="Prenom", mail="test@mail.com", password_hash="hashedpassword", salt="randomsalt", last_login="notadate")
    with pytest.raises(ValueError):
        User(id=1, username="testuser", nom="Nom", prenom="Prenom", mail="test@mail.com", password_hash="hashedpassword", salt="randomsalt", status=123)
    with pytest.raises(ValueError):
        User(id=1, username="testuser", nom="Nom", prenom="Prenom", mail="test@mail.com", password_hash="hashedpassword", salt="randomsalt", setting_param=123)


def test_user_equality():
    user1 = User(id=1, username="testuser", salt="randomsalt", password="hashedpassword")
    user2 = User(id=1, username="testuser", salt="randomsalt", password="hashedpassword")
    user3 = User(id=2, username="otheruser", salt="othersalt", password="otherpassword")

    assert user1 == user2
    assert user1 != user3


def test_user_string_representation():
    user = User(id=1, username="testuser", salt="randomsalt", password="hashedpassword")
    assert str(user) == "User(id=1, username='testuser')"
