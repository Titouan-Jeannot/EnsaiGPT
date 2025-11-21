# src/cli/pages/feedback.py

from datetime import datetime
from typing import List, Optional, Tuple

from ObjetMetier.Feedback import Feedback
from cli.ui import ask_yes_no, ask_optional, BackCommand, session
from cli.context import feedback_dao  # pour l'instant, DAO direct


def build_feedback_object(
    user_id: int, message_id: int, is_like: bool, comment: str
) -> Feedback:
    """Construire un objet Feedback à partir des entrées utilisateur."""
    created_at = datetime.now()
    try:
        return Feedback(
            id_feedback=None,
            id_user=user_id,
            id_message=message_id,
            is_like=is_like,
            comment=comment,
            created_at=created_at,
        )
    except Exception:
        # fallback en cas de problème de constructeur
        return Feedback(
            id_feedback=123,
            id_user=user_id,
            id_message=message_id,
            is_like=is_like,
            comment=comment,
            created_at=created_at,
        )


def add_feedback_flow(conv_id: int, messages: List) -> Tuple[bool, Optional[str]]:
    """
    Flux pour ajouter un feedback sur un message agent.

    Retourne (success, message_notification).
    """
    agent_messages = [msg for msg in messages if getattr(msg, "is_from_agent", False)]
    if not agent_messages:
        msg = "Aucun message agent disponible pour feedback."
        print(msg)
        return False, msg

    default = agent_messages[0]
    print(f"Message agent par défaut: ID {default.id_message} -> {default.message}")

    try:
        use_default = ask_yes_no("Utiliser ce message ?")
    except BackCommand:
        return False, None

    if use_default:
        target_id = default.id_message
    else:
        ids = [msg.id_message for msg in agent_messages]
        from cli.ui import ask_int
        try:
            target_id = ask_int("Choisir ID du message agent", ids)
        except BackCommand:
            return False, None

    try:
        liked = ask_yes_no("Like ?")
        comment = ask_optional("Commentaire (optionnel)") or ""
    except BackCommand:
        return False, None

    feedback_obj = build_feedback_object(
        user_id=session.current_user_id,
        message_id=target_id,
        is_like=liked,
        comment=comment,
    )

    try:
        result = feedback_dao.create(feedback_obj)
    except Exception as exc:
        msg = f"Echec d'enregistrement du feedback: {exc}"
        print(msg)
        return False, msg

    msg = "Feedback enregistré avec succès."
    print(msg)
    return True, msg
