"""Playlist screens that keep application services outside the UI."""

from __future__ import annotations

from src.application.events import InputEvent, InputKind, KeyCode
from src.application.playlist import Playlist
from src.ui.cli.components import Rect, SurfaceLike
from src.ui.cli.playlist.widgets import PlaylistTable, SearchInput


class PlaylistPanel:
    def __init__(self, playlist: Playlist) -> None:
        self.table = PlaylistTable(playlist)
        self.search = SearchInput(playlist)

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        self.table.render(surface, rect)
        self.search.render(surface, Rect(rect.top + rect.height - 1, rect.left, 1, rect.width))

    def handle(self, event: InputEvent) -> bool:
        if self.search.active:
            return self.search.handle(event)
        if event.kind == InputKind.KEY and event.key == KeyCode.CHARACTER and event.text == "/":
            self.search.active = True
            return True
        return self.table.handle(event)

