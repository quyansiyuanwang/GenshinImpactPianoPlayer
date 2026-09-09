"""Keyboard controller for simulating key presses."""

import time
import keyboard
from typing import List
from src.ui.cli.input.injection_state import mark_injected


class KeyboardController:
    """Controls keyboard input simulation.

    Uses 'keyboard' library for raw key event simulation.
    Note: Requires administrator/root privileges to function properly.
    """

    def __init__(self) -> None:
        """Initialize keyboard controller."""
        pass

    def press_key(self, key: str) -> None:
        """Press a single key.

        Args:
            key: Key to press
        """
        with mark_injected(keyboard.key_to_scan_codes(key.lower(), error_if_missing=False)):
            keyboard.press(key.lower())

    def release_key(self, key: str) -> None:
        """Release a single key.

        Args:
            key: Key to release
        """
        with mark_injected(keyboard.key_to_scan_codes(key.lower(), error_if_missing=False)):
            keyboard.release(key.lower())

    def tap_key(self, key: str) -> None:
        """Press and immediately release a key.

        Args:
            key: Key to tap
        """
        with mark_injected(keyboard.key_to_scan_codes(key.lower(), error_if_missing=False)):
            keyboard.press_and_release(key.lower())

    def press_keys_simultaneously(self, keys: List[str]) -> None:
        """Press multiple keys at the same time (chord).

        Args:
            keys: List of keys to press simultaneously
        """
        # Press all keys
        scan_codes = [
            code
            for key in keys
            for code in keyboard.key_to_scan_codes(key.lower(), error_if_missing=False)
        ]
        with mark_injected(scan_codes):
            for key in keys:
                keyboard.press(key.lower())
            time.sleep(0.005)
            for key in keys:
                keyboard.release(key.lower())

    def press_keys_arpeggio(self, keys: List[str], interval: float) -> None:
        """Press keys in rapid succession (arpeggio).

        Args:
            keys: List of keys to press in sequence
            interval: Time interval between key presses (seconds)
        """
        for key in keys:
            self.tap_key(key)
            time.sleep(interval)

    def release_all(self, keys: List[str]) -> None:
        """Release multiple keys.

        Args:
            keys: List of keys to release
        """
        for key in keys:
            self.release_key(key)

    def press_scan_code(self, scan_code: int) -> None:
        with mark_injected([scan_code]):
            keyboard.press(scan_code)

    def release_scan_code(self, scan_code: int) -> None:
        with mark_injected([scan_code]):
            keyboard.release(scan_code)

    def tap_scan_code(self, scan_code: int) -> None:
        with mark_injected([scan_code]):
            keyboard.press_and_release(scan_code)

    def press_scan_codes_simultaneously(self, scan_codes: List[int]) -> None:
        with mark_injected(scan_codes):
            for scan_code in scan_codes:
                keyboard.press(scan_code)
            time.sleep(0.005)
            for scan_code in scan_codes:
                keyboard.release(scan_code)
