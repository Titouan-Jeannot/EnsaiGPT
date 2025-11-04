import pytest

from src.Service.AuthService import AuthService


def test_hash_and_verify(auth_service: AuthService):
    hashed = auth_service.hash_mdp("password123")
    assert auth_service.verify_mdp("password123", hashed) is True
    assert auth_service.verify_mdp("wrong", hashed) is False


def test_hash_invalid(auth_service: AuthService):
    with pytest.raises(ValueError):
        auth_service.hash_mdp("short")


def test_authenticate_success(auth_service: AuthService, user_service):
    user = user_service.create_user("alice", "alice@example.com", "password123")
    authenticated = auth_service.authenticate("alice@example.com", "password123")
    assert authenticated.id_user == user.id_user


def test_authenticate_failure(auth_service: AuthService):
    assert auth_service.authenticate("unknown@example.com", "password123") is None
