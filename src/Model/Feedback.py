from datetime import datetime

class Feedback (self, id_feedback, id_user, id_message, is_like, comment, create_at):

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
        self.id_feedback = id_feedback
        self.id_user = id_user
        self.id_message = id_message
        self.is_like = is_like
        self.comment = comment
        self.create_at = create_at
