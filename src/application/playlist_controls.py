"""Playlist actions exposed by the CLI host."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.application.events import InputEvent, InputKind, KeyCode


class PlaylistControlsMixin:
    playlist: Any
    file_loader: Any
    track_controller: Any
    playlist_focus: bool
    _flash: Any

    def _load_playlist_entry(self, entry: Any) -> None:
        ok, message = self.track_controller.load(entry.path)
        self._flash(message)
        if ok:
            self.playlist.current_index = self.playlist.entries.index(entry)

    def playlist_next(self, _event: InputEvent | None = None) -> None:
        entry = self.playlist.next()
        if entry:
            self._load_playlist_entry(entry)

    def playlist_previous(self, _event: InputEvent | None = None) -> None:
        entry = self.playlist.previous()
        if entry:
            self._load_playlist_entry(entry)

    def playlist_play_selected(self, _event: InputEvent | None = None) -> None:
        entry = self.playlist.move_visible(self.playlist.visible_index)
        if entry:
            self._load_playlist_entry(entry)

    def playlist_add_paths(self, paths: list[str | Path]) -> int:
        entries, errors = self.file_loader.load_paths(paths)
        added = self.playlist.add_paths([entry.path for entry in entries])
        self.playlist_errors = errors
        self._flash(
            f"Added {added} file(s)"
            if added
            else (errors[0] if errors else "No new files")
        )
        return int(added)

    def playlist_remove_selected(self, _event: InputEvent | None = None) -> None:
        removed = self.playlist.remove_visible(self.playlist.visible_index)
        if removed:
            self._flash(f"Removed {removed.title}")

    def playlist_clear(self, _event: InputEvent | None = None) -> None:
        self.playlist.clear()
        self._flash("Playlist cleared")

    def handle_playlist_event(self, event: InputEvent) -> bool:
        if event.kind != InputKind.KEY:
            return False
        if event.key == KeyCode.CHARACTER and event.text == "\t":
            self.playlist_focus = not self.playlist_focus
            return True
        if not self.playlist_focus:
            return False
        if event.key == KeyCode.UP:
            self.playlist.move_visible(max(0, self.playlist.visible_index - 1))
            return True
        if event.key == KeyCode.DOWN:
            self.playlist.move_visible(
                min(
                    len(self.playlist.visible_entries) - 1,
                    self.playlist.visible_index + 1,
                )
            )
            return True
        if event.key == KeyCode.HOME:
            self.playlist.move_visible(0)
            return True
        if event.key == KeyCode.END:
            self.playlist.move_visible(max(0, len(self.playlist.visible_entries) - 1))
            return True
        if event.key == KeyCode.ENTER:
            self.playlist_play_selected(event)
            return True
        if event.key != KeyCode.CHARACTER:
            return False
        if event.text.lower() == "n":
            self.playlist_next(event)
            return True
        if event.text.lower() == "p":
            self.playlist_previous(event)
            return True
        if event.text.lower() == "d":
            self.playlist_remove_selected(event)
            return True
        if event.text.lower() == "c":
            self.playlist_clear(event)
            return True
        return False
