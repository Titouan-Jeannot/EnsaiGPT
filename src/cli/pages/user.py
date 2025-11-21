# src/cli/pages/user.py

from cli.ui import (
    session,
    ask_optional,
    ask_yes_no,
    ask_nonempty,
    ask_menu,
    BackCommand,
    QuitCommand,
    reset_session,
    ensure_logged_in,
)
from cli.context import user_service, stats_service

# pour l'analyse statique éventuelle
stats_service = stats_service


# ---------------------------------------------------------------------------
# Helpers de navigation (imports locaux pour éviter les cycles)
# ---------------------------------------------------------------------------

def _go_conversations_manage() -> None:
    from cli.pages.conversations import page_manage
    page_manage()


def _go_conversations_new() -> None:
    from cli.pages.conversations import create_conversation
    create_conversation()


def _go_join_collab() -> None:
    from cli.pages.collaboration import page_join_collab
    page_join_collab()


def _go_home() -> None:
    from cli.pages.home import page_home
    page_home()


# ---------------------------------------------------------------------------
# Espace utilisateur
# ---------------------------------------------------------------------------

def page_user_home() -> None:
    """Page principale de l'utilisateur connecté."""
    if not ensure_logged_in():
        return

    while True:
        try:
            choix = ask_menu(
                title="Espace utilisateur",
                subtitle=f"Connecté en tant que {session.current_username}",
                options=[
                    ("Mon compte", "account"),
                    ("Gestion des conversations", "conversations"),
                    ("Nouvelle conversation", "new_conv"),
                    ("Rejoindre une collaboration", "join_collab"),
                    ("Déconnexion", "logout"),
                    ("Quitter l'application", "quit"),
                ],
            )
        except BackCommand:
            # Si on est déjà au “haut” de la navigation, on ignore /back
            return

        if choix == "account":
            page_account()

        elif choix == "conversations":
            _go_conversations_manage()

        elif choix == "new_conv":
            _go_conversations_new()

        elif choix == "join_collab":
            _go_join_collab()

        elif choix == "logout":
            print("Déconnexion effectuée.")
            reset_session()
            return

        elif choix == "quit":
            raise QuitCommand()


# ---------------------------------------------------------------------------
# Gestion du compte
# ---------------------------------------------------------------------------

def page_account() -> None:
    """Page de gestion du compte utilisateur."""
    if not ensure_logged_in():
        return

    while True:
        try:
            user = user_service.get_user_by_id(session.current_user_id)
        except Exception as exc:
            print(f"Impossible de charger le compte: {exc}")
            return

        if not user:
            print("Utilisateur introuvable.")
            reset_session()
            return

        print("\n=== Mon compte ===")
        print(f"ID       : {user.id}")
        print(f"Email    : {user.mail}")
        print(f"Nom      : {user.nom}")
        print(f"Prénom   : {user.prenom}")
        print(f"Pseudo   : {user.username}")
        print(f"Statut   : {user.status}")
        print(f"Paramètre assistant : {user.setting_param}")

        stats = _get_user_stats(user.id)
        if stats:
            print("\n--- Statistiques ---")
            try:
                print(f"Conversations actives: {stats_service.nb_conv(user.id)}")
            except Exception:
                pass
            try:
                print(f"Messages envoyés     : {stats_service.nb_messages(user.id)}")
            except Exception:
                pass
            if "temps_passe" in stats:
                print(f"Temps passé          : {stats['temps_passe']}")
            print("---------------------")

        try:
            choix = ask_menu(
                title="Mon compte",
                subtitle=None,
                options=[
                    ("Modifier mes informations", "edit"),
                    ("Supprimer mon compte", "delete"),
                    ("Retour", "back"),
                    ("Quitter l'application", "quit"),
                ],
            )
        except BackCommand:
            return

        if choix == "edit":
            update_account(user.id)

        elif choix == "delete":
            if ask_yes_no("Confirmer la suppression du compte ?"):
                try:
                    user_service.delete_user(user.id)
                except Exception as exc:
                    print(f"Echec de suppression: {exc}")
                else:
                    print("Compte supprimé. Retour à l'accueil.")
                    reset_session()
                    _go_home()
                    return

        elif choix == "back":
            return

        elif choix == "quit":
            raise QuitCommand()


def update_account(user_id: int) -> None:
    """Mettre à jour les informations du compte utilisateur."""
    print("\n--- Modification du profil ---")
    print("Laisser vide pour conserver la valeur actuelle.")

    mail = None
    password = None

    try:
        username = ask_optional("Nouveau pseudo")
        nom = ask_optional("Nouveau nom")
        prenom = ask_optional("Nouveau prénom")
        setting_param = ask_optional("Nouveau paramètre assistant")

        change_mail = ask_yes_no("Modifier l'email ?")
        if change_mail:
            mail = ask_nonempty("Nouvel email")

        change_password = ask_yes_no("Modifier le mot de passe ?")
        if change_password:
            password = ask_nonempty("Nouveau mot de passe")
    except BackCommand:
        return

    try:
        user_service.update_user(
            user_id=user_id,
            mail=mail,
            username=username,
            nom=nom,
            prenom=prenom,
            setting_param=setting_param,
            password_plain=password,
        )
    except Exception as exc:
        print(f"Echec de mise à jour: {exc}")
        return

    print("Profil mis à jour.")


# ---------------------------------------------------------------------------
# Statistiques utilisateur
# ---------------------------------------------------------------------------

def _get_user_stats(user_id: int) -> dict:
    """Récupérer les statistiques de l'utilisateur."""
    stats = {}
    try:
        stats["nb_conv"] = stats_service.nb_conv(user_id)
    except Exception:
        pass
    try:
        stats["nb_messages"] = stats_service.nb_messages(user_id)
    except Exception:
        pass
    try:
        delta = stats_service.temps_passe(user_id, simple_window=True)
        if delta:
            stats["temps_passe"] = _format_duration(delta)
    except Exception:
        pass
    return stats


def _format_duration(delta) -> str:
    """Formater une durée en une chaîne lisible."""
    try:
        total_seconds = int(delta.total_seconds())
    except Exception:
        return "0s"
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)
