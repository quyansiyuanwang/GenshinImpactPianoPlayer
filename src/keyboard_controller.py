"""Keyboard controller for simulating key presses."""

import time
import keyboard
from typing import List


class KeyboardController:
    """Controls keyboard input simulation.

    Uses 'keyboard' library for raw key event simulation.
    Note: Requires administrator/root privileges to function properly.
    """

    def __init__(self) -> None:
        """Initialize keyboard controller."""
        pass

    def press_key(self, key: str) -> None:
        """Press a single key."""
        keyboard.press(key.lower())

    def release_key(self, key: str) -> None:
        """Release a single key."""
        keyboard.release(key.lower())

    def tap_key(self, key: str) -> None:
        """Press and immediately release a key."""
        keyboard.press_and_release(key.lower())

    def press_keys_simultaneously(self, keys: List[str]) -> None:
        """Press multiple keys at the same time (chord)."""
        # Press all keys
        for key in keys:
            keyboard.press(key.lower())

        # Minimal delay to ensure all keys are registered
        time.sleep(0.005)

        # Release all keys
        for key in keys:
            keyboard.release(key.lower())

    def press_keys_arpeggio(self, keys: List[str], interval: float) -> None:
        """Press keys in rapid succession (arpeggio)."""
        for key in keys:
            self.tap_key(key)
            time.sleep(interval)
