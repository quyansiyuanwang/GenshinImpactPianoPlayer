"""Small reusable screen primitives used by the settings workflow.

The legacy CLI mixins remain responsible for wiring application services.  The
classes here keep page state and event handling independent of curses values,
the player, and profile storage.
"""

from __future__ import annotations

from collections.abc import Callable

from src.application.events import InputEvent, InputKind, KeyCode
from src.ui.cli.components import (
    Component,
    ListComponent,
    Rect,
    SurfaceLike,
    TextComponent,
)


class MainScreen(Component):
    """Render a supplied set of score/status lines."""

    def __init__(self, lines: list[str] | None = None) -> None:
        self.content = TextComponent(lines or [])

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        self.content.render(surface, rect)


class SettingsScreen(Component):
    """Navigate settings sections without knowing how they are persisted."""

    def __init__(
        self,
        sections: list[str] | None = None,
        on_open: Callable[[str], None] | None = None,
    ) -> None:
        self.sections = ListComponent(sections or ["hotkeys", "mapping"])
        self.on_open = on_open

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        self.sections.render(surface, rect)

    def handle(self, event: InputEvent) -> bool:
        if self.sections.handle(event):
            return True
        if event.kind == InputKind.KEY and event.key == KeyCode.ENTER:
            if self.sections.items and self.on_open:
                self.on_open(self.sections.items[self.sections.selected])
            return True
        return super().handle(event)


class HotkeyProfileScreen(SettingsScreen):
    """Marker screen for the hotkey profile editor."""


class MappingProfileScreen(SettingsScreen):
    """Marker screen for the score mapping editor."""
