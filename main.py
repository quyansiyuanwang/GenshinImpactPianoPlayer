"""GIPianoPlayer - A Python piano playing script.

This program reads a specially formatted text file and simulates keyboard
input to "play" the piano in games or applications.
"""

import argparse
from src.cli import CLI


def main() -> None:
    """Main entry point for GIPianoPlayer."""
    parser = argparse.ArgumentParser(description="GIPianoPlayer - Automated piano playing script")
    parser.add_argument("file", help="Path to the score text file")

    args = parser.parse_args()

    cli = CLI(args.file)
    cli.run()


if __name__ == "__main__":
    main()
