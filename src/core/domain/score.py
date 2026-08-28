"""Score domain model."""

from dataclasses import dataclass
from typing import List

from src.core.domain.note import Note
from src.core.domain.config import PlayConfig


@dataclass
class ParsedScore:
    """Complete parsed score with configuration and notes."""

    config: PlayConfig
    lines: List[List[Note]]  # Each line contains multiple notes
    warnings: List[str]  # Human-readable notes about ignored characters

    def __init__(
        self,
        config: PlayConfig,
        lines: List[List[Note]],
        warnings: List[str] | None = None,
    ) -> None:
        """Initialize parsed score.

        Args:
            config: Playback configuration
            lines: List of lines, each containing notes
            warnings: Notes about characters the parser skipped
        """
        self.config = config
        self.lines = lines
        self.warnings = warnings if warnings is not None else []

    def get_total_lines(self) -> int:
        """Get total number of lines in the score.

        Returns:
            Number of lines
        """
        return len(self.lines)

    def get_line(self, index: int) -> List[Note]:
        """Get a specific line by index.

        Args:
            index: Line index (0-based)

        Returns:
            List of notes in the line

        Raises:
            IndexError: If index is out of range
        """
        return self.lines[index]

    def get_total_notes(self) -> int:
        """Get total number of notes in the score.

        Returns:
            Total note count
        """
        return sum(len(line) for line in self.lines)
