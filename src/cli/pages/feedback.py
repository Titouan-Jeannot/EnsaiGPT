# src/cli/pages/feedback.py

from datetime import datetime
from typing import List

from ObjetMetier.Feedback import Feedback
from cli.ui import (
    ask_yes_no,
    ask_optional,
    ask_menu,
    BackCommand,
    session,
)
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
        # Fallback très défensif si le constructeur exige un id non None
        return Feedback(
            id_feedback=123,
            id_user=user_id,
            id_message=message_id,
            is_like=is_like,
            comment=comment,
            created_at=created_at,
        )


def add_feedback_flow(conv_id: int, messages: List) -> None:
    """Flux pour ajouter un feedback sur un message agent."""
    agent_messages = [msg for msg in messages if getattr(msg, "is_from_agent", False)]
    if not agent_messages:
        print("Aucun message agent disponible pour feedback.")
        return

    # Message par défaut = dernier message agent
    default = agent_messages[0]
    print(f"Message agent par défaut: ID {default.id_message} -> {default.message}")
    try:
        use_default = ask_yes_no("Utiliser ce message ?")
    except BackCommand:
        return

    if use_default:
        target_id = default.id_message
    else:
        # On propose un petit menu déroulant pour choisir le message agent
        options = []
        for msg in agent_messages:
            label = f"ID {msg.id_message} – {msg.message[:60]}"
            options.append((label, str(msg.id_message)))
        options.append(("Annuler", "cancel"))

        try:
            choix = ask_menu(
                title="Choisir un message agent",
                subtitle="Sélectionnez le message sur lequel donner un feedback",
                options=options,
            )
        except BackCommand:
            return

        if choix == "cancel":
            return

        try:
            target_id = int(choix)
        except ValueError:
            print("Choix invalide.")
            return

    # Like / dislike + commentaire
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
        _ = feedback_dao.create(feedback_obj)
    except Exception as exc:
        print(f"Echec d'enregistrement du feedback: {exc}")
        return

    print("Feedback enregistré avec succès.")
