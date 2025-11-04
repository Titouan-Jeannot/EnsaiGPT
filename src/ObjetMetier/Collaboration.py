"""Objet métier Collaboration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


_ALLOWED_ROLES = {"ADMIN", "WRITER", "VIEWER", "BANNED"}


@dataclass(slots=True)
class Collaboration:
    """Associe un utilisateur à une conversation avec un rôle donné."""

    id_collaboration: Optional[int]
    id_conversation: int
    id_user: int
    role: str

    def __post_init__(self) -> None:
        if self.id_conversation <= 0:
            raise ValueError("id_conversation doit être positif")
        if self.id_user <= 0:
            raise ValueError("id_user doit être positif")
        role = self.role.upper()
        if role not in _ALLOWED_ROLES:
            raise ValueError("role invalide")
        self.role = role

    def can_write(self) -> bool:
        """Retourne True si le rôle permet d'écrire."""

        return self.role in {"ADMIN", "WRITER"}

    def is_admin(self) -> bool:
        """Retourne True si le collaborateur est administrateur."""

        return self.role == "ADMIN"
