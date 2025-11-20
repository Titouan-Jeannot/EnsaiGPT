from cli.ui import QuitCommand
from cli.pages.home import page_home


def main() -> None:
    """Point d'entrée principal de l'application."""
    try:
        while True:
            page_home()
    except QuitCommand:
        print("A bientot.")


if __name__ == "__main__":
    main()
