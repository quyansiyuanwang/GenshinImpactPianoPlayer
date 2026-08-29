"""Input adapters for curses and the global keyboard package."""

from typing import Any, Protocol

from src.application.events import InputEvent, InputKind, KeyCode
from src.ui.cli.input.key_binding import InputNormalizer


class InputSource(Protocol):
    """Any backend that can provide normalized application events."""

    def read_event(self) -> InputEvent: ...


class CursesInputAdapter:
    """Translate curses key codes into normalized events."""

    def __init__(self, screen: Any) -> None:
        self.screen = screen

    def read_event(self) -> InputEvent:
        value = self.screen.getch()
        import curses

        if value == getattr(curses, "KEY_RESIZE", -1):
            height, width = self.screen.getmaxyx()
            return InputEvent.resize(width, height)
        special = {
            10: KeyCode.ENTER,
            13: KeyCode.ENTER,
            27: KeyCode.ESCAPE,
            8: KeyCode.BACKSPACE,
            127: KeyCode.BACKSPACE,
            getattr(curses, "KEY_BACKSPACE", -2): KeyCode.BACKSPACE,
            getattr(curses, "KEY_UP", -3): KeyCode.UP,
            getattr(curses, "KEY_DOWN", -4): KeyCode.DOWN,
            getattr(curses, "KEY_LEFT", -5): KeyCode.LEFT,
            getattr(curses, "KEY_RIGHT", -6): KeyCode.RIGHT,
            getattr(curses, "KEY_PPAGE", -7): KeyCode.PAGE_UP,
            getattr(curses, "KEY_NPAGE", -8): KeyCode.PAGE_DOWN,
            getattr(curses, "KEY_HOME", -9): KeyCode.HOME,
            getattr(curses, "KEY_END", -10): KeyCode.END,
        }
        # Insert/delete are ordinary command names in the profile format but
        # are not represented by a dedicated semantic enum member.
        insert_code = getattr(curses, "KEY_IC", -11)
        delete_code = getattr(curses, "KEY_DC", -12)
        if value == insert_code:
            return InputEvent.character("insert")
        if value == delete_code:
            return InputEvent.character("delete")
        if value in special:
            return InputEvent(InputKind.KEY, special[value])
        if 0 <= value <= 255:
            return InputEvent.character(chr(value))
        f1 = getattr(curses, "KEY_F1", 265)
        f12 = getattr(curses, "KEY_F12", f1 + 11)
        if f1 <= value <= f12:
            return InputEvent(
                InputKind.KEY, KeyCode.FUNCTION, function_number=value - f1 + 1
            )
        return InputEvent(InputKind.KEY)

    def read_available(self) -> InputEvent:
        """Read one non-blocking event for main-loop polling."""
        return self.read_event()


class KeyboardInputAdapter:
    """Translate keyboard.KeyboardEvent objects into normalized events."""

    _modifiers = {
        "ctrl": "ctrl",
        "left ctrl": "ctrl",
        "right ctrl": "ctrl",
        "shift": "shift",
        "left shift": "shift",
        "right shift": "shift",
        "alt": "alt",
        "left alt": "alt",
        "right alt": "alt",
    }

    def __init__(self) -> None:
        self._modifier_state: set[str] = set()

    def read_event(self, event: Any) -> InputEvent:
        name = InputNormalizer.key_name(str(event.name))
        modifier = self._modifiers.get(name) or InputNormalizer.modifier(name)
        if event.event_type == "up":
            if modifier:
                self._modifier_state.discard(modifier)
            return InputEvent(InputKind.KEY)
        if modifier:
            self._modifier_state.add(modifier)
            return InputEvent(InputKind.KEY)
        if name.startswith("f") and name[1:].isdigit():
            return InputEvent(
                InputKind.KEY,
                KeyCode.FUNCTION,
                modifiers=frozenset(self._modifier_state),
                function_number=int(name[1:]),
            )
        special = {
            "enter": KeyCode.ENTER,
            "escape": KeyCode.ESCAPE,
            "backspace": KeyCode.BACKSPACE,
            "up": KeyCode.UP,
            "down": KeyCode.DOWN,
            "left": KeyCode.LEFT,
            "right": KeyCode.RIGHT,
            "page up": KeyCode.PAGE_UP,
            "page down": KeyCode.PAGE_DOWN,
            "home": KeyCode.HOME,
            "end": KeyCode.END,
        }
        if name in special:
            return InputEvent(
                InputKind.KEY, special[name], modifiers=frozenset(self._modifier_state)
            )
        if name == "+":
            name = "="
        return InputEvent.character(name, frozenset(self._modifier_state))
