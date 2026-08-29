"""Reusable terminal components with resize-aware rendering."""

from dataclasses import dataclass
from typing import Any, Protocol, cast

import curses

from src.application.events import InputEvent, InputKind, KeyCode
from src.ui.cli.terminal_text import clip_cells


@dataclass(frozen=True)
class Rect:
    """A drawable terminal rectangle."""

    top: int
    left: int
    height: int
    width: int


class SurfaceLike(Protocol):
    """Minimal surface contract accepted by components and screens."""

    def getmaxyx(self) -> tuple[int, int]: ...
    def erase(self) -> None: ...
    def addstr(self, row: int, col: int, text: str, *attributes: int) -> None: ...
    def refresh(self) -> None: ...


class TerminalSurface:
    """Small safe wrapper around a curses window.

    Keeping terminal operations here lets components remain backend-neutral and
    gives every write one place to handle a resize between layout and drawing.
    """

    def __init__(self, window: Any) -> None:
        self.window = window
        self.highlight_attr = curses.A_REVERSE

    def getmaxyx(self) -> tuple[int, int]:
        return cast(tuple[int, int], self.window.getmaxyx())

    def erase(self) -> None:
        self.window.erase()

    def addstr(self, row: int, col: int, text: str, *attributes: int) -> None:
        height, width = self.getmaxyx()
        if row < 0 or row >= height or col < 0 or col >= width:
            return
        clipped = clip_cells(text, max(0, width - col - 1))
        try:
            self.window.addstr(row, col, clipped, *attributes)
        except Exception:
            # A SIGWINCH may invalidate dimensions after getmaxyx().
            return

    def refresh(self) -> None:
        self.window.refresh()


class Component:
    """Base class for independently renderable input components."""

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        raise NotImplementedError

    def handle(self, event: InputEvent) -> bool:
        return event.kind == InputKind.RESIZE


class TextComponent(Component):
    """Draw one or more clipped text lines."""

    def __init__(self, lines: list[str] | str) -> None:
        self.lines = [lines] if isinstance(lines, str) else lines

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        for offset, line in enumerate(self.lines[: rect.height]):
            try:
                surface.addstr(
                    rect.top + offset, rect.left, clip_cells(line, rect.width - 1)
                )
            except Exception:
                pass


class ListComponent(Component):
    """Render a selectable list and handle semantic navigation keys."""

    def __init__(self, items: list[str]) -> None:
        self.items = items
        self.selected = 0

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        visible = self.items[: rect.height]
        for index, item in enumerate(visible):
            marker = "> " if index == self.selected else "  "
            try:
                surface.addstr(
                    rect.top + index,
                    rect.left,
                    clip_cells(marker + item, rect.width - 1),
                )
            except Exception:
                pass

    def handle(self, event: InputEvent) -> bool:
        if event.kind != InputKind.KEY or event.key is None:
            return super().handle(event)
        if event.key == KeyCode.UP:
            self.selected = max(0, self.selected - 1)
            return True
        if event.key == KeyCode.DOWN:
            self.selected = min(max(0, len(self.items) - 1), self.selected + 1)
            return True
        return False


class TextInputComponent(Component):
    """Resize-safe single-line text editor."""

    def __init__(self, value: str = "") -> None:
        self.value = value

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        try:
            surface.addstr(rect.top, rect.left, clip_cells(self.value, rect.width - 1))
        except Exception:
            pass

    def handle(self, event: InputEvent) -> bool:
        if event.kind != InputKind.KEY or event.key is None:
            return super().handle(event)
        if event.key == KeyCode.BACKSPACE:
            self.value = self.value[:-1]
            return True
        if event.key == KeyCode.CHARACTER and event.text:
            self.value += event.text
            return True
        return False


class KeyCaptureComponent(TextInputComponent):
    """Text component for normalized key binding values."""

    def handle(self, event: InputEvent) -> bool:
        if event.key == KeyCode.ESCAPE:
            self.value = ""
            return True
        return super().handle(event)


class StatusBar(TextComponent):
    """A one-line status message component."""

    def set_message(self, message: str) -> None:
        self.lines = [message]


class ScrollablePanel(Component):
    """Render a vertically scrollable child list."""

    def __init__(self, children: list[Component]) -> None:
        self.children = children
        self.offset = 0

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        for index, child in enumerate(
            self.children[self.offset : self.offset + rect.height]
        ):
            child.render(surface, Rect(rect.top + index, rect.left, 1, rect.width))


class ResizeAwareScreen(Component):
    """Screen base that stores the latest layout rectangle."""

    def __init__(self) -> None:
        self.rect = Rect(0, 0, 0, 0)

    def handle(self, event: InputEvent) -> bool:
        if (
            event.kind == InputKind.RESIZE
            and event.width is not None
            and event.height is not None
        ):
            self.rect = Rect(0, 0, event.height, event.width)
            return True
        return super().handle(event)
