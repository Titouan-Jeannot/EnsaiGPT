# Service pour la gestion des utilisateurs

try:
    from ObjetMetier.User import User
    from DAO.UserDAO import UserDAO
    from Service.AuthService import AuthService
except Exception:
    from ObjetMetier.User import User
    from DAO.UserDAO import UserDAO
    from Service.AuthService import AuthService
import re
import os
import base64
import hashlib
from datetime import datetime, timezone


class UserService:
    """Service mÃ©tier pour la gestion des utilisateurs.

    Cette classe centralise la logique applicative (validation, rÃ¨gles, transformation)
    et utilise UserDAO pour l'accÃ¨s persistant.
    """

    def __init__(self, user_dao: UserDAO, auth_service: AuthService):
        """Initialise le service avec une instance de UserDAO et AuthService."""
        self.user_dao = user_dao
        #if not isinstance(auth_service, AuthService):
        #    raise ValueError("auth_service doit Ãªtre une instance de AuthService")
        self.auth_service = auth_service

    def create_user(
        self,
        mail: str,
        password_plain: str,
        username: str,
        nom: str = "",
        prenom: str = "",
    ) -> User:
        """
        CrÃ©e un nouvel utilisateur Ã  partir des donnÃ©es brutes.
        GÃ¨re la validation, le hashing du mot de passe et la crÃ©ation de l'objet User.
        """
        # Validation des champs requis
        if not mail or not password_plain or not username:
            raise ValueError("Email, mot de passe et nom d'utilisateur requis")

        # Valide la robustesse du mot de passe (lÃ¨ve en cas d'erreur)
        self.auth_service.check_user_password_strength(password_plain)
        # Nettoyage basique des entrées
        mail = mail.strip().lower()
        username = username.strip()
        nom = nom.strip()
        prenom = prenom.strip()

        # VÃ©rifications via AuthService
        self.auth_service.check_user_email(None, mail)
        self.auth_service.check_user_username(None, username)

        # GÃ©nÃ©ration salt et hash du mot de passe

        salt = self.auth_service.generate_salt()
        password_hash = self.auth_service.hash_mdp(password_plain, salt)

        # CrÃ©ation de l'objet User
        user = User(
            id=None,
            username=username,
            nom=nom,
            prenom=prenom,
            mail=mail,
            password_hash=password_hash,
            salt=salt,
            sign_in_date=datetime.now(timezone.utc),
            last_login=None,
            status="active",
            setting_param="Tu es un assistant utile.",
        )

        # CrÃ©ation en BD via DAO
        created_user = self.user_dao.create(user)
        return created_user

    def update_user(
        self,
        user_id: int,
        mail: str = None,
        password_plain: str = None,
        username: str = None,
        nom: str = None,
        prenom: str = None,
        status: str = None,
        setting_param: str = None,
    ) -> bool:
        """Met Ã  jour un utilisateur Ã  partir des donnÃ©es brutes."""
        # RÃ©cupÃ©rer l'utilisateur existant
        current_user = self.get_user_by_id(user_id)
        if not current_user:
            raise ValueError("Utilisateur non trouvÃ©")

        # VÃ©rifications via AuthService
        self.auth_service.check_user_can_update(user_id)

        # Mise Ã  jour des champs modifiÃ©s
        if mail is not None:
            mail = mail.strip().lower()
            self.auth_service.check_user_email(user_id, mail)
            current_user.mail = mail

        if username is not None:
            username = username.strip()
            self.auth_service.check_user_username(user_id, username)
            current_user.username = username

        if nom is not None:
            current_user.nom = nom.strip()

        if prenom is not None:
            current_user.prenom = prenom.strip()

        if password_plain is not None:
            self.auth_service.check_user_password_strength(password_plain)
            salt = self.auth_service.generate_salt()
            current_user.password_hash = self.auth_service.hash_mdp(
                password_plain, salt
            )
            current_user.salt = salt

        if status is not None:
            if status not in ["active", "inactive", "banni", "deleted"]:
                raise ValueError("Statut invalide")
            current_user.status = status

        if setting_param is not None:
            if not isinstance(setting_param, str):
                raise ValueError("Le paramÃ¨tre de configuration doit Ãªtre une chaÃ®ne de caractÃ¨res.")
            if not setting_param:
                raise ValueError("Le paramÃ¨tre de configuration ne peut pas Ãªtre vide aprÃ¨s nettoyage.")
            # eviter les injections XSS et SQL
            # autoriser uniquement les caractÃ¨res alphanumÃ©riques et quelques symboles plus les espaces, virgules, points , apostrophes, tirets, underscores
            setting_param = re.sub(r'[^a-zA-Z0-9\s,.\-_\'\"!?]', "", setting_param)



            # limiter la longueur
            if len(setting_param) > 500:
                raise ValueError("Le paramÃ¨tre de configuration est trop long.")
            if "<script>" in setting_param.lower():
                raise ValueError("Le paramÃ¨tre de configuration contient du code interdit.")
            if "&" in setting_param or ";" in setting_param:
                raise ValueError("Le paramÃ¨tre de configuration contient des caractÃ¨res interdits.")
            if ".." in setting_param or "//" in setting_param:
                raise ValueError("Le paramÃ¨tre de configuration contient des sÃ©quences interdites.")
            if "\x00" in setting_param:
                raise ValueError("Le paramÃ¨tre de configuration contient des caractÃ¨res nuls interdits.")

            current_user.setting_param = setting_param

        # DÃ©lÃ©guer la mise Ã  jour au DAO
        return self.user_dao.update(current_user)

    # Les mÃ©thodes suivantes sont cohÃ©rentes car ce sont des mÃ©thodes de lecture
    # qui retournent des objets User ou des listes d'objets User
    def get_user_by_id(self, id: int) -> User:
        """Retourne un utilisateur par id ou None si introuvable."""
        # utilisation rÃ©siliente des noms possibles dans le DAO
        for name in ("get_user_by_id", "get_by_id", "read"):
            fn = getattr(self.user_dao, name, None)
            if callable(fn):
                try:
                    return fn(id)
                except Exception:
                    continue
        return None

    def get_user_by_username(self, username: str) -> User:
        """Retourne un utilisateur par username ou None si introuvable."""
        fn = getattr(self.user_dao, "get_user_by_username", None)
        if callable(fn):
            return fn(username)
        # fallback : parcourir la liste si disponible
        fn_list = getattr(self.user_dao, "list_users", None)
        if callable(fn_list):
            for u in fn_list():
                if getattr(u, "username", None) == username:
                    return u
        return None

    def list_users(self):
        """Retourne la liste de tous les utilisateurs."""
        fn = getattr(self.user_dao, "list_users", None) or getattr(
            self.user_dao, "all", None
        )
        if callable(fn):
            return fn()
        return []

    def delete_user(self, user_id: int) -> bool:
        """Supprime un utilisateur par son ID. et change son mail par None"""
        # VÃ©rification que l'utilisateur existe
        current_user = self.get_user_by_id(user_id)
        if not current_user:
            raise ValueError("Utilisateur non trouvÃ©")

        # VÃ©rifications via AuthService
        self.auth_service.check_user_can_delete(user_id)

        # DÃ©lÃ©guer la suppression au DAO
        # et modifier le mail par None pour liberer l'email
        # return self.user_dao.delete(user_id)
        return self.update_user(user_id, mail=None, status="inactive")

    def authenticate_user(self, mail: str, password_plain: str) -> User:
        """Authentifie un utilisateur par email et mot de passe."""
        # RÃ©cupÃ©rer l'utilisateur par email
        fn = getattr(self.user_dao, "get_user_by_email", None)
        if not callable(fn):
            raise NotImplementedError(
                "Le DAO ne supporte pas la recherche par email"
            )
        user = fn(mail)
        if not user:
            return None

        # V?rifier le mot de passe
        verify_fn = getattr(self.auth_service, "verify_password", None) or getattr(
            self.auth_service, "verify_mdp", None
        )
        if callable(verify_fn) and verify_fn(password_plain, user.password_hash, user.salt):
            # Mettre ? jour la date du dernier login
            user.last_login = datetime.now(timezone.utc)
            self.user_dao.update(user)
            return user
        return None
