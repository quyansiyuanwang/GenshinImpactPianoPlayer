"""Shared fixtures for deterministic playback tests."""

from collections.abc import Iterable
from threading import Event, Lock
import time

from src.core.domain.config import PlayConfig
from src.core.domain.note import Note, NoteType
from src.core.domain.score import ParsedScore


class FakeKeyboard:
    """Record keyboard operations without sending system input."""

    def __init__(self) -> None:
        self.operations: list[tuple[str, tuple[str, ...]]] = []
        self.operation_event = Event()
        self._lock = Lock()

    def press_key(self, key: str) -> None:
        self._record("press", [key])

    def release_key(self, key: str) -> None:
        self._record("release", [key])

    def tap_key(self, key: str) -> None:
        self._record("tap", [key])

    def press_keys_simultaneously(self, keys: list[str]) -> None:
        self._record("chord", keys)

    def wait_for(
        self, operation: tuple[str, tuple[str, ...]], timeout: float = 1.0
    ) -> bool:
        """Wait until an expected operation is present."""
        deadline = time.monotonic() + timeout
        while operation not in self.operations:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            self.operation_event.clear()
            self.operation_event.wait(remaining)
        return True

    def _record(self, operation: str, keys: Iterable[str]) -> None:
        with self._lock:
            self.operations.append((operation, tuple(keys)))
            self.operation_event.set()


def make_score(lines: list[list[str]], interval: float = 0.5) -> ParsedScore:
    """Create a small score from note names for playback tests."""
    config = PlayConfig(
        version=1.0,
        speed_multiplier=1.0,
        arpeggio_interval=interval,
        interval_rating=interval,
        line_interval_rating=0.0,
        space_interval_rating=1.0,
        empty_line_interval_rating=0.0,
        segment_length=0,
        segment_strict=False,
    )
    notes = [[Note(NoteType.SINGLE, [key]) for key in line] for line in lines]
    return ParsedScore(config, notes)
