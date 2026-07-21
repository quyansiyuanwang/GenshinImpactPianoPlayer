"""File service for handling score file operations."""

from pathlib import Path
from typing import Optional

from src.core.domain.score import ParsedScore
from src.core.parser.score_parser import ScoreParser


class FileService:
    """Service for file operations related to scores."""

    def __init__(self) -> None:
        """Initialize file service."""
        self._current_file_path: Optional[Path] = None
        self._current_score: Optional[ParsedScore] = None
        self._file_content: str = ""

    @property
    def current_file_path(self) -> Optional[Path]:
        """Get current file path.

        Returns:
            Current file path or None
        """
        return self._current_file_path

    @property
    def current_score(self) -> Optional[ParsedScore]:
        """Get current parsed score.

        Returns:
            Current ParsedScore or None
        """
        return self._current_score

    @property
    def file_content(self) -> str:
        """Get original file content.

        Returns:
            File content as string
        """
        return self._file_content

    def load_score(self, file_path: str | Path) -> ParsedScore:
        """Load and parse a score file.

        Args:
            file_path: Path to score file

        Returns:
            Parsed score

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Score file not found: {file_path}")

        # Read original content
        with open(file_path, encoding="utf-8") as f:
            self._file_content = f.read()

        # Parse score
        parser = ScoreParser(str(file_path))
        score = parser.parse()

        self._current_file_path = file_path
        self._current_score = score

        return score

    def reload_score(self) -> ParsedScore:
        """Reload the current score file from disk.

        Returns:
            Reloaded ParsedScore

        Raises:
            ValueError: If no file is currently loaded
            FileNotFoundError: If file no longer exists
        """
        if self._current_file_path is None:
            raise ValueError("No file currently loaded")

        return self.load_score(self._current_file_path)

    def reparse_score(self) -> ParsedScore:
        """Reparse the current score with updated configuration.

        This is useful when configuration has changed and you want to
        reparse the score with the new settings (e.g., segment_length).

        Returns:
            Reparsed ParsedScore

        Raises:
            ValueError: If no file is currently loaded
        """
        if self._current_file_path is None:
            raise ValueError("No file currently loaded")

        # Parse again (will use current config from file)
        parser = ScoreParser(str(self._current_file_path))
        score = parser.parse()

        self._current_score = score
        return score

    def get_config_file_path(self) -> Optional[Path]:
        """Get the path for the configuration file associated with current score.

        Returns:
            Path to .config.toml file or None if no score loaded
        """
        if self._current_file_path is None:
            return None

        return self._current_file_path.with_suffix(".config.toml")

    def validate_file(self, file_path: str | Path) -> bool:
        """Validate if a file can be loaded as a score.

        Args:
            file_path: Path to file to validate

        Returns:
            True if file is valid, False otherwise
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return False

        if not file_path.is_file():
            return False

        try:
            # Try to parse
            parser = ScoreParser(str(file_path))
            parser.parse()
            return True
        except Exception:
            return False

    def get_file_info(self) -> dict[str, str | int]:
        """Get information about the current file.

        Returns:
            Dictionary with file information

        Raises:
            ValueError: If no file is currently loaded
        """
        if self._current_file_path is None or self._current_score is None:
            raise ValueError("No file currently loaded")

        return {
            "path": str(self._current_file_path),
            "name": self._current_file_path.name,
            "size": self._current_file_path.stat().st_size,
            "lines": self._current_score.get_total_lines(),
            "notes": self._current_score.get_total_notes(),
        }
