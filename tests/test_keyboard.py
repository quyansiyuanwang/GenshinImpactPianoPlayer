"""Test keyboard controller functionality."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.keyboard_controller import KeyboardController
import time

def main():
    print("Testing Keyboard Controller")
    print("=" * 50)

    controller = KeyboardController()

    if controller.use_keyboard:
        print("✓ Using 'keyboard' library (raw key presses)")
    else:
        print("⚠ Using 'pynput' library (text input only)")
        print("  Install 'keyboard' for game input support")

    print()
    print("Test will start in 3 seconds...")
    print("Please switch to a text editor (like Notepad) to see the output")
    time.sleep(3)

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
