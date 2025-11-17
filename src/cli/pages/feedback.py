# src/cli/pages/feedback.py

from datetime import datetime
from typing import List

from ObjetMetier.Feedback import Feedback
from cli.ui import ask_yes_no, ask_optional, BackCommand, session
from cli.context import feedback_dao  # pour l'instant, DAO direct

import questionary
from questionary import Choice, Separator


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
        # fallback si le constructeur n'accepte pas None
        return Feedback(
            id_feedback=0,
            id_user=user_id,
            id_message=message_id,
            is_like=is_like,
            comment=comment,
            created_at=created_at,
        )


def add_feedback_flow(conv_id: int, messages: List) -> None:
    # On filtre seulement les messages de l'agent
    agent_messages = [msg for msg in messages if getattr(msg, "is_from_agent", False)]
    if not agent_messages:
        print("Aucun message agent disponible pour feedback.")
        return

    default = agent_messages[0]
    print(
        f"Message agent par défaut : ID {default.id_message} -> "
        f"{_preview_message(default.message)}"
    )

    try:
        use_default = ask_yes_no("Utiliser ce message ?")
    except BackCommand:
        return

    # Choix du message cible
    if use_default:
        target_id = default.id_message
    else:
        # Menu déroulant pour choisir le message agent
        choices = []
        for msg in agent_messages:
            label = f"[{msg.id_message}] {_preview_message(msg.message)}"
            choices.append(Choice(label, msg.id_message))

        choices.append(Separator())
        choices.append(Choice("❌ Annuler", "cancel"))

        selection = questionary.select(
            "Choisir le message agent pour le feedback :",
            choices=choices,
        ).ask()

        if selection is None or selection == "cancel":
            return

        target_id = selection

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
        result = feedback_dao.create(feedback_obj)
    except Exception as exc:
        print(f"Échec d'enregistrement du feedback : {exc}")
        return

    print(f"✅ Feedback enregistré avec l'id {result.id_feedback}.")


def _preview_message(content: str, max_len: int = 60) -> str:
    """
    Retourne un petit aperçu du message pour l'affichage dans les menus.
    """
    if not isinstance(content, str):
        return str(content)
    content = content.replace("\n", " ").strip()
    return content if len(content) <= max_len else content[: max_len - 3] + "..."
