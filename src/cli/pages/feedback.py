# src/cli/pages/feedback.py

from datetime import datetime
from typing import List

from src.ObjetMetier.Feedback import Feedback
from src.cli.ui import ask_yes_no, ask_optional, BackCommand, session
from src.cli.context import feedback_dao  # pour l'instant, DAO direct


def build_feedback_object(
    user_id: int, message_id: int, is_like: bool, comment: str
) -> Feedback:
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
        return Feedback(
            id_feedback=0,
            id_user=user_id,
            id_message=message_id,
            is_like=is_like,
            comment=comment,
            created_at=created_at,
        )


def add_feedback_flow(conv_id: int, messages: List) -> None:
    agent_messages = [msg for msg in messages if getattr(msg, "is_from_agent", False)]
    if not agent_messages:
        print("Aucun message agent disponible pour feedback.")
        return
    default = agent_messages[0]
    print(f"Message agent par defaut: ID {default.id_message} -> {default.message}")
    try:
        use_default = ask_yes_no("Utiliser ce message ?")
    except BackCommand:
        return
    if use_default:
        target_id = default.id_message
    else:
        ids = [msg.id_message for msg in agent_messages]
        from src.cli.ui import ask_int
        try:
            target_id = ask_int("Choisir ID du message agent", ids)
        except BackCommand:
            return
    try:
        liked = ask_yes_no("Like ?")
        comment = ask_optional("Commentaire (optionnel)") or ""
    except BackCommand:
        return
    feedback_obj = build_feedback_object(
        user_id=session.current_user_id,
        message_id=target_id,
        is_like=liked,
        comment=comment,
    )
    try:
        result = feedback_dao.create(feedback_obj)
    except Exception as exc:
        print(f"Echec d'enregistrement du feedback: {exc}")
        return
    print(f"Feedback enregistre avec l'id {result.id_feedback}.")
