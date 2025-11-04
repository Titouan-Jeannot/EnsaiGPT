import pytest

from src.DAO.User_DAO import UserDAO
from src.ObjetMetier.User import User


def build_user(mail: str = "alice@example.com", username: str = "alice") -> User:
    return User(
        id_user=None,
        username=username,
        nom="",
        prenom="",
        mail=mail,
        password_hash="salt$hash",
        setting_param="",
    )


def test_create_and_read_user(user_dao: UserDAO):
    created = user_dao.create(build_user())
    assert created.id_user is not None
    fetched = user_dao.read(created.id_user)
    assert fetched == created


def test_create_duplicate_mail(user_dao: UserDAO):
    user_dao.create(build_user())
    with pytest.raises(ValueError):
        user_dao.create(build_user(username="alice2"))


def test_create_duplicate_username(user_dao: UserDAO):
    user_dao.create(build_user())
    with pytest.raises(ValueError):
        user_dao.create(build_user(mail="bob@example.com"))


def test_update_user(user_dao: UserDAO):
    created = user_dao.create(build_user())
    created.username = "alice2"
    updated = user_dao.update(created)
    assert updated is True
    assert user_dao.read(created.id_user).username == "alice2"


def test_update_invalid_id(user_dao: UserDAO):
    user = build_user()
    assert user_dao.update(user) is False


def test_delete_user(user_dao: UserDAO):
    created = user_dao.create(build_user())
    assert user_dao.delete(created.id_user) is True
    assert user_dao.read(created.id_user) is None


def test_get_user_by_email_and_username(user_dao: UserDAO):
    created = user_dao.create(build_user())
    assert user_dao.get_user_by_email("alice@example.com") == created
    assert user_dao.get_user_by_username("alice") == created
    assert user_dao.get_user_by_email("unknown@example.com") is None
