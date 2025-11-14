# src/main.py

from cli.ui import QuitCommand
from cli import page_home  # récupéré via cli.__init__


def main() -> None:
    try:
        while True:
            page_home()
    except QuitCommand:
        print("A bientot.")


if __name__ == "__main__":
    main()
