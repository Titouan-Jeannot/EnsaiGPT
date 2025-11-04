"""DAO en mémoire pour les utilisateurs."""
from __future__ import annotations

from typing import Iterable, Optional

from src.DAO.base import BaseInMemoryDAO
from src.ObjetMetier.User import User


class UserDAO(BaseInMemoryDAO[User]):
    """Gestion des utilisateurs dans une structure en mémoire."""

    def __init__(self) -> None:
        super().__init__("id_user")

    # ------------------------------------------------------------------
    # Opérations spécifiques
    # ------------------------------------------------------------------
    def create(self, user: User) -> User:  # type: ignore[override]
        if any(
            existing.mail.lower() == user.mail.lower()
            for existing in self.list_all()
        ):
            raise ValueError("Adresse mail déjà utilisée")
        if any(
            existing.username.lower() == user.username.lower()
            for existing in self.list_all()
        ):
            raise ValueError("Nom d'utilisateur déjà utilisé")
        return super().create(user)

    def read(self, user_id: int) -> Optional[User]:  # type: ignore[override]
        return super().read(user_id)

    def update(self, user: User) -> bool:  # type: ignore[override]
        if user.id_user is None:
            return False
        for existing in self.list_all():
            if existing.id_user == user.id_user:
                continue
            if existing.mail.lower() == user.mail.lower():
                raise ValueError("Adresse mail déjà utilisée")
            if existing.username.lower() == user.username.lower():
                raise ValueError("Nom d'utilisateur déjà utilisé")
        return super().update(user)

    def delete(self, user_id: int) -> bool:  # type: ignore[override]
        return super().delete(user_id)

    # Helpers ------------------------------------------------------------
    def get_user_by_email(self, email: str) -> Optional[User]:
        email_lower = email.lower()
        for user in self.list_all():
            if user.mail.lower() == email_lower:
                return user
        return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        username_lower = username.lower()
        for user in self.list_all():
            if user.username.lower() == username_lower:
                return user
        return None

    def list_users(self) -> Iterable[User]:
        return list(self.list_all())
