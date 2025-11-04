"""Service d'authentification."""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from typing import Optional

from src.DAO.User_DAO import UserDAO
from src.ObjetMetier.User import User


@dataclass(slots=True)
class AuthService:
    """Fournit les primitives nécessaires à l'authentification."""

    user_dao: UserDAO
    iterations: int = 120_000
    salt_size: int = 16

    def _generate_salt(self) -> bytes:
        return os.urandom(self.salt_size)

    def hash_mdp(self, password: str) -> str:
        """Retourne un hash salé encodé en base64."""

        if not isinstance(password, str) or len(password) < 8:
            raise ValueError("Mot de passe trop court")
        salt = self._generate_salt()
        digest = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self.iterations)
        return f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"

    def verify_mdp(self, password: str, stored_hash: str) -> bool:
        """Vérifie qu'un mot de passe correspond au hash stocké."""

        try:
            salt_b64, digest_b64 = stored_hash.split("$", maxsplit=1)
        except ValueError:
            return False
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(digest_b64.encode())
        computed = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self.iterations)
        return compare_digest(expected, computed)

    def authenticate(self, mail: str, password: str) -> Optional[User]:
        """Authentifie un utilisateur à partir de son mail et mot de passe."""

        if not mail or not password:
            return None
        user = self.user_dao.get_user_by_email(mail)
        if user is None:
            return None
        if self.verify_mdp(password, user.password_hash):
            user.touch_login()
            self.user_dao.update(user)
            return user
        return None

    # Helpers pour UserService -----------------------------------------
    def prepare_new_user(self, username: str, mail: str, password: str) -> User:
        """Crée un objet :class:`User` prêt à être persisté."""

        hashed = self.hash_mdp(password)
        return User(
            id_user=None,
            username=username,
            nom="",
            prenom="",
            mail=mail,
            password_hash=hashed,
            setting_param="Tu es un assistant utile.",
        )
