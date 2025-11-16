import os
import base64
import hashlib
import hmac
import time
import re
from typing import Optional
from datetime import datetime, timedelta, timezone


try:
    from ObjetMetier.User import User
    from DAO.UserDAO import UserDAO
except Exception:
    from ObjetMetier.User import User
    from DAO.UserDAO import UserDAO


class AuthService:
    """
    Service d'authentification sécurisé pour l'application.
    - Génère sel (base64), calcule hash via PBKDF2-HMAC-SHA256.
    - Simple protection temporelle après un échec (on garde le timestamp du dernier échec seulement).
    - Méthodes utilitaires compatibles avec le DAO fourni.
    """

    # Paramètres cryptographiques / sécurité
    ITERATIONS = 100_000
    SALT_LEN = 16
    DK_LEN = 32
    # délai minimal après un échec avant de pouvoir réessayer (en secondes)
    RETRY_DELAY_SECONDS = 10

    EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

    def __init__(self, user_dao: UserDAO):
        self.user_dao = user_dao
        # suivi simple en mémoire des derniers échecs : {mail: last_failed_ts}
        self._last_failed = {}

    # ----- fonctions de sel / hash -----
    def generate_salt(self) -> str:
        """Génère un sel aléatoire et le renvoie en base64 (string)."""
        return base64.b64encode(os.urandom(self.SALT_LEN)).decode("ascii")

    def hash_mdp(self, password: str, salt_b64: str) -> str:
        """
        Calcule le hash du mot de passe avec le sel (salt_b64 : base64).
        Retourne le dérivé en base64 (pour stockage dans password_hash).
        Utilise PBKDF2-HMAC-SHA256.
        """
        if not isinstance(password, str) or password == "":
            raise ValueError("password invalide")
        try:
            salt = base64.b64decode(salt_b64)
        except Exception:
            raise ValueError("salt invalide (base64 attendu)")
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, self.ITERATIONS, dklen=self.DK_LEN
        )
        return base64.b64encode(dk).decode("ascii")

    def verify_mdp(
        self, password: str, stored_hash_b64: str, stored_salt_b64: str
    ) -> bool:
        """
        Vérifie un mot de passe en recalculant hash_mdp(password, stored_salt_b64)
        et comparant (en temps-constant) au stored_hash_b64.
        """
        if not isinstance(password, str) or password == "":
            return False
        try:
            computed = self.hash_mdp(password, stored_salt_b64)
        except Exception:
            return False
        # comparaison en temps-constant
        return hmac.compare_digest(computed, stored_hash_b64)

    # ----- helpers DAO résilients -----
    # ajustement : pas compris ce passage
    def _get_user_by_mail(self, mail: str) -> Optional[User]:
        """Utilise les méthodes connues du DAO pour retrouver un user par mail."""
        if not mail:
            return None
        mail = mail.strip().lower()

        # Try direct email lookup methods
        fn = getattr(self.user_dao, "get_user_by_email", None) or getattr(
            self.user_dao, "get_by_email", None
        )
        if callable(fn):
            try:
                return fn(mail)
            except Exception:
                return None

        return None

    # ----- authentification -----
    def authenticate(self, mail: str, password: str) -> Optional[User]:
        """
        Authentifie un utilisateur par mail + mot de passe.
        En cas d'échec, enregistre le timestamp du dernier échec et impose un petit délai avant nouveau essai.
        """
        if not mail or not password:
            # print("1")
            return None
        if not self.EMAIL_RE.match(mail):
            # print("2")
            return None

        # blocage si délai non écoulé depuis dernier échec pour cet email
        last = self._last_failed.get(mail)
        now = datetime.now(timezone.utc)
        if last and (now - last).total_seconds() < self.RETRY_DELAY_SECONDS:
            # print("3")
            return None

        user = self._get_user_by_mail(mail)
        if not user:
            # enregistrer timestamp d'échec et retourner None
            # print("4")
            self._register_failed(mail)
            return None

        # Vérifier via les champs présents
        # DAO et User stockent password_hash (base64) et salt (base64)
        stored_hash = getattr(user, "password_hash", None)
        stored_salt = getattr(user, "salt", None)
        if not stored_hash or not stored_salt:
            # print("5")
            self._register_failed(mail)
            return None

        if self.verify_mdp(password, stored_hash, stored_salt):
            # print("6")
            # succès -> effacer timestamp d'échec
            user.last_login = now
            self.user_dao.update(user)
            if mail in self._last_failed:
                # print("7")
                del self._last_failed[mail]
            return user

        # échec -> enregistrer ts et refuser
        self._register_failed(mail)
        return None

    def _register_failed(self, mail: str):
        """Enregistre le timestamp du dernier échec (pas de compteur)."""
        self._last_failed[mail] = datetime.now(timezone.utc)

    # ----- Méthodes utilitaires appelées par UserService -----
    def check_user_exists(self, user_id: int):
        if user_id is None:
            raise ValueError("id requis")
        fn = (
            getattr(self.user_dao, "read", None)
            or getattr(self.user_dao, "get_user_by_id", None)
            or getattr(self.user_dao, "get_by_id", None)
        )
        if callable(fn):
            user = fn(user_id)
            if not user:
                raise ValueError("Utilisateur introuvable")
            return True
        raise ValueError("Méthode DAO introuvable pour check_user_exists")

    def check_user_password(self, user_id: int, plain_password: str):
        if not plain_password:
            raise ValueError("Mot de passe requis pour vérification")
        # récupérer user via DAO
        fn = getattr(self.user_dao, "read", None) or getattr(
            self.user_dao, "get_user_by_id", None
        )
        user = fn(user_id) if callable(fn) else None
        if not user:
            raise ValueError("Utilisateur introuvable")
        stored_hash = getattr(user, "password_hash", None)
        stored_salt = getattr(user, "salt", None)
        if not stored_hash or not stored_salt:
            raise ValueError("Aucun mot de passe stocké pour cet utilisateur")
        if not self.verify_mdp(plain_password, stored_hash, stored_salt):
            raise ValueError("Mot de passe incorrect")
        return True

    def check_user_email(self, user_id: int, email: str):
        if not email or not self.EMAIL_RE.match(email):
            raise ValueError("Email invalide")
        fn = getattr(self.user_dao, "get_user_by_email", None)
        if callable(fn):
            other = fn(email)
            if other and getattr(other, "id", None) != user_id:
                raise ValueError("Email déjà utilisé")
        return True

    def check_user_username(self, user_id: int, username: str):
        if not username or not isinstance(username, str):
            raise ValueError("Nom d'utilisateur invalide")
        if not (3 <= len(username) <= 30):
            raise ValueError(
                "Le nom d'utilisateur doit contenir entre 3 et 30 caractères."
            )
        if not re.match(r"^[A-Za-z0-9._\-]+$", username):
            raise ValueError("Nom d'utilisateur contient des caractères non autorisés")
        fn = getattr(self.user_dao, "get_user_by_username", None)
        if callable(fn):
            other = fn(username)
            if other and getattr(other, "id", None) != user_id:
                raise ValueError("Nom d'utilisateur déjà pris")
        return True

    def check_user_nom(self, user_id: int, nom: str):
        if nom is None:
            return True
        if not isinstance(nom, str) or len(nom) > 50:
            raise ValueError("Nom invalide ou trop long")
        return True

    def check_user_prenom(self, user_id: int, prenom: str):
        if prenom is None:
            return True
        if not isinstance(prenom, str) or len(prenom) > 50:
            raise ValueError("Prénom invalide ou trop long")
        return True

    def check_user_can_update(self, user_id: int):
        # vérifier existence
        fn = getattr(self.user_dao, "read", None) or getattr(
            self.user_dao, "get_user_by_id", None
        )
        user = fn(user_id) if callable(fn) else None
        if not user:
            raise ValueError("Utilisateur introuvable")
        # ne pas autoriser si status est 'banni' ou 'inactive'
        status = getattr(user, "status", None)
        if status and status.lower() in ("banni", "inactive"):
            raise ValueError("Utilisateur non modifiable (banni/supprimé)")
        return True

    def check_user_can_delete(self, user_id: int):
        return self.check_user_can_update(user_id)

    # remplace l'ancienne check_user_is_not_admin inexistante
    def check_user_not_banned_or_deleted(self, user_id: int):
        fn = getattr(self.user_dao, "read", None) or getattr(
            self.user_dao, "get_user_by_id", None
        )
        user = fn(user_id) if callable(fn) else None
        if not user:
            raise ValueError("Utilisateur introuvable")
        status = getattr(user, "status", None)
        if status and status.lower() in ("banni", "inactive"):
            raise ValueError("Action interdite : utilisateur banni ou supprimé")
        return True

    def check_user_is_not_self(self, current_user_id: int, target_user_id: int):
        if current_user_id == target_user_id:
            raise ValueError("Action interdite sur soi-même")
        return True

    def check_user_password_strength(self, password: str):
        if not password or len(password) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Le mot de passe doit contenir au moins une lettre majuscule.")
        if not re.search(r"[a-z]", password):
            raise ValueError("Le mot de passe doit contenir au moins une lettre minuscule.")
        if not re.search(r"[0-9]", password):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("Le mot de passe doit contenir au moins un caractère spécial.")
        return True
