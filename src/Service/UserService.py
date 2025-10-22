# Service pour la gestion des utilisateurs

try:
    from Objet_Metier.User import User
    from DAO.User_DAO import UserDAO
except Exception:
    from src.Objet_Metier.User import User
    from src.DAO.User_DAO import UserDAO
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


    def __init__(self, user_dao: UserDAO):
        """Initialise le service avec une instance de UserDAO."""
        self.user_dao = user_dao


    def create_user(self, user: User) -> User:
        """Crée un nouvel utilisateur après validation."""
        # Ici, on pourrait ajouter des validations supplémentaires
        if not user.email:
            raise ValueError("L'email est requis.")
        if not user.password:
            raise ValueError("Le mot de passe est requis.")
        # Nettoyage basique
        user.email = user.email.strip().lower()
        if hasattr(user, "username") and isinstance(user.username, str):
            user.username = user.username.strip()

        # Validation email (pattern simple mais robuste)
        _email_re = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$", re.IGNORECASE)
        if not _email_re.match(user.email):
            raise ValueError("Format d'email invalide.")

        # Nom d'utilisateur obligatoire et règles
        if not hasattr(user, "username") or not user.username:
            raise ValueError("Le nom d'utilisateur est requis.")
        if not (3 <= len(user.username) <= 30):
            raise ValueError("Le nom d'utilisateur doit contenir entre 3 et 30 caractères.")
        if not re.match(r"^[A-Za-z0-9._\-]+$", user.username):
            raise ValueError("Le nom d'utilisateur contient des caractères non autorisés.")

        # Vérifications du mot de passe (longueur et complexité)
        pwd = user.password
        if len(pwd) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        if len(pwd) > 128:
            raise ValueError("Le mot de passe est trop long.")
        if not re.search(r"[0-9]", pwd):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
        if not re.search(r"[a-z]", pwd):
            raise ValueError("Le mot de passe doit contenir au moins une lettre minuscule.")
        if not re.search(r"[A-Z]", pwd):
            raise ValueError("Le mot de passe doit contenir au moins une lettre majuscule.")
        if not re.search(r"[!@#$%^&*()_\-+=\[\]{};:'\",.<>/?\\|`~]", pwd):
            raise ValueError("Le mot de passe doit contenir au moins un caractère spécial.")

        # Contrôles de longueur pour d'autres champs courants
        if hasattr(user, "first_name") and user.first_name and len(user.first_name) > 50:
            raise ValueError("Le prénom est trop long.")
        if hasattr(user, "last_name") and user.last_name and len(user.last_name) > 50:
            raise ValueError("Le nom est trop long.")

        # Vérifier unicité si le DAO propose des méthodes adaptées
        if hasattr(self.user_dao, "get_user_by_email") and self.user_dao.get_user_by_email(user.email): # ajustement user_DAO n'a que read
            raise ValueError("Un utilisateur avec cet email existe déjà.")
        if hasattr(self.user_dao, "get_user_by_username") and self.user_dao.get_user_by_username(user.username):
            raise ValueError("Ce nom d'utilisateur est déjà pris.")

        # Vérification de l'âge minimal si date_de_naissance fournie (=> >= 13 ans)
        """
        if hasattr(user, "date_of_birth") and user.date_of_birth:
            dob = user.date_of_birth
            if isinstance(dob, str):
                try:
                    dob = datetime.date.fromisoformat(dob)
                except Exception:
                    raise ValueError("Le format de la date de naissance est invalide (YYYY-MM-DD attendu).")
            if not isinstance(dob, datetime.date):
                raise ValueError("La date de naissance doit être une date valide.")
            today = datetime.date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 13:
                raise ValueError("L'utilisateur doit avoir au moins 13 ans.")

        # Validation du status si présents
        if hasattr(user, "status") and user.status is not None:
            if not isinstance(user.status, (list, tuple, set)):
                raise ValueError("Le champ status doit être une liste.")
            allowed_status = {"active", "inactive"} # ajustement
            invalid = [s for s in user.status if s not in allowed_status]
            if invalid:
                raise ValueError(f"Statuts invalides: {invalid}")
        """

        # Hachage sécurisé du mot de passe (PBKDF2 + sel)
        # ajustement: c'est un autre service qui gère ça normalement
        def _hash_password(plain: str) -> str:
            salt = os.urandom(16)
            dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, 100_000)
            return base64.b64encode(salt + dk).decode("utf-8")

        user.password = _hash_password(user.password)

        # Suppression/protection de caractères de contrôle dans les champs texte
        # ajustement : j'ai pas compris ce que ça fait
        for attr in ("first_name", "last_name", "username", "email"):
            if hasattr(user, attr) and isinstance(getattr(user, attr), str):
                cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", getattr(user, attr)).strip()
                setattr(user, attr, cleaned)

        return self.user_dao.create(user)

    def get_user_by_id(self, id: int) -> User:
        """Retourne un utilisateur par id ou None si introuvable."""
        return self.dao.get_user_by_id(id)

    def get_user_by_username(self, username: str) -> User:
        """Retourne un utilisateur par username ou None si introuvable."""
        return self.dao.get_user_by_username(username)

    def update_user(self, user: User) -> bool:
        """Met à jour un utilisateur. Effectue des vérifications avant la mise à jour."""
        if not user.id:
            raise ValueError("id requis pour mise à jour")

        # ajustement : faire les verifications avec auth_service pour le mdp, mail, et toute autre info sensible qui pourrait poser problème

        self.auth_service.check_user_password(user.id, user.password) # ajustement : passord hash mais comment verifier qu'il est correcte avant de le hash
        self.auth_service.check_user_email(user.id, user.mail)
        self.auth_service.check_user_username(user.id, user.username)
        self.auth_service.check_user_nom(user.id, user.nom)
        self.auth_service.check_user_prenom(user.id, user.prenom)
        self.auth_service.check_user_exists(user.id)
        self.auth_service.check_user_can_update(user.id)

        return self.dao.update_user(user)

    def delete_user(self, id: int) -> bool:
        """Supprime un utilisateur par id."""
        # ajustement : faire les verification avec auth_service
        self.auth_service.check_user_exists(id)
        self.auth_service.check_user_can_delete(id)
        # self.auth_service.check_user_is_not_admin(id)
        # self.auth_service.check_user_is_not_self(id)

        return self.dao.delete_user(id)





# ajustement : verfifier le code ci-dessous

    def set_user_settings(self, id: int, setting_param: str) -> bool:
        """Met à jour le champ setting_param d'un utilisateur."""
        user = self.dao.get_by_id(id)
        if not user:
            return False
        user.setting_param = setting_param
        return self.dao.update_user(user)

    def update_status(self, id: int, status: str) -> bool:
        """Met à jour le statut d'un utilisateur (ex: active, suspended)."""
        user = self.dao.get_by_id(id)
        if not user:
            return False
        user.status = status
        return self.dao.update_user(user)

    def list_users(self):
        """Retourne la liste de tous les utilisateurs."""
        return self.dao.list_users()

    def _row_to_user(self, row: dict) -> User:
        """Utilitaire de conversion ligne->User si nécessaire."""
        # déléguer au DAO quand il existe
        return self.dao._row_to_user(row)

    # méthode supplémentaire utile: recherche paginée
    def search_by_username_prefix(self, prefix: str):
        """Recherche d'utilisateurs dont le username commence par un préfixe.

        Méthode optionnelle qui effectue une recherche simple.
        """
        # implémentation naïve: récupérer tout et filtrer en mémoire
        users = self.dao.list_users()
        return [u for u in users if u.username.startswith(prefix)]
