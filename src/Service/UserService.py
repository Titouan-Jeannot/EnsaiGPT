# Service pour la gestion des utilisateurs

try:
    from Objet_Metier.User import User
    from DAO.User_DAO import UserDAO
    from Service.AuthService import AuthService
except Exception:
    from src.Objet_Metier.User import User
    from src.DAO.User_DAO import UserDAO
    from src.Service.AuthService import AuthService
import re
import os
import base64
import hashlib
import datetime


class UserService:
    """Service métier pour la gestion des utilisateurs.

    Cette classe centralise la logique applicative (validation, règles, transformation)
    et utilise UserDAO pour l'accès persistant.
    """

    def __init__(self, user_dao: UserDAO, auth_service: AuthService):
        """Initialise le service avec une instance de UserDAO et AuthService."""
        self.user_dao = user_dao
        if not isinstance(auth_service, AuthService):
            raise ValueError("auth_service doit être une instance de AuthService")
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
        Crée un nouvel utilisateur à partir des données brutes.
        Gère la validation, le hashing du mot de passe et la création de l'objet User.
        """
        # Validation des champs requis
        if not mail or not password_plain or not username:
            raise ValueError("Email, mot de passe et nom d'utilisateur requis")

        if self.auth_service.check_user_password_strength(password_plain) is False:
            raise ValueError(
                "Le mot de passe doit contenir au moins 8 caractères, "
                "une majuscule, une minuscule, un chiffre et un caractère spécial."
            )

        # Nettoyage basique des entrées
        mail = mail.strip().lower()
        username = username.strip()
        nom = nom.strip()
        prenom = prenom.strip()

        # Vérifications via AuthService
        self.auth_service.check_user_email(None, mail)
        self.auth_service.check_user_username(None, username)

        # Génération salt et hash du mot de passe

        salt = self.auth_service.generate_salt()
        password_hash = self.auth_service.hash_mdp(password_plain, salt)

        # Création de l'objet User
        user = User(
            id=None,  # sera généré par la BD ajustement : comment ça se passe
            username=username,
            nom=nom,
            prenom=prenom,
            mail=mail,
            password_hash=password_hash,
            salt=salt,
            sign_in_date=datetime.datetime.now(),
            last_login=None,
            status="active",
            setting_param="Tu es un assistant utile.",
        )

        # Création en BD via DAO
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
        """Met à jour un utilisateur à partir des données brutes."""
        # Récupérer l'utilisateur existant
        # ajustement : il faut verifier que les infos sont valides avant de faire la mise à jour
        current_user = self.get_user_by_id(user_id)
        if not current_user:
            raise ValueError("Utilisateur non trouvé")

        # Vérifications via AuthService
        self.auth_service.check_user_can_update(user_id)

        # Mise à jour des champs modifiés
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
            if self.auth_service.check_user_password_strength(password_plain) is False:
                raise ValueError(
                    "Le mot de passe doit contenir au moins 8 caractères, "
                    "une majuscule, une minuscule, un chiffre et un caractère spécial."
                )
            else:
                salt = self.auth_service.generate_salt()
                current_user.password_hash = self.auth_service.hash_mdp(
                    password_plain, salt
                )
                current_user.salt = salt

        if status is not None:
            if status not in ["active", "inactive", "banni", "delete"]:
                raise ValueError("Statut invalide")
            current_user.status = status

        if setting_param is not None:
            # ajustement : validation possible du parametre
            if not isinstance(setting_param, str):
                raise ValueError("Le paramètre de configuration doit être une chaîne de caractères.")
            if not setting_param:
                raise ValueError("Le paramètre de configuration ne peut pas être vide après nettoyage.")
            # eviter les injections XSS et SQL
            # autoriser uniquement les caractères alphanumériques et quelques symboles plus les espaces, virgules, points , apostrophes, tirets, underscores
            setting_param = re.sub(r"[^a-zA-Z0-9\s,.\-_'\"!?]()", "", setting_param)



            # limiter la longueur
            if len(setting_param) > 500:
                raise ValueError("Le paramètre de configuration est trop long.")
            if "<script>" in setting_param.lower():
                raise ValueError("Le paramètre de configuration contient du code interdit.")
            if "&" in setting_param or ";" in setting_param:
                raise ValueError("Le paramètre de configuration contient des caractères interdits.")
            if ".." in setting_param or "//" in setting_param:
                raise ValueError("Le paramètre de configuration contient des séquences interdites.")
            if "\x00" in setting_param:
                raise ValueError("Le paramètre de configuration contient des caractères nuls interdits.")

            current_user.setting_param = setting_param

        # Déléguer la mise à jour au DAO
        return self.user_dao.update(current_user)

    # Les méthodes suivantes sont cohérentes car ce sont des méthodes de lecture
    # qui retournent des objets User ou des listes d'objets User
    def get_user_by_id(self, id: int) -> User:
        """Retourne un utilisateur par id ou None si introuvable."""
        # utilisation résiliente des noms possibles dans le DAO
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
        """Supprime un utilisateur par son ID."""
        # Vérification que l'utilisateur existe
        current_user = self.get_user_by_id(user_id)
        if not current_user:
            raise ValueError("Utilisateur non trouvé")

        # Vérifications via AuthService
        self.auth_service.check_user_can_delete(user_id)

        # Déléguer la suppression au DAO
        # ajustement : suppression physique ou mettre en status inactive/delete ?
        # return self.user_dao.delete(user_id)
        return self.update_user(user_id, status="inactive")

    def authenticate_user(self, mail: str, password_plain: str) -> User:
        """Authentifie un utilisateur par email et mot de passe."""
        # Récupérer l'utilisateur par email
        fn = getattr(self.user_dao, "get_user_by_email", None)
        if not callable(fn):
            raise NotImplementedError(
                "Le DAO ne supporte pas la recherche par email"
            )
        user = fn(mail)
        if not user:
            return None

        # Vérifier le mot de passe
        if self.auth_service.verify_password(password_plain, user.password_hash, user.salt):
            # Mettre à jour la date du dernier login
            user.last_login = datetime.datetime.now()
            self.user_dao.update(user)
            return user
        return None
