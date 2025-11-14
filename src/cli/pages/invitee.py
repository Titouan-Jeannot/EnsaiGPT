# src/cli/pages/invitee.py

from cli.ui import QuitCommand, ask_int, BackCommand, ask_nonempty
# adapte le chemin suivant à ton projet si besoin :
# from cli.Service.LLMService import llm_service
# ou : from Service.LLMService import llm_service
# (je laisse le nom llm_service tel que tu l'utilises plus bas)
from cli.context import llm_service

def page_invitee() -> None:
    print("\n=== Mode invite ===")
    print("Certaines actions exigent un compte utilisateur.")
    print("1) Envoyer un requete (sans historique)")
    print("9) Retour accueil")
    print("0) Quitter")
    try:
        choice = ask_int("Votre choix", [1, 9, 0])
    except BackCommand:
        return

    if choice == 1:
        page_send_request_invitee()
    elif choice == 9:
        # import LOCAL pour éviter l'import circulaire
        from cli.pages.home import page_home
        page_home()
    elif choice == 0:
        raise QuitCommand()


def page_send_request_invitee() -> None:
    print("\n=== Envoyer une requete en mode invite ===")
    try:
        prompt = ask_nonempty("Votre requete : ")
        print(f"Prompt recu: {prompt}")
    except BackCommand:
        return

    try:
        response = llm_service.requete_invitee(prompt=prompt)
    except Exception as e:
        print(f"Erreur lors de la generation de la reponse: {e}")
        return

    print(f"Réponse: {response['content']}")
    page_invitee()
