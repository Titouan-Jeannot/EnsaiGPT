

from cli.ui import QuitCommand
from cli.pages.home import page_home

def main() -> None:
    try:
        while True:
            page_home()
    except QuitCommand:
        print("A bientot.")


if __name__ == "__main__":
    main()
