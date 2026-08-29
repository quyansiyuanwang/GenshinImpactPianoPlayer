"""Discovery and validation of score files for the runtime playlist."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence

from src.application.playlist import PlaylistEntry

SUPPORTED_SCORE_EXTENSIONS = frozenset({".qymusic", ".txt"})


class FileLoader:
    def __init__(self, extensions: frozenset[str] = SUPPORTED_SCORE_EXTENSIONS) -> None:
        self.extensions = {extension.casefold() for extension in extensions}

    def file(self, value: str | Path) -> tuple[PlaylistEntry | None, str | None]:
        path = Path(value).expanduser()
        if not path.exists():
            return None, f"File not found: {path}"
        if not path.is_file():
            return None, f"Not a file: {path}"
        if path.suffix.casefold() not in self.extensions:
            return None, f"Unsupported file type: {path.name}"
        try:
            path.resolve().open("r", encoding="utf-8-sig").close()
        except (OSError, UnicodeError) as error:
            return None, f"Cannot read {path.name}: {error}"
        return PlaylistEntry.from_path(path), None

    def directory(self, value: str | Path) -> tuple[list[PlaylistEntry], list[str]]:
        path = Path(value).expanduser()
        if not path.exists():
            return [], [f"Directory not found: {path}"]
        if not path.is_dir():
            return [], [f"Not a directory: {path}"]
        entries: list[PlaylistEntry] = []
        for candidate in sorted(path.iterdir(), key=lambda item: item.name.casefold()):
            if candidate.is_file() and candidate.suffix.casefold() in self.extensions:
                entry, error = self.file(candidate)
                if entry:
                    entries.append(entry)
                elif error:
                    return entries, [error]
        return entries, []

    def load_paths(self, values: Sequence[str | Path]) -> tuple[list[PlaylistEntry], list[str]]:
        entries: list[PlaylistEntry] = []
        errors: list[str] = []
        for value in values:
            path = Path(value).expanduser()
            if path.is_dir():
                found, found_errors = self.directory(path)
                entries.extend(found)
                errors.extend(found_errors)
            else:
                entry, error = self.file(path)
                if entry:
                    entries.append(entry)
                elif error:
                    errors.append(error)
        return entries, errors
