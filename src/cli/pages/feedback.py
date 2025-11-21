# src/cli/pages/feedback.py

from datetime import datetime
from typing import List

from ObjetMetier.Feedback import Feedback
from cli.ui import ask_yes_no, ask_optional, BackCommand, session
from cli.context import feedback_service  # utiliser le service FeedbackService


def add_feedback_flow(conv_id: int, messages: List) -> None:
    """Flux pour ajouter un feedback sur un message agent."""
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
        from cli.ui import ask_int
        try:
            target_id = ask_int("Choisir ID du message agent", ids)
        except BackCommand:
            return
    try:
        liked = ask_yes_no("Like ?")
        comment = ask_optional("Commentaire (optionnel)") or ""
    except BackCommand:
        return

    try:
        result = feedback_service.add_feedback(
            user_id=session.current_user_id,
            message_id=target_id,
            is_like=liked,
            comment=comment,
        )
    except Exception as exc:
        print(f"Echec d'enregistrement du feedback: {exc}")
        return
    print("Feedback enregistre avec succes.")
    # print(f"Feedback enregistre avec l'id {result.id_feedback}.")
