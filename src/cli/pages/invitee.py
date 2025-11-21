# src/cli/pages/invitee.py

from cli.ui import (
    QuitCommand,
    BackCommand,
    ask_nonempty,
    ask_menu,
)
from cli.context import llm_service


def _go_home() -> None:
    """Retour à l'accueil (import local pour éviter les cycles)."""
    from cli.pages.home import page_home
    page_home()


def page_invitee(header: str | None = None) -> None:
    """Page du mode invité."""
    while True:
        try:
            choix = ask_menu(
                title="Mode invité",
                subtitle="Certaines actions exigent un compte utilisateur.",
                options=[
                    ("Envoyer une requête (sans historique)", "send"),
                    ("Retour accueil", "home"),
                    ("Quitter l'application", "quit"),
                ],
                clear_screen=True,
                header=header,  # ➜ ici on affiche la question/réponse si fournie
            )
        except BackCommand:
            # On revient simplement au menu appelant
            return

        if choix == "send":
            # Après une nouvelle requête, on remplacera le header
            header = page_send_request_invitee()
        elif choix == "home":
            _go_home()
            return
        elif choix == "quit":
            raise QuitCommand()


def page_send_request_invitee() -> str | None:
    """Envoyer une requête en mode invité.

    Retourne une chaîne 'header' à afficher dans le prochain écran de menu,
    ou None en cas d'annulation.
    """
    print("\n=== Envoyer une requête en mode invité ===")
    try:
        prompt = ask_nonempty("Votre requête : ")
    except BackCommand:
        return None

    try:
        response = llm_service.requete_invitee(prompt=prompt)
    except Exception as e:
        print(f"Erreur lors de la génération de la réponse: {e}")
        return None

    content = response.get("content", response)

    # On construit un petit résumé compact à ré-afficher en haut du prochain menu
    header = (
        "Dernière interaction (mode invité)\n"
        "-------------------------------\n"
        f"Vous : {prompt}\n\n"
        f"Réponse :\n{content}\n"
    )

    print("\n--- Réponse ---")
    print(content)

    # On retourne le header au caller, qui le passera à page_invitee()
    return header
