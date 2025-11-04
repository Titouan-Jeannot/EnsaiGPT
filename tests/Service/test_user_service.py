import pytest

from src.Service.UserService import UserService


def test_create_user(user_service: UserService):
    user = user_service.create_user("alice", "alice@example.com", "password123")
    assert user.id_user is not None


def test_create_user_invalid(user_service: UserService):
    with pytest.raises(ValueError):
        user_service.create_user("", "", "short")


def test_update_user(user_service: UserService):
    user = user_service.create_user("alice", "alice@example.com", "password123")
    updated = user_service.update_user(user.id_user, username="bob", password="password456")
    assert updated.username == "bob"
    assert updated.password_hash != user.password_hash


def test_update_unknown_user(user_service: UserService):
    with pytest.raises(ValueError):
        user_service.update_user(999, username="ghost")


def test_set_user_settings(user_service: UserService):
    user = user_service.create_user("alice", "alice@example.com", "password123")
    updated = user_service.set_user_settings(user.id_user, "Bonjour")
    assert updated.setting_param == "Bonjour"
    with pytest.raises(ValueError):
        user_service.set_user_settings(user.id_user, "")


def test_update_status(user_service: UserService):
    user = user_service.create_user("alice", "alice@example.com", "password123")
    updated = user_service.update_status(user.id_user, "banned")
    assert updated.status == "banned"
    with pytest.raises(ValueError):
        user_service.update_status(user.id_user, "unknown")


def test_delete_user(user_service: UserService, user_dao):
    user = user_service.create_user("alice", "alice@example.com", "password123")
    assert user_service.delete_user(user.id_user) is True
    assert user_dao.read(user.id_user) is None
