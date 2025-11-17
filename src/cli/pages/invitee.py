# src/cli/pages/invitee.py

from cli.ui import QuitCommand, BackCommand, ask_nonempty
from cli.context import llm_service

import questionary
from questionary import Choice, Separator


def page_invitee() -> None:
    """
    Menu du mode invité avec un select (flèches + Entrée).
    """
    while True:
        action = questionary.select(
            "\n=== Mode invité ===\nCertaines actions exigent un compte utilisateur.",
            choices=[
                Choice("💬 Envoyer une requête (sans historique)", "send_request"),
                Separator(),
                Choice("⬅️ Retour accueil", "back_home"),
                Choice("❌ Quitter", "quit"),
            ],
        ).ask()

        if action is None:
            # On considère un Ctrl+C comme un retour à l'accueil
            return

        if action == "send_request":
            page_send_request_invitee()

        elif action == "back_home":
            # import LOCAL pour éviter l'import circulaire
            from cli.pages.home import page_home
            page_home()
            # on revient ensuite dans le menu invité quand page_home() se termine

        elif action == "quit":
            raise QuitCommand()


def page_send_request_invitee() -> None:
    print("\n=== Envoyer une requête en mode invité ===")
    try:
        prompt = ask_nonempty("Votre requête : ")
        print(f"Prompt reçu : {prompt}")
    except BackCommand:
        return

    try:
        response = llm_service.requete_invitee(prompt=prompt)
    except Exception as e:
        print(f"❌ Erreur lors de la génération de la réponse : {e}")
        return

    # On affiche simplement la réponse puis on revient au menu invité
    print(f"\n🤖 Réponse : {response['content']}")
