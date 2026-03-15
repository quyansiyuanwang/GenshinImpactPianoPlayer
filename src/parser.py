"""Parser for score text files."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Union
from src.config import PlayConfig
from src.constants import (
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


class NoteType(Enum):
    """Type of musical note."""

    SINGLE = "single"  # Single key
    CHORD = "chord"  # Multiple keys pressed simultaneously
    ARPEGGIO = "arpeggio"  # Keys pressed in rapid succession
    EMPTY_LINE = "empty_line"  # Empty line (blank line in score)


@dataclass
class Note:
    """Represents a musical note or group of notes."""

    type: NoteType
    keys: List[Union[str, "Note"]]  # Can contain strings or nested Notes

    def __init__(self, type: NoteType, keys: List[Union[str, "Note"]]):
        self.type = type
        self.keys = keys

    def display(self, show_rest_as_underscore: bool = True) -> str:
        """Display the note as a string.

        Args:
            show_rest_as_underscore: If True, show rest (space) as "_"

        Returns:
            String representation of the note
        """
        if self.type == NoteType.SINGLE:
            key = self.keys[0]
            assert isinstance(key, str), "SINGLE note key must be string"
            if key == " ":
                return "_" if show_rest_as_underscore else " "
            return key

        if self.type == NoteType.CHORD:
            chord_keys = [k for k in self.keys if isinstance(k, str)]
            return f"({''.join(chord_keys)})"

        if self.type == NoteType.ARPEGGIO:
            arp_content = ""
            for key in self.keys:
                if isinstance(key, str):
                    arp_content += key
                else:  # Nested chord
                    nested_chord_keys = [k for k in key.keys if isinstance(k, str)]
                    arp_content += f"({''.join(nested_chord_keys)})"
            return f"[{arp_content}]"

        if self.type == NoteType.EMPTY_LINE:
            return "[Empty Line]"

        return ""


@dataclass
class ParsedScore:
    """Complete parsed score with configuration and notes."""

    config: PlayConfig
    lines: List[List[Note]]  # Each line contains multiple notes


class ScoreParser:
    """Parser for score text files."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = ""
        self.pos = 0
        self._segment_length = 0  # Will be set during config parsing
        self._segment_strict = False  # Will be set during config parsing
        self._empty_line_interval_rating = 0.0  # Will be set during config parsing

    def parse(self) -> ParsedScore:
        """Parse the score file and return ParsedScore object."""
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.content = f.read()

        config = self._parse_config()
        lines = self._parse_score()

        return ParsedScore(config=config, lines=lines)

    def _parse_config(self) -> PlayConfig:
        """Parse configuration parameters from file header."""
        lines = self.content.split("\n")
        config_dict: dict[str, float] = {}
        score_start = 0

        for i, line in enumerate(lines):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Check for separator line (------) marking end of config
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

        # Handle both 'version' as key or first line as version number
        version = config_dict.get("version", None)
        if version is None and lines and lines[0].strip():
            try:
                version = float(lines[0].strip())
            except ValueError:
                version = 1.0

        # Store segment_length for use during line parsing
        self._segment_length = int(
            config_dict.get("segment_length", DEFAULT_SEGMENT_LENGTH)
        )
        # Store segment_strict for use during line parsing
        segment_strict_value = config_dict.get("segment_strict", DEFAULT_SEGMENT_STRICT)
        self._segment_strict = bool(segment_strict_value)
        # Store empty_line_interval_rating for use during score parsing
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

        Empty lines are preserved as special EMPTY_LINE markers only if
        empty_line_interval_rating > 0.
        """
        lines: List[List[Note]] = []

        for line in self.score_content.split("\n"):
            stripped = line.strip()

            # Skip comments
            if stripped.startswith("#"):
                continue

            # Empty line - only add if empty_line_interval_rating > 0
            if not stripped:
                # Check if we should preserve empty lines
                empty_line_rating = getattr(self, "_empty_line_interval_rating", 0)
                if empty_line_rating > 0:
                    lines.append([Note(type=NoteType.EMPTY_LINE, keys=[])])
                continue

            # Parse normal line
            notes = self._parse_line(stripped)
            if notes:
                lines.append(notes)

        return lines

    def _parse_line(self, line: str) -> List[Note]:
        """Parse a single line into a list of notes.

        Whitespace characters (space, tab, etc.) are treated as empty notes (rests).
        '/' is a segment separator - if segment_length > 0, pad to that length.
        """
        # First pass: split by '/' and parse each segment
        segments: List[List[Note]] = []
        current_segment: List[Note] = []
        i = 0

        while i < len(line):
            char = line[i]

            if char == "/":
                # End current segment
                if current_segment or segments:  # Don't add empty first segment
                    segments.append(current_segment)
                    current_segment = []
                i += 1
            elif char.isspace():
                # Any whitespace character is an empty note (rest)
                current_segment.append(Note(type=NoteType.SINGLE, keys=[" "]))
                i += 1
            elif char == "(":
                # Chord - find matching closing parenthesis
                end = self._find_matching_bracket(line, i, "(", ")")
                chord_content = line[i + 1 : end]
                # Filter only valid keys
                chord_keys: List[Union[str, Note]] = [
                    k.upper() for k in chord_content if k.upper() in VALID_KEYS
                ]
                if chord_keys:  # Only add if there are valid keys
                    current_segment.append(Note(type=NoteType.CHORD, keys=chord_keys))
                i = end + 1
            elif char == "[":
                # Arpeggio - find matching closing bracket
                end = self._find_matching_bracket(line, i, "[", "]")
                arpeggio_content = line[i + 1 : end]
                arpeggio_notes = self._parse_arpeggio(arpeggio_content)
                if arpeggio_notes:  # Only add if there are valid notes
                    current_segment.append(
                        Note(type=NoteType.ARPEGGIO, keys=arpeggio_notes)
                    )
                i = end + 1
            elif char.upper() in VALID_KEYS:
                # Single note - only if it's a valid key
                single_key: List[Union[str, Note]] = [char.upper()]
                current_segment.append(Note(type=NoteType.SINGLE, keys=single_key))
                i += 1
            else:
                # Skip invalid characters
                i += 1

        # Add the last segment if any
        if current_segment:
            segments.append(current_segment)

        # If no segments (no '/' found), treat entire line as one segment
        if not segments:
            segments = [current_segment] if current_segment else []

        # Second pass: apply segment_length padding/truncation if enabled
        segment_length = self._get_segment_length()
        segment_strict = self._get_segment_strict()
        if segment_length > 0:
            processed_segments: List[List[Note]] = []
            for segment in segments:
                if len(segment) < segment_length:
                    # Pad with empty notes (rests)
                    padding_needed = segment_length - len(segment)
                    processed_segment = (
                        segment
                        + [Note(type=NoteType.SINGLE, keys=[" "])] * padding_needed
                    )
                    processed_segments.append(processed_segment)
                elif len(segment) > segment_length and segment_strict:
                    # Strict mode: truncate to segment_length
                    processed_segments.append(segment[:segment_length])
                else:
                    # Normal mode: keep as is (even if exceeds length)
                    processed_segments.append(segment)
            segments = processed_segments

        # Flatten all segments into a single list of notes
        notes: List[Note] = []
        for segment in segments:
            notes.extend(segment)

        return notes

    def _get_segment_length(self) -> int:
        """Get segment_length from config if available."""
        # This will be called during parsing, need to access from stored config
        return getattr(self, "_segment_length", 0)

    def _get_segment_strict(self) -> bool:
        """Get segment_strict from config if available."""
        return getattr(self, "_segment_strict", False)

    def _parse_arpeggio(self, content: str) -> List[Union[str, Note]]:
        """Parse arpeggio content which may contain nested chords."""
        notes: List[Union[str, Note]] = []
        i = 0

        while i < len(content):
            char = content[i]

            if char == "(":
                # Nested chord within arpeggio
                end = self._find_matching_bracket(content, i, "(", ")")
                chord_content = content[i + 1 : end]
                # Filter only valid keys
                chord_keys: List[Union[str, Note]] = [
                    k.upper() for k in chord_content if k.upper() in VALID_KEYS
                ]
                if chord_keys:  # Only add if there are valid keys
                    notes.append(Note(type=NoteType.CHORD, keys=chord_keys))
                i = end + 1
            elif char.upper() in VALID_KEYS:
                # Single note - only if it's a valid key
                notes.append(char.upper())
                i += 1
            else:
                # Skip invalid characters
                i += 1

        return notes

    def _find_matching_bracket(
        self, text: str, start: int, open_char: str, close_char: str
    ) -> int:
        """Find the index of the matching closing bracket."""
        count = 1
        i = start + 1

        while i < len(text) and count > 0:
            if text[i] == open_char:
                count += 1
            elif text[i] == close_char:
                count -= 1
            i += 1

        return i - 1
