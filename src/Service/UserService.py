"""Service métier pour les utilisateurs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.DAO.User_DAO import UserDAO
from src.ObjetMetier.User import User
from src.Service.AuthService import AuthService


_ALLOWED_STATUS = {"active", "suspended", "banned"}


@dataclass(slots=True)
class UserService:
    """Regroupe la logique métier autour des utilisateurs."""

    user_dao: UserDAO
    auth_service: AuthService

    # ------------------------------------------------------------------
    def create_user(
        self,
        username: str,
        mail: str,
        password: str,
        nom: str = "",
        prenom: str = "",
    ) -> User:
        if not username or not mail:
            raise ValueError("username et mail sont obligatoires")
        user = self.auth_service.prepare_new_user(username.strip(), mail.strip(), password)
        user.nom = nom
        user.prenom = prenom
        return self.user_dao.create(user)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.user_dao.read(user_id)

    def update_user(
        self,
        user_id: int,
        *,
        username: Optional[str] = None,
        mail: Optional[str] = None,
        password: Optional[str] = None,
        nom: Optional[str] = None,
        prenom: Optional[str] = None,
    ) -> User:
        user = self.user_dao.read(user_id)
        if user is None:
            raise ValueError("Utilisateur introuvable")
        if username:
            user.username = username
        if mail:
            user.mail = mail
        if password:
            user.password_hash = self.auth_service.hash_mdp(password)
        if nom is not None:
            user.nom = nom
        if prenom is not None:
            user.prenom = prenom
        self.user_dao.update(user)
        return user

    def delete_user(self, user_id: int) -> bool:
        return self.user_dao.delete(user_id)

    def set_user_settings(self, user_id: int, setting_param: str) -> User:
        if not isinstance(setting_param, str) or not setting_param.strip():
            raise ValueError("Paramètre de configuration invalide")
        user = self.user_dao.read(user_id)
        if user is None:
            raise ValueError("Utilisateur introuvable")
        user.setting_param = setting_param
        self.user_dao.update(user)
        return user

    def update_status(self, user_id: int, status: str) -> User:
        status_lower = status.lower()
        normalized = {value: value for value in _ALLOWED_STATUS}
        if status_lower not in normalized:
            raise ValueError("Statut utilisateur invalide")
        user = self.user_dao.read(user_id)
        if user is None:
            raise ValueError("Utilisateur introuvable")
        user.status = normalized[status_lower]
        self.user_dao.update(user)
        return user
