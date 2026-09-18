import argparse

from . import __version__


def main():
    parser = argparse.ArgumentParser(description="AstroCalc interactive terminal astronomy")
    parser.add_argument("--version", action="version", version=f"astrocalc {__version__}")
    parser.parse_args()
    from .ui import AstroApp
    AstroApp().run()


if __name__ == "__main__":
    main()
