"""Objets métier liés aux utilisateurs."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


_ALLOWED_STATUS = {"active", "suspended", "banned"}


@dataclass(slots=True)
class User:
    """Représente un utilisateur persistant.

    Tous les attributs correspondent directement aux colonnes de la base de données.
    Les validations légères exécutées dans :meth:`__post_init__` garantissent que
    l'objet reste cohérent avant de passer aux couches DAO/Service.
    """

    id_user: Optional[int] = None
    username: str = field(default="")
    nom: str = field(default="")
    prenom: str = field(default="")
    mail: str = field(default="")
    password_hash: str = field(default="")
    sign_in_date: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    status: str = field(default="active")
    setting_param: str = field(default="")

    def __post_init__(self) -> None:
        if not isinstance(self.username, str) or not self.username:
            raise ValueError("username doit être une chaîne non vide")
        if not isinstance(self.mail, str) or "@" not in self.mail:
            raise ValueError("mail doit être une adresse valide")
        if not isinstance(self.password_hash, str) or not self.password_hash:
            raise ValueError("password_hash doit être une chaîne non vide")
        if self.status not in _ALLOWED_STATUS:
            raise ValueError("status doit appartenir à {active, suspended, banned}")
        if not isinstance(self.setting_param, str):
            raise ValueError("setting_param doit être une chaîne de caractères")

    def touch_login(self) -> None:
        """Met à jour la date de dernière connexion à maintenant."""

        self.last_login = datetime.utcnow()
