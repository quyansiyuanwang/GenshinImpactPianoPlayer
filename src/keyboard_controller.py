"""Keyboard controller for simulating key presses."""

import time
from typing import List

try:
    import keyboard
    USE_KEYBOARD = True
except ImportError:
    from pynput.keyboard import Controller
    USE_KEYBOARD = False


class KeyboardController:
    """Controls keyboard input simulation.

    Prefers 'keyboard' library for game input simulation (raw key presses).
    Falls back to 'pynput' for text input if 'keyboard' is not available.
    """

    def __init__(self) -> None:
        if USE_KEYBOARD:
            # keyboard library is available - better for game input
            self.use_keyboard = True
        else:
            # Fall back to pynput
            self.use_keyboard = False
            self.controller = Controller()

    def press_key(self, key: str) -> None:
        """Press a single key."""
        if self.use_keyboard:
            keyboard.press(key.lower())
        else:
            # pynput accepts single character strings
            self.controller.press(key.lower())

    def release_key(self, key: str) -> None:
        """Release a single key."""
        if self.use_keyboard:
            keyboard.release(key.lower())
        else:
            # pynput accepts single character strings
            self.controller.release(key.lower())

    def tap_key(self, key: str) -> None:
        """Press and immediately release a key."""
        if self.use_keyboard:
            keyboard.press_and_release(key.lower())
        else:
            # pynput accepts single character strings
            self.controller.press(key.lower())
            self.controller.release(key.lower())

    def press_keys_simultaneously(self, keys: List[str]) -> None:
        """Press multiple keys at the same time (chord)."""
        if self.use_keyboard:
            # Press all keys
            for key in keys:
                keyboard.press(key.lower())

            # Minimal delay to ensure all keys are registered
            time.sleep(0.005)  # Reduced from 0.01 to 0.005

            # Release all keys
            for key in keys:
                keyboard.release(key.lower())
        else:
            # Press all keys
            for key in keys:
                self.controller.press(key.lower())

            # Minimal delay to ensure all keys are registered
            time.sleep(0.005)

            # Release all keys
            for key in keys:
                self.controller.release(key.lower())

    def press_keys_arpeggio(self, keys: List[str], interval: float) -> None:
        """Press keys in rapid succession (arpeggio)."""
        for key in keys:
            self.tap_key(key)
            time.sleep(interval)

