"""GIPianoPlayer - A Python piano playing script.

This program reads a specially formatted text file and simulates keyboard
input to "play" the piano in games or applications.
"""

import argparse
import sys
import ctypes


def is_admin() -> bool:
    """Check if the program is running with administrator privileges.

    Returns:
        True if running as admin, False otherwise
    """
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def main() -> None:
    """Main entry point for GIPianoPlayer."""
    parser = argparse.ArgumentParser(
        description="GIPianoPlayer - Automated piano playing script"
    )
    parser.add_argument("file", help="Path to the score text file")

    args = parser.parse_args()

    print("=" * 70)
    print("GIPianoPlayer")
    print("=" * 70)
    print()

    # Check for admin privileges and warn if not running as admin
    if not is_admin():
        print("=" * 70)
        print("WARNING: Not running with Administrator privileges!")
        print("=" * 70)
        print("Hotkeys (F8, +/-, etc.) may not work without admin privileges.")
        print("To enable hotkeys:")
        print("  1. Right-click on GIPianoPlayer.exe")
        print("  2. Select 'Run as administrator'")
        print()
        print("Press Enter to continue anyway, or Ctrl+C to exit...")
        print("=" * 70)
        try:
            input()
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

    from src.cli import CLI

    cli = CLI(args.file)
    cli.run()


if __name__ == "__main__":
    main()
