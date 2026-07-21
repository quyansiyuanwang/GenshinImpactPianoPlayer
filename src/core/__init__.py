"""Core domain models and business logic for GIPianoPlayer.

Import from specific modules instead of from this __init__.py to avoid circular imports.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.domain.note import Note, NoteType
    from src.core.domain.score import ParsedScore
    from src.core.domain.config import PlayConfig
    from src.core.parser.score_parser import ScoreParser
    from src.core.keyboard.controller import KeyboardController
    from src.core.player.player import Player

__all__ = [
    "Note",
    "NoteType",
    "ParsedScore",
    "PlayConfig",
    "ScoreParser",
    "KeyboardController",
    "Player",
]


def __getattr__(name: str) -> Any:
    """Lazy import to avoid circular dependencies."""
    if name == "Note" or name == "NoteType":
        from src.core.domain.note import Note, NoteType

        return Note if name == "Note" else NoteType
    elif name == "ParsedScore":
        from src.core.domain.score import ParsedScore

        return ParsedScore
    elif name == "PlayConfig":
        from src.core.domain.config import PlayConfig

        return PlayConfig
    elif name == "ScoreParser":
        from src.core.parser.score_parser import ScoreParser

        return ScoreParser
    elif name == "KeyboardController":
        from src.core.keyboard.controller import KeyboardController

        return KeyboardController
    elif name == "Player":
        from src.core.player.player import Player

        return Player
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
