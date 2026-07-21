"""Score parser for reading and parsing score text files."""

from typing import List, Union

from src.core.domain.note import Note, NoteType
from src.core.domain.score import ParsedScore
from src.core.domain.config import PlayConfig
from src.application.config.constants import (
    VALID_KEYS,
    DEFAULT_VERSION,
    DEFAULT_SPEED_MULTIPLIER,
    DEFAULT_ARPEGGIO_INTERVAL,
    DEFAULT_INTERVAL_RATING,
    DEFAULT_LINE_INTERVAL_RATING,
    DEFAULT_SPACE_INTERVAL_RATING,
    DEFAULT_EMPTY_LINE_INTERVAL_RATING,
    DEFAULT_SEGMENT_LENGTH,
    DEFAULT_SEGMENT_STRICT,
)

__all__ = ["ScoreParser", "Note", "NoteType", "ParsedScore"]


class ScoreParser:
    """Parser for score text files."""

    def __init__(self, file_path: str) -> None:
        """Initialize parser.

        Args:
            file_path: Path to score file
        """
        self.file_path = file_path
        self.content = ""
        self.score_content = ""
        self.pos = 0
        self._segment_length = 0
        self._segment_strict = False
        self._empty_line_interval_rating = 0.0

    def parse(self) -> ParsedScore:
        """Parse the score file and return ParsedScore object.

        Returns:
            Parsed score with configuration and notes
        """
        with open(self.file_path, encoding="utf-8") as f:
            self.content = f.read()

        config = self._parse_config()
        lines = self._parse_score()

        return ParsedScore(config=config, lines=lines)

    def _parse_config(self) -> PlayConfig:
        """Parse configuration parameters from file header.

        Returns:
            Parsed configuration
        """
        lines = self.content.split("\n")
        config_dict: dict[str, float] = {}
        score_start = 0

        for i, line in enumerate(lines):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Check for separator line marking end of config
            if line.startswith("---"):
                score_start = i + 1
                break

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Convert to appropriate type
                try:
                    config_dict[key.lower()] = float(value)
                except ValueError:
                    pass
            else:
                # First non-config line marks start of score
                score_start = i
                break

        # Store score content starting position
        self.score_content = "\n".join(lines[score_start:])

        # Handle version
        version = config_dict.get("version")
        if version is None and lines and lines[0].strip():
            try:
                version = float(lines[0].strip())
            except ValueError:
                version = DEFAULT_VERSION

        # Store segment settings for use during line parsing
        self._segment_length = int(
            config_dict.get("segment_length", DEFAULT_SEGMENT_LENGTH)
        )
        segment_strict_value = config_dict.get("segment_strict", DEFAULT_SEGMENT_STRICT)
        self._segment_strict = bool(segment_strict_value)
        self._empty_line_interval_rating = config_dict.get(
            "empty_line_interval_rating", DEFAULT_EMPTY_LINE_INTERVAL_RATING
        )

        return PlayConfig(
            version=version or DEFAULT_VERSION,
            speed_multiplier=config_dict.get(
                "speed_multiplier", DEFAULT_SPEED_MULTIPLIER
            ),
            arpeggio_interval=config_dict.get(
                "arpeggio_interval", DEFAULT_ARPEGGIO_INTERVAL
            ),
            interval_rating=config_dict.get("interval_rating", DEFAULT_INTERVAL_RATING),
            line_interval_rating=config_dict.get(
                "line_interval_rating", DEFAULT_LINE_INTERVAL_RATING
            ),
            space_interval_rating=config_dict.get(
                "space_interval_rating", DEFAULT_SPACE_INTERVAL_RATING
            ),
            empty_line_interval_rating=config_dict.get(
                "empty_line_interval_rating", DEFAULT_EMPTY_LINE_INTERVAL_RATING
            ),
            segment_length=self._segment_length,
            segment_strict=self._segment_strict,
        )

    def _parse_score(self) -> List[List[Note]]:
        """Parse the score content into lines of notes.

        Returns:
            List of lines, each containing notes
        """
        lines: List[List[Note]] = []

        for line in self.score_content.split("\n"):
            stripped = line.strip()

            # Skip comments
            if stripped.startswith("#"):
                continue

            # Empty line - only add if empty_line_interval_rating > 0
            if not stripped:
                if self._empty_line_interval_rating > 0:
                    lines.append([Note(type=NoteType.EMPTY_LINE, keys=[])])
                continue

            # Parse normal line
            notes = self._parse_line(stripped)
            if notes:
                lines.append(notes)

        return lines

    def _parse_line(self, line: str) -> List[Note]:
        """Parse a single line into a list of notes.

        Args:
            line: Line content to parse

        Returns:
            List of notes in the line
        """
        # First pass: split by '/' and parse each segment
        segments: List[List[Note]] = []
        current_segment: List[Note] = []
        i = 0

        while i < len(line):
            char = line[i]

            if char == "/":
                # End current segment
                if current_segment or segments:
                    segments.append(current_segment)
                    current_segment = []
                i += 1
            elif char.isspace():
                # Any whitespace character is a rest
                current_segment.append(Note(type=NoteType.SINGLE, keys=[" "]))
                i += 1
            elif char == "(":
                # Chord
                end = self._find_matching_bracket(line, i, "(", ")")
                chord_content = line[i + 1 : end]
                chord_keys: List[Union[str, Note]] = [
                    k.upper() for k in chord_content if k.upper() in VALID_KEYS
                ]
                if chord_keys:
                    current_segment.append(Note(type=NoteType.CHORD, keys=chord_keys))
                i = end + 1
            elif char == "[":
                # Arpeggio
                end = self._find_matching_bracket(line, i, "[", "]")
                arpeggio_content = line[i + 1 : end]
                arpeggio_notes = self._parse_arpeggio(arpeggio_content)
                if arpeggio_notes:
                    current_segment.append(
                        Note(type=NoteType.ARPEGGIO, keys=arpeggio_notes)
                    )
                i = end + 1
            elif char.upper() in VALID_KEYS:
                # Single note
                single_key: List[Union[str, Note]] = [char.upper()]
                current_segment.append(Note(type=NoteType.SINGLE, keys=single_key))
                i += 1
            else:
                # Skip invalid characters
                i += 1

        # Add the last segment
        if current_segment:
            segments.append(current_segment)

        # If no segments, treat entire line as one segment
        if not segments:
            segments = [current_segment] if current_segment else []

        # Second pass: apply segment_length padding/truncation if enabled
        if self._segment_length > 0:
            processed_segments: List[List[Note]] = []
            for segment in segments:
                if len(segment) < self._segment_length:
                    # Pad with rests
                    padding_needed = self._segment_length - len(segment)
                    processed_segment = segment + [
                        Note(type=NoteType.SINGLE, keys=[" "])
                        for _ in range(padding_needed)
                    ]
                    processed_segments.append(processed_segment)
                elif len(segment) > self._segment_length and self._segment_strict:
                    # Strict mode: truncate
                    processed_segments.append(segment[: self._segment_length])
                else:
                    # Normal mode: keep as is
                    processed_segments.append(segment)
            segments = processed_segments

        # Flatten all segments
        notes: List[Note] = []
        for segment in segments:
            notes.extend(segment)

        return notes

    def _parse_arpeggio(self, content: str) -> List[Union[str, Note]]:
        """Parse arpeggio content which may contain nested chords.

        Args:
            content: Arpeggio content

        Returns:
            List of notes/keys in the arpeggio
        """
        notes: List[Union[str, Note]] = []
        i = 0

        while i < len(content):
            char = content[i]

            if char == "(":
                # Nested chord within arpeggio
                end = self._find_matching_bracket(content, i, "(", ")")
                chord_content = content[i + 1 : end]
                chord_keys: List[Union[str, Note]] = [
                    k.upper() for k in chord_content if k.upper() in VALID_KEYS
                ]
                if chord_keys:
                    notes.append(Note(type=NoteType.CHORD, keys=chord_keys))
                i = end + 1
            elif char.upper() in VALID_KEYS:
                # Single note
                notes.append(char.upper())
                i += 1
            else:
                # Skip invalid characters
                i += 1

        return notes

    def _find_matching_bracket(
        self, text: str, start: int, open_char: str, close_char: str
    ) -> int:
        """Find the index of the matching closing bracket.

        Args:
            text: Text to search in
            start: Starting position
            open_char: Opening bracket character
            close_char: Closing bracket character

        Returns:
            Index of matching closing bracket
        """
        count = 1
        i = start + 1

        while i < len(text) and count > 0:
            if text[i] == open_char:
                count += 1
            elif text[i] == close_char:
                count -= 1
            i += 1

        return i - 1
