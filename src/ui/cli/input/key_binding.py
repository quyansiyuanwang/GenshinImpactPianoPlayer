"""Backend-independent key binding matching."""

from dataclasses import dataclass

from src.application.events import InputEvent, InputKind, KeyCode


_SPECIAL_KEYS = {
    "enter": KeyCode.ENTER,
    "return": KeyCode.ENTER,
    "esc": KeyCode.ESCAPE,
    "escape": KeyCode.ESCAPE,
    "backspace": KeyCode.BACKSPACE,
    "up": KeyCode.UP,
    "down": KeyCode.DOWN,
    "left": KeyCode.LEFT,
    "right": KeyCode.RIGHT,
    "page up": KeyCode.PAGE_UP,
    "page down": KeyCode.PAGE_DOWN,
    "page_up": KeyCode.PAGE_UP,
    "page_down": KeyCode.PAGE_DOWN,
    "home": KeyCode.HOME,
    "end": KeyCode.END,
}

_SPECIAL_NAMES = {
    KeyCode.ENTER: "enter",
    KeyCode.ESCAPE: "escape",
    KeyCode.BACKSPACE: "backspace",
    KeyCode.UP: "up",
    KeyCode.DOWN: "down",
    KeyCode.LEFT: "left",
    KeyCode.RIGHT: "right",
    KeyCode.PAGE_UP: "page up",
    KeyCode.PAGE_DOWN: "page down",
    KeyCode.HOME: "home",
    KeyCode.END: "end",
}


@dataclass(frozen=True)
class KeyBinding:
    """Normalized key combination used by the command router."""

    name: str
    modifiers: frozenset[str] = frozenset()

    @classmethod
    def parse(cls, value: str) -> "KeyBinding":
        value = value.strip().lower()
        if value == "+":
            value = "="
        elif value.endswith("+") and not value.endswith("++"):
            raise ValueError("binding is missing a key")
        if value.endswith("++"):
            # ``ctrl++`` is the conventional spelling for Ctrl plus the
            # equals/plus key, but splitting on '+' would lose the key token.
            value = value[:-1] + "="
        parts = [part.strip().lower() for part in value.split("+") if part.strip()]
        if not parts:
            raise ValueError("empty key binding")
        allowed_modifiers = {"ctrl", "shift", "alt"}
        unknown_modifiers = set(parts[:-1]) - allowed_modifiers
        if unknown_modifiers:
            raise ValueError(f"unknown modifier: {sorted(unknown_modifiers)[0]}")
        modifiers = frozenset(parts[:-1])
        key = parts[-1]
        if key in {"+", "plus"}:
            key = "="
        if key in {"return", "esc"}:
            key = {"return": "enter", "esc": "escape"}[key]
        key = {
            "page_up": "page up",
            "page_down": "page down",
        }.get(key, key)
        if not key:
            raise ValueError("empty key binding")
        if key in allowed_modifiers:
            raise ValueError("binding must include a non-modifier key")
        return cls(key, modifiers)

    def matches(self, event: InputEvent) -> bool:
        if event.kind != InputKind.KEY or event.key is None:
            return False
        if event.key == KeyCode.CHARACTER:
            name = event.text.lower()
        elif event.key == KeyCode.FUNCTION:
            name = f"f{event.function_number}"
        else:
            name = _SPECIAL_NAMES.get(event.key, event.key.value)
        return name == self.name and event.modifiers == self.modifiers

    def __str__(self) -> str:
        prefix = "+".join(sorted(self.modifiers))
        return f"{prefix}+{self.name}" if prefix else self.name


class InputNormalizer:
    """Canonicalize key names and modifier labels from any input backend."""

    _modifier_aliases = {
        "control": "ctrl",
        "left control": "ctrl",
        "right control": "ctrl",
        "option": "alt",
    }

    @classmethod
    def modifier(cls, name: str) -> str | None:
        value = name.strip().lower()
        value = cls._modifier_aliases.get(value, value)
        return value if value in {"ctrl", "shift", "alt"} else None

    @classmethod
    def key_name(cls, name: str) -> str:
        value = name.strip().lower()
        aliases = {
            "return": "enter",
            "esc": "escape",
            "pageup": "page up",
            "pagedown": "page down",
            "plus": "=",
        }
        return aliases.get(value, "=" if value == "+" else value)
