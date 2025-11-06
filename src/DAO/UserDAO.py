import logging

from psycopg2.errors import DatabaseError, IntegrityError
from psycopg2.extras import RealDictCursor

from src.DAO.DBConnector import DBConnection

try:
    from src.ObjetMetier.User import User
except Exception:
    from ObjetMetier.User import User


class UserDAO:
    """DAO pour User : CRUD + recherche, basé sur DBConnection (pool partagé)."""

    # --- CREATE ---
    def create(self, user: User) -> User:
        query = """
        INSERT INTO users (username, nom, prenom, mail, password_hash, salt,
                           sign_in_date, last_login, status, setting_param)
        VALUES (%(username)s, %(nom)s, %(prenom)s, %(mail)s, %(password_hash)s,
                %(salt)s, %(sign_in_date)s, %(last_login)s, %(status)s, %(setting_param)s)
        RETURNING id_user;
        """
        try:
            with DBConnection().connection as conn:
                with conn.cursor(RealDictCursor) as cur:
                    cur.execute(
                        query,
                        {
                            "username": user.username,
                            "nom": user.nom,
                            "prenom": user.prenom,
                            "mail": user.mail,
                            "password_hash": user.password_hash,
                            "salt": user.salt,
                            "sign_in_date": user.sign_in_date,
                            "last_login": user.last_login,
                            "status": user.status,
                            "setting_param": user.setting_param,
                        },
                    )
                    row = cur.fetchone()
                    user.id = row["id_user"] if row else None
            return user
        except IntegrityError as e:
            logging.error(f"Contrainte violation : {e}")
            raise ValueError("Contrainte violation (username/mail déjà utilisé)") from e
        except DatabaseError as e:
            logging.error(f"Erreur BDD : {e}")
            raise

    # --- READ (by ID) ---
    def read(self, user_id: int):
        """Lit un utilisateur par id. Retourne None si non trouvé."""
        query = "SELECT * FROM users WHERE id_user = %(id)s;"
        with DBConnection().connection as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, {"id": user_id})
                row = cur.fetchone()
                if not row:
                    return None
                return User(
                    id=row["id_user"],
                    username=row["username"],
                    nom=row["nom"],
                    prenom=row["prenom"],
                    mail=row["mail"],
                    password_hash=row["password_hash"],
                    salt=row["salt"],
                    sign_in_date=row["sign_in_date"],
                    last_login=row["last_login"],
                    status=row["status"],
                    setting_param=row["setting_param"],
                )

    # --- UPDATE ---
    def update(self, user: User) -> bool:
        query = """
        UPDATE users
           SET username=%(username)s,
               nom=%(nom)s,
               prenom=%(prenom)s,
               mail=%(mail)s,
               password_hash=%(password_hash)s,
               salt=%(salt)s,
               sign_in_date=%(sign_in_date)s,
               last_login=%(last_login)s,
               status=%(status)s,
               setting_param=%(setting_param)s
         WHERE id_user=%(id)s;
        """
        try:
            with DBConnection().connection as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        query,
                        {
                            "username": user.username,
                            "nom": user.nom,
                            "prenom": user.prenom,
                            "mail": user.mail,
                            "password_hash": user.password_hash,
                            "salt": user.salt,
                            "sign_in_date": user.sign_in_date,
                            "last_login": user.last_login,
                            "status": user.status,
                            "setting_param": user.setting_param,
                            "id": user.id,
                        },
                    )
                    return cur.rowcount == 1
        except IntegrityError as e:
            logging.error(f"Contrainte violation update : {e}")
            raise ValueError("Username ou email déjà utilisé") from e
        except DatabaseError as e:
            logging.error(f"Erreur update BDD : {e}")
            raise

    # --- DELETE ---
    def delete(self, user_id: int) -> bool:
        """Supprime un utilisateur par id_user."""
        query = "DELETE FROM users WHERE id_user = %(id)s;"
        with DBConnection().connection as conn:
            with conn.cursor() as cur:
                cur.execute(query, {"id": user_id})
                return cur.rowcount > 0

    # --- READ by EMAIL ---
    def get_user_by_email(self, email: str):
        """Lit un utilisateur par email. Retourne None si non trouvé."""
        query = "SELECT * FROM users WHERE mail = %(email)s;"
        with DBConnection().connection as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, {"email": email})
                row = cur.fetchone()
                if not row:
                    return None
                return User(
                    id=row["id_user"],
                    username=row["username"],
                    nom=row["nom"],
                    prenom=row["prenom"],
                    mail=row["mail"],
                    password_hash=row["password_hash"],
                    salt=row["salt"],
                    sign_in_date=row["sign_in_date"],
                    last_login=row["last_login"],
                    status=row["status"],
                    setting_param=row["setting_param"],
                )

    # --- READ by USERNAME ---
    def get_user_by_username(self, username: str):
        """Lit un utilisateur par username. Retourne None si non trouvé."""
        query = "SELECT * FROM users WHERE username = %(u)s;"
        with DBConnection().connection as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, {"u": username})
                row = cur.fetchone()
                if not row:
                    return None
                return User(
                    id=row["id_user"],
                    username=row["username"],
                    nom=row["nom"],
                    prenom=row["prenom"],
                    mail=row["mail"],
                    password_hash=row["password_hash"],
                    salt=row["salt"],
                    sign_in_date=row["sign_in_date"],
                    last_login=row["last_login"],
                    status=row["status"],
                    setting_param=row["setting_param"],
                )

    def update_last_login(self, user_id: int) -> None:
        """
        Met à jour la date du dernier login pour un utilisateur.
        ajustement : Est-ce que c'est en UTC ?
        """
        query = "UPDATE users SET last_login = NOW() WHERE id_user = %(id)s;"
        with DBConnection().connection as conn:
            with conn.cursor() as cur:
                cur.execute(query, {"id": user_id})
            conn.commit()


'''import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError, DatabaseError

# Import User from the project domain model
try:
    from ObjetMetier.User import User
except Exception:
    from src.ObjetMetier.User import User


class UserDAO:
    """DAO minimal pour User : create, read, update, delete, list.

    Cette classe attend une connexion psycopg2 existante ou une DSN.
    """

    def __init__(self, conn):
        """Initialise le DAO avec une connexion psycopg2."""

        if isinstance(conn, str):
            self.conn = psycopg2.connect(conn)
        else:
            self.conn = conn

    def create(self, user: User) -> User:
        query = """
        INSERT INTO users (username, nom, prenom, mail, password_hash, salt,
                          sign_in_date, last_login, status, setting_param)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        try:
            # Ajouter context manager pour transactions
            with self.conn.transaction():
                with self.conn.cursor() as cursor:
                    cursor.execute(
                        query,
                        (
                            user.username,
                            user.nom,
                            user.prenom,
                            user.mail,
                            user.password_hash,
                            user.salt,
                            user.sign_in_date,
                            user.last_login,
                            user.status,
                            user.setting_param,
                        ),
                    )
                    user.id = cursor.fetchone()[0]
            return user
        except IntegrityError as e:
            # rollback géré par le context manager
            # remonter une erreur métier claire
            raise ValueError(
                "Contrainte violation (username/email déjà utilisé)"
            ) from e
        except DatabaseError as e:
            # rollback géré par le context manager
            raise

    def read(self, user_id: int) -> User:
        """Lit un utilisateur par id. Retourne None si non trouvé."""
        query = "SELECT * FROM users WHERE id=%s;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (user_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return User(
                id=row["id"],
                username=row["username"],
                nom=row["nom"],
                prenom=row["prenom"],
                mail=row["mail"],
                password_hash=row["password_hash"],
                salt=row["salt"],
                sign_in_date=row["sign_in_date"],
                last_login=row["last_login"],
                status=row["status"],
                setting_param=row["setting_param"],
            )

    def update(self, user: User) -> bool:
        query = """
        UPDATE users
        SET username=%s, nom=%s, prenom=%s, mail=%s, password_hash=%s, salt=%s, sign_in_date=%s, last_login=%s, status=%s, setting_param=%s
        WHERE id=%s;
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        user.username,
                        user.nom,
                        user.prenom,
                        user.mail,
                        user.password_hash,
                        user.salt,
                        user.sign_in_date,
                        user.last_login,
                        user.status,
                        user.setting_param,
                        user.id,
                    ),
                )
            self.conn.commit()
            return cursor.rowcount > 0
        except IntegrityError as e:
            self.conn.rollback()
            raise ValueError(
                "Contrainte violation (username/email déjà utilisé)"
            ) from e
        except DatabaseError:
            self.conn.rollback()
            raise

    def delete(self, user_id: int) -> bool:
        """Supprime un utilisateur par id. Retourne True si réussi."""
        query = "DELETE FROM users WHERE id=%s;"
        with self.conn.cursor() as cursor:
            cursor.execute(query, (user_id,))
            self.conn.commit()
            return cursor.rowcount > 0

    def get_user_by_email(self, email: str) -> User:
        """Lit un utilisateur par email. Retourne None si non trouvé."""
        query = "SELECT * FROM users WHERE mail=%s;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (email,))
            row = cursor.fetchone()
            if row is None:
                return None
            return User(
                id=row["id"],
                username=row["username"],
                nom=row["nom"],
                prenom=row["prenom"],
                mail=row["mail"],
                password_hash=row["password_hash"],
                salt=row["salt"],
                sign_in_date=row["sign_in_date"],
                last_login=row["last_login"],
                status=row["status"],
                setting_param=row["setting_param"],
            )

    def get_user_by_username(self, username: str) -> User:
        """Lit un utilisateur par nom d'utilisateur. Retourne None si non trouvé."""
        query = "SELECT * FROM users WHERE username=%s;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (username,))
            row = cursor.fetchone()
            if row is None:
                return None
            return User(
                id=row["id"],
                username=row["username"],
                nom=row["nom"],
                prenom=row["prenom"],
                mail=row["mail"],
                password_hash=row["password_hash"],
                salt=row["salt"],
                sign_in_date=row["sign_in_date"],
                last_login=row["last_login"],
                status=row["status"],
                setting_param=row["setting_param"],
            )'''


# ajustement : qu'est ce que c'est ?
# reponses : Les index sont des structures de données qui améliorent la vitesse des opérations de recherche dans une base de données. Ils fonctionnent comme des tables de matières, permettant à la base de données de trouver rapidement les lignes correspondantes sans avoir à parcourir chaque ligne de la table.
# CREATE INDEX users_mail_idx ON users(mail);
# CREATE INDEX users_username_idx ON users(username);
