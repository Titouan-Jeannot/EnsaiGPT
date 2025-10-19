# Service pour la gestion des utilisateurs

try:
    from Objet_Metier.User import User
    from DAO.user_DAO import UserDAO
except Exception:
    from src.Objet_Metier.User import User
    from src.DAO.user_DAO import UserDAO


class UserService:
    """Service métier pour la gestion des utilisateurs.

    Cette classe centralise la logique applicative (validation, règles, transformation)
    et utilise UserDAO pour l'accès persistant.
    """

    def __init__(self, dao: UserDAO):
        """Initialise le service avec une instance de UserDAO."""
        self.dao = dao

    def create_user(self, user: User) -> User:
        """Crée un utilisateur après validations minimales.

        - Vérifie que le nom d'utilisateur et l'email ne sont pas déjà utilisés.
        - Délègue la création au DAO.
        """
        # validation basique
        if not user.username or not user.mail:
            raise ValueError("username et mail sont requis")

        existing = self.dao.get_by_username(user.username)
        if existing:
            raise ValueError("username déjà utilisé")

        # on pourrait aussi vérifier l'email ici
        return self.dao.create_user(user)

    def get_user_by_id(self, id: int) -> User:
        """Retourne un utilisateur par id ou None si introuvable."""
        return self.dao.get_by_id(id)

    def ge_by_username(self, username: str) -> User:
        """Retourne un utilisateur par username ou None si introuvable."""
        return self.dao.get_by_username(username)

    def update_user(self, user: User) -> bool:
        """Met à jour un utilisateur. Effectue des vérifications avant la mise à jour."""
        if not user.id:
            raise ValueError("id requis pour mise à jour")
        # possibilité: vérifier unicité username/mail
        return self.dao.update_user(user)

    def delete_user(self, id: int) -> bool:
        """Supprime un utilisateur par id."""
        return self.dao.delete_user(id)

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
