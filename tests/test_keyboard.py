"""Test keyboard controller functionality."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.keyboard_controller import KeyboardController
import time

def main() -> None:
    print("Testing Keyboard Controller")
    print("=" * 50)
    print("✓ Using 'keyboard' library (raw key presses)")
    print()
    print("Test will start in 3 seconds...")
    print("Please switch to a text editor (like Notepad) to see the output")
    time.sleep(3)

    controller = KeyboardController()

    print("\nTesting single key press...")
    controller.tap_key('a')
    time.sleep(0.5)

    print("Testing chord (multiple keys)...")
    controller.press_keys_simultaneously(['b', 'c', 'd'])
    time.sleep(0.5)

    print("Testing arpeggio...")
    controller.press_keys_arpeggio(['e', 'f', 'g'], 0.1)
    time.sleep(0.5)

    print("\nTest complete!")
    print("You should see: a bcd efg in your text editor")

if __name__ == '__main__':
    main()
