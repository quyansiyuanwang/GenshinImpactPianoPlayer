"""Global hotkey handler with scan-code support for symbol keys."""

from collections.abc import Callable
from typing import TYPE_CHECKING

import keyboard
from src.application.events import InputEvent
from src.ui.cli.input.adapters import KeyboardInputAdapter

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
        self._locked = False
        self._unlock_binding = "f12"
        self._event_dispatcher: Callable[[InputEvent], object] | None = None
        self._input_adapter = KeyboardInputAdapter()

    def set_event_dispatcher(self, dispatcher: Callable[[InputEvent], object] | None) -> None:
        """Route normalized events to an application controller when configured."""
        self._event_dispatcher = dispatcher

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

    def set_locked(self, locked: bool, unlock_binding: str | None = None) -> None:
        """Ignore all registered callbacks while locked except the unlock key."""
        self._locked = bool(locked)
        if unlock_binding:
            self._unlock_binding = unlock_binding.lower()

    def is_locked(self) -> bool:
        """Return whether user control input is currently locked."""
        return self._locked

    def _on_key_event(self, event: "KeyboardEvent") -> None:
        """Track modifier state and dispatch key-down callbacks."""
        normalized = self._input_adapter.read_event(event)
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

        if self._event_dispatcher and normalized.key is not None:
            self._event_dispatcher(normalized)
            return

        if not any(self._modifier_state.values()):
            callback = self._scan_code_hotkeys.get(event.scan_code)
            if callback:
                if self._allowed_while_locked(name, event.scan_code):
                    self._dispatch(callback)
                return

        key_name = self._qualified_name(name)
        callback = self._hotkeys.get(key_name)
        if callback:
            if self._allowed_while_locked(name, event.scan_code, key_name):
                self._dispatch(callback)
        elif self._modifier_state["shift"] and not (
            self._modifier_state["ctrl"] or self._modifier_state["alt"]
        ):
            # A shifted symbol key (e.g. Shift+= producing "+") keeps the same
            # physical scan code, so fall back to its base-key binding.
            callback = self._scan_code_hotkeys.get(event.scan_code)
            if callback:
                if self._allowed_while_locked(name, event.scan_code):
                    self._dispatch(callback)

    def _allowed_while_locked(
        self, name: str, scan_code: int, qualified_name: str | None = None
    ) -> bool:
        if not self._locked:
            return True
        binding = self._unlock_binding
        if binding in SCAN_CODES:
            return scan_code == SCAN_CODES[binding] and not any(
                self._modifier_state.values()
            )
        return qualified_name == binding or (
            qualified_name is None and self._qualified_name(name) == binding
        )

    @staticmethod
    def _dispatch(callback: Callable[[], None]) -> None:
        """Run a callback without letting an error kill the global hook."""
        try:
            callback()
        except Exception:
            pass

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
        modifiers = [
            modifier
            for modifier in ("ctrl", "shift", "alt")
            if self._modifier_state[modifier]
        ]
        if modifiers:
            return "+".join([*modifiers, name])
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
