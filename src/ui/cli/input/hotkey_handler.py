"""Global hotkey handler with scan-code support for symbol keys."""

from collections.abc import Callable
from typing import TYPE_CHECKING

import keyboard

if TYPE_CHECKING:
    from keyboard import KeyboardEvent


SCAN_CODES = {
    "=": 13,
    "-": 12,
    "[": 26,
    "]": 27,
    ",": 51,
    ".": 52,
}


class HotkeyHandler:
    """Dispatch registered key combinations from one owned keyboard hook."""

    def __init__(self) -> None:
        self._hotkeys: dict[str, Callable[[], None]] = {}
        self._scan_code_hotkeys: dict[int, Callable[[], None]] = {}
        self._modifier_state = {"shift": False, "ctrl": False, "alt": False}
        self._hooked = False

    def register(self, key: str, callback: Callable[[], None]) -> None:
        """Register a binding, selecting a scan code for physical symbol keys."""
        normalized = key.lower()
        if normalized in SCAN_CODES:
            self.register_by_scan_code(SCAN_CODES[normalized], callback)
        else:
            self.register_by_name(normalized, callback)

    def register_by_name(self, key_name: str, callback: Callable[[], None]) -> None:
        """Register a named key or modifier combination."""
        self._hotkeys[key_name.lower()] = callback

    def register_by_scan_code(
        self, scan_code: int, callback: Callable[[], None]
    ) -> None:
        """Register a physical scan-code binding."""
        self._scan_code_hotkeys[scan_code] = callback

    def _on_key_event(self, event: "KeyboardEvent") -> None:
        """Track modifier state and dispatch key-down callbacks."""
        name = event.name.lower()
        modifier = self._modifier_name(name)
        if event.event_type == "up":
            if modifier:
                self._modifier_state[modifier] = False
            return
        if event.event_type != "down":
            return
        if modifier:
            self._modifier_state[modifier] = True
            return

        if not any(self._modifier_state.values()):
            callback = self._scan_code_hotkeys.get(event.scan_code)
            if callback:
                callback()
                return

        key_name = self._qualified_name(name)
        callback = self._hotkeys.get(key_name)
        if callback:
            callback()

    @staticmethod
    def _modifier_name(name: str) -> str | None:
        """Normalize left/right modifier key names."""
        if name in {"shift", "left shift", "right shift"}:
            return "shift"
        if name in {"ctrl", "left ctrl", "right ctrl"}:
            return "ctrl"
        if name in {"alt", "left alt", "right alt"}:
            return "alt"
        return None

    def _qualified_name(self, name: str) -> str:
        """Return the registered representation of a key combination."""
        if name == "+":
            name = "="
        for modifier in ("ctrl", "shift", "alt"):
            if self._modifier_state[modifier]:
                return f"{modifier}+{name}"
        return name

    def start(self) -> None:
        """Start the process-wide hook once."""
        if not self._hooked:
            keyboard.hook(self._on_key_event)
            self._hooked = True

    def stop(self) -> None:
        """Remove only the hook owned by this handler."""
        if self._hooked:
            keyboard.unhook(self._on_key_event)
            self._hooked = False
