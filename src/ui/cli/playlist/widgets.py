"""Backend-neutral playlist widgets."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from src.application.events import InputEvent, InputKind, KeyCode
from src.application.playlist import Playlist, PlaylistEntry
from src.ui.cli.components import Component, Rect, SurfaceLike
from src.ui.cli.settings.layout import clip


class PlaylistTable(Component):
    def __init__(self, playlist: Playlist, *, focused: bool = False) -> None:
        self.playlist = playlist
        self.offset = 0
        self.focused = focused

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        if rect.height <= 0 or rect.width <= 1:
            return
        focus_label = " [FOCUSED]" if self.focused else ""
        query = f"  /{self.playlist.query}" if self.playlist.query else ""
        title = f" Playlist ({len(self.playlist.visible_entries)}){focus_label}{query} "
        title_attr = getattr(surface, "highlight_attr", 0) if self.focused else 0
        surface.addstr(rect.top, rect.left, clip(title, rect.width), title_attr)
        capacity = max(0, rect.height - 2)
        selected = self.playlist.visible_index
        if selected < self.offset:
            self.offset = selected
        elif selected >= self.offset + capacity:
            self.offset = max(0, selected - capacity + 1)
        maximum = max(0, len(self.playlist.visible_entries) - capacity)
        self.offset = min(self.offset, maximum)
        entries = self.playlist.visible_entries[self.offset : self.offset + capacity]
        for row, entry in enumerate(entries, 1):
            index = self.offset + row - 1
            selected = index == self.playlist.visible_index
            marker = ">" if selected else " "
            current = "*" if entry is self.playlist.current else " "
            line = f"{marker}{current} {index + 1:02d}  {entry.title}"
            attr = (
                getattr(surface, "highlight_attr", 0)
                if selected and self.focused
                else getattr(surface, "active_attr", 0)
                if entry is self.playlist.current
                else 0
            )
            surface.addstr(rect.top + row, rect.left, clip(line, rect.width), attr)
        if not entries:
            surface.addstr(
                rect.top + 1, rect.left, clip("(empty)  A add  / search", rect.width)
            )
        if rect.height > 1:
            hint = " Up/Down Move  Enter Load " if self.focused else " Tab Focus "
            surface.addstr(
                rect.top + rect.height - 1,
                rect.left,
                clip(hint, rect.width),
            )

    def handle(self, event: InputEvent) -> bool:
        if event.kind != InputKind.KEY:
            return event.kind == InputKind.RESIZE
        if event.key == KeyCode.UP:
            self.playlist.move_visible(self.playlist.visible_index - 1)
            return True
        if event.key == KeyCode.DOWN:
            self.playlist.move_visible(self.playlist.visible_index + 1)
            return True
        if event.key == KeyCode.HOME:
            self.playlist.move_visible(0)
            return True
        if event.key == KeyCode.END:
            self.playlist.move_visible(len(self.playlist.visible_entries) - 1)
            return True
        return False


class SearchInput(Component):
    def __init__(
        self, playlist: Playlist, on_change: Callable[[str], None] | None = None
    ) -> None:
        self.playlist = playlist
        self.value = ""
        self.active = False
        self.on_change = on_change

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        if self.active:
            surface.addstr(
                rect.top,
                rect.left,
                clip(f"Search: {self.value}", rect.width),
                getattr(surface, "highlight_attr", 0),
            )

    def handle(self, event: InputEvent) -> bool:
        if event.kind == InputKind.RESIZE:
            return True
        if event.kind != InputKind.KEY or event.key is None or not self.active:
            return False
        if event.key == KeyCode.ESCAPE:
            self.active = False
            self.value = ""
            self.playlist.clear_search()
            return True
        if event.key == KeyCode.ENTER:
            self.active = False
            return True
        if event.key == KeyCode.BACKSPACE:
            self.value = self.value[:-1]
        elif event.key == KeyCode.CHARACTER and event.text.isprintable():
            self.value += event.text
        else:
            return False
        self.playlist.search(self.value)
        if self.on_change:
            self.on_change(self.value)
        return True


class FileBrowser(Component):
    """Simple current-directory browser used by integrations."""

    def __init__(self, entries: Sequence[PlaylistEntry] = ()) -> None:
        self.entries = list(entries)
        self.cursor = 0

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        for index, entry in enumerate(self.entries[: rect.height]):
            marker = ">" if index == self.cursor else " "
            surface.addstr(
                rect.top + index, rect.left, clip(f"{marker} {entry.title}", rect.width)
            )
