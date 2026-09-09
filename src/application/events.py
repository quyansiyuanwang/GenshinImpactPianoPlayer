"""Shared application input events."""

from dataclasses import dataclass, field
from enum import Enum


class InputKind(Enum):
    """Kinds of input delivered to the application."""

    KEY = "key"
    RESIZE = "resize"
    QUIT = "quit"


class KeyCode(Enum):
    """Semantic keyboard keys independent of input backend."""

    CHARACTER = "character"
    ENTER = "enter"
    ESCAPE = "escape"
    BACKSPACE = "backspace"
    TAB = "tab"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    PAGE_UP = "page_up"
    PAGE_DOWN = "page_down"
    HOME = "home"
    END = "end"
    FUNCTION = "function"


@dataclass(frozen=True)
class InputEvent:
    """Normalized event consumed by commands and TUI components."""

    kind: InputKind
    key: KeyCode | None = None
    text: str = ""
    modifiers: frozenset[str] = field(default_factory=frozenset)
    function_number: int | None = None
    width: int | None = None
    height: int | None = None
    scan_code: int | None = None

    @classmethod
    def character(
        cls, value: str, modifiers: frozenset[str] = frozenset(), scan_code: int | None = None
    ) -> "InputEvent":
        return cls(InputKind.KEY, KeyCode.CHARACTER, value, modifiers, scan_code=scan_code)

    @classmethod
    def resize(cls, width: int, height: int) -> "InputEvent":
        return cls(InputKind.RESIZE, width=width, height=height)

    @classmethod
    def quit(cls) -> "InputEvent":
        return cls(InputKind.QUIT)
