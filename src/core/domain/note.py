"""Note domain model."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Union


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

    def __init__(self, type: NoteType, keys: List[Union[str, "Note"]]) -> None:
        """Initialize note.

        Args:
            type: Type of note
            keys: List of keys or nested notes
        """
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

    def is_rest(self) -> bool:
        """Check if this note is a rest (space).

        Returns:
            True if this is a rest note
        """
        return (
            self.type == NoteType.SINGLE
            and len(self.keys) == 1
            and isinstance(self.keys[0], str)
            and self.keys[0] == " "
        )

    def is_empty_line(self) -> bool:
        """Check if this note represents an empty line.

        Returns:
            True if this is an empty line marker
        """
        return self.type == NoteType.EMPTY_LINE

    def get_all_keys(self) -> List[str]:
        """Get all physical keys in this note (flattened).

        Returns:
            List of all key strings
        """
        result: List[str] = []

        def collect_keys(keys: List[Union[str, Note]]) -> None:
            for key in keys:
                if isinstance(key, str):
                    result.append(key)
                else:
                    collect_keys(key.keys)

        collect_keys(self.keys)
        return result
