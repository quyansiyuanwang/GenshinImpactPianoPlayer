"""Backend-neutral page stack for the terminal user interface."""

from __future__ import annotations

from typing import Protocol

from src.application.events import InputEvent, InputKind
from src.ui.cli.components import Rect, SurfaceLike


class Screen(Protocol):
    """Contract implemented by every interactive page."""

    def render(self, surface: SurfaceLike, rect: Rect) -> None: ...

    def handle(self, event: InputEvent) -> bool: ...


class ScreenManager:
    """Manage nested screens and centralize resize propagation."""

    def __init__(self, root: Screen | None = None) -> None:
        self._stack: list[Screen] = []
        if root is not None:
            self._stack.append(root)
        self._rect = Rect(0, 0, 0, 0)

    @property
    def current(self) -> Screen | None:
        return self._stack[-1] if self._stack else None

    def open(self, screen: Screen) -> None:
        self._stack.append(screen)
        if self._rect.width or self._rect.height:
            screen.handle(InputEvent.resize(self._rect.width, self._rect.height))

    def close(self) -> Screen | None:
        return self._stack.pop() if self._stack else None

    def handle(self, event: InputEvent) -> bool:
        if (
            event.kind == InputKind.RESIZE
            and event.width is not None
            and event.height is not None
        ):
            self._rect = Rect(0, 0, event.height, event.width)
        screen = self.current
        return screen.handle(event) if screen is not None else False

    def render(self, surface: SurfaceLike) -> None:
        screen = self.current
        if screen is None:
            return
        height, width = surface.getmaxyx()
        self._rect = Rect(0, 0, height, width)
        screen.render(surface, self._rect)
