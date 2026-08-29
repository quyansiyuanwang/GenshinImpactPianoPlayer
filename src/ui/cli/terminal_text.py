"""Unicode-aware text measurement for terminal cells."""

from __future__ import annotations

import unicodedata


def cell_width(text: object) -> int:
    """Return the number of terminal columns occupied by *text*."""
    return sum(_character_width(character) for character in str(text))


def clip_cells(text: object, width: int) -> str:
    """Clip text without splitting a wide or combining character."""
    if width <= 0:
        return ""
    result: list[str] = []
    used = 0
    for character in str(text):
        character_width = _character_width(character)
        if used + character_width > width:
            break
        result.append(character)
        used += character_width
    return "".join(result)


def fit_cells(text: object, width: int) -> str:
    """Clip and right-pad text to exactly *width* terminal columns."""
    clipped = clip_cells(text, width)
    return clipped + " " * max(0, width - cell_width(clipped))


def _character_width(character: str) -> int:
    if not character or unicodedata.combining(character):
        return 0
    category = unicodedata.category(character)
    if category in {"Cc", "Cf", "Cs"}:
        return 0
    return 2 if unicodedata.east_asian_width(character) in {"W", "F"} else 1
