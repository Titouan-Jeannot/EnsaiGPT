from datetime import datetime

class Feedback :

    def __init__(self, id_feedback, id_user, id_message, is_like, comment, create_at):
        """
        Constructeur de la classe Feedback.

        Paramètres:
        -----------
        - id_feedback : identifiant unique du feedback
        - id_user : identifiant de l'utilisateur
        - id_message : identifiant du message
        - is_like : booléen indiquant si le feedback est un like (True) ou un dislike (False)
        - comment : commentaire associé au feedback
        - create_at : date et heure de création du feedback

        Raises:
        -----------
        - ValueError : si un des paramètres est None
        """
        if id_feedback is None or not isinstance(id_feedback, int):
            raise ValueError("id_feedback must be a non-null integer")
        if id_user is None or not isinstance(id_user, int):
            raise ValueError("id_user must be a non-null integer")
        if id_message is None or not isinstance(id_message, int):
            raise ValueError("id_message must be a non-null integer")
        if is_like is None or not isinstance(is_like, bool):
            raise ValueError("is_like must be a non-null boolean")
        if comment is not None and not isinstance(comment, str):
            raise ValueError("comment must be a string or None")
        if create_at is None or not isinstance(create_at, datetime):
            raise ValueError("create_at must be a non-null datetime")

        self.id_feedback = id_feedback
        self.id_user = id_user
        self.id_message = id_message
        self.is_like = is_like
        self.comment = comment
        self.create_at = create_at

    def __eq__(self, other):
        if not isinstance(other, Feedback):
            return False
        return (self.id_feedback == other.id_feedback and
                self.id_user == other.id_user and
                self.id_message == other.id_message and
                self.is_like == other.is_like and
                self.comment == other.comment and
                self.create_at == other.create_at)
