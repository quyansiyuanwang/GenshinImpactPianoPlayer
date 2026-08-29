"""Runtime playlist model used by the CLI and terminal UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlaylistEntry:
    path: Path
    title: str
    directory: Path

    @classmethod
    def from_path(cls, path: Path) -> "PlaylistEntry":
        resolved = path.expanduser().resolve()
        return cls(resolved, resolved.name, resolved.parent)


class Playlist:
    """Ordered, de-duplicated list of score files with search state."""

    def __init__(self, entries: list[PlaylistEntry] | None = None) -> None:
        self.entries: list[PlaylistEntry] = []
        self.current_index = 0
        self.selected_index = 0
        self._visible_indices: list[int] = []
        self.query = ""
        for entry in entries or []:
            self.add(entry)

    @property
    def current(self) -> PlaylistEntry | None:
        return self.entries[self.current_index] if self.entries else None

    @property
    def visible_entries(self) -> list[PlaylistEntry]:
        indices = self._visible_indices or list(range(len(self.entries)))
        return [self.entries[index] for index in indices]

    @property
    def visible_index(self) -> int:
        indices = self._visible_indices or list(range(len(self.entries)))
        try:
            return indices.index(self.selected_index)
        except ValueError:
            return 0

    def move_visible(self, index: int) -> PlaylistEntry | None:
        indices = self._visible_indices or list(range(len(self.entries)))
        if not indices:
            return None
        index = min(max(0, index), len(indices) - 1)
        self.selected_index = indices[index]
        return self.entries[self.selected_index]

    def add(self, entry: PlaylistEntry) -> bool:
        key = str(entry.path).casefold()
        if any(str(item.path).casefold() == key for item in self.entries):
            return False
        self.entries.append(entry)
        if len(self.entries) == 1:
            self.current_index = 0
        self._apply_query()
        return True

    def add_paths(self, paths: list[Path]) -> int:
        added = 0
        for path in paths:
            if self.add(PlaylistEntry.from_path(path)):
                added += 1
        return added

    def remove_visible(self, index: int) -> PlaylistEntry | None:
        indices = self._visible_indices or list(range(len(self.entries)))
        if not 0 <= index < len(indices):
            return None
        actual = indices[index]
        removed = self.entries.pop(actual)
        if actual < self.current_index:
            self.current_index -= 1
        elif actual == self.current_index:
            self.current_index = min(self.current_index, max(0, len(self.entries) - 1))
        if actual < self.selected_index:
            self.selected_index -= 1
        elif actual == self.selected_index:
            self.selected_index = min(self.selected_index, max(0, len(self.entries) - 1))
        self._apply_query()
        return removed

    def clear(self) -> None:
        self.entries.clear()
        self.current_index = 0
        self._visible_indices.clear()

    def select_visible(self, index: int) -> PlaylistEntry | None:
        indices = self._visible_indices or list(range(len(self.entries)))
        if not 0 <= index < len(indices):
            return None
        self.current_index = indices[index]
        self.selected_index = self.current_index
        return self.current

    def next(self) -> PlaylistEntry | None:
        if not self.entries:
            return None
        self.current_index = (self.current_index + 1) % len(self.entries)
        self.selected_index = self.current_index
        return self.current

    def previous(self) -> PlaylistEntry | None:
        if not self.entries:
            return None
        self.current_index = (self.current_index - 1) % len(self.entries)
        self.selected_index = self.current_index
        return self.current

    def search(self, query: str) -> list[PlaylistEntry]:
        self.query = query
        self._apply_query()
        return self.visible_entries

    def clear_search(self) -> None:
        self.search("")

    def _apply_query(self) -> None:
        needle = self.query.casefold().strip()
        if not needle:
            self._visible_indices = []
            return
        self._visible_indices = [
            index
            for index, entry in enumerate(self.entries)
            if needle in entry.title.casefold()
            or needle in str(entry.path.parent).casefold()
        ]
