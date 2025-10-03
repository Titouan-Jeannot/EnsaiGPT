from pydantic import BaseModel
from datetime import datetime as timestamp


class User(BaseModel):
    id: int
    username: str
    nom: str
    prenom: str
    mail: str
    password_hash: str
    salt: str
    sign_in_date: timestamp = None
    last_login: timestamp = None
    status: str  # enum = "active"  # active, inactive, banned
    setting_param: str

    def __init__(self, id, username, nom, prenom, mail, password_hash, salt, sign_in_date=None, last_login=None, status="active", setting_param="Tu es un assistant utile."):
        """
        Initialisation de la classe User.
        """
        if not isinstance(id, int):
            raise ValueError("id must be an integer")
        if not isinstance(username, str):
            raise ValueError("username must be a string")
        if not isinstance(nom, str):
            raise ValueError("nom must be a string")
        if not isinstance(prenom, str):
            raise ValueError("prenom must be a string")
        if not isinstance(mail, str):
            raise ValueError("mail must be a string")
        if not isinstance(password_hash, str):
            raise ValueError("password_hash must be a string")
        if not isinstance(salt, str):
            raise ValueError("salt must be a string")
        if sign_in_date is not None and not isinstance(sign_in_date, timestamp):
            raise ValueError("sign_in_date must be a timestamp or None")
        if last_login is not None and not isinstance(last_login, timestamp):
            raise ValueError("last_login must be a timestamp or None")
        if not isinstance(status, str):
            raise ValueError("status must be a string")
        if not isinstance(setting_param, str):
            raise ValueError("setting_param must be a string")

        self.id = id
        self.username = username
        self.nom = nom
        self.prenom = prenom
        self.mail = mail
        self.password_hash = password_hash
        self.salt = salt
        self.sign_in_date = sign_in_date
        self.last_login = last_login
        self.status = status
        self.setting_param = setting_param
