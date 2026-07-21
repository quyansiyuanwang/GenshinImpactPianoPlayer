"""GIPianoPlayer - A Python piano playing script.

This program reads a specially formatted text file and simulates keyboard
input to "play" the piano in games or applications.
"""

import argparse
import sys
import ctypes
from pathlib import Path


def is_admin() -> bool:
    """Check if the program is running with administrator privileges.

    Returns:
        True if running as admin, False otherwise
    """
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def get_log_directory() -> str:
    """Get the directory where log files will be saved.

    Returns:
        Path to log directory
    """
    if getattr(sys, "frozen", False):
        # Running as packaged exe
        exe_dir = Path(sys.executable).parent
        # Test if we can write to exe directory
        try:
            test_file = exe_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
            return str(exe_dir)
        except (PermissionError, OSError):
            # Can't write to exe directory, use temp directory
            import tempfile

            temp_dir = Path(tempfile.gettempdir()) / "GIPianoPlayer"
            temp_dir.mkdir(exist_ok=True)
            return str(temp_dir)
    else:
        # Running in development
        return str(Path.cwd())


def main() -> None:
    """Main entry point for GIPianoPlayer."""
    parser = argparse.ArgumentParser(
        description="GIPianoPlayer - Automated piano playing script"
    )
    parser.add_argument("file", help="Path to the score text file")

    args = parser.parse_args()

    # Show log directory
    log_dir = get_log_directory()
    print("=" * 70)
    print("GIPianoPlayer")
    print("=" * 70)
    print(f"Log files will be saved to: {log_dir}")
    print("  - hotkey_errors.log: Hotkey registration log")
    print("  - hotkey_debug.log: Hotkey trigger log")
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
