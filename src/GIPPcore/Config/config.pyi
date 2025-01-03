from typing import Tuple


class Config:
    PLAYER_KEYS: Tuple[str, str, str, str, str, str, str]

    PLAYER_INTERVAL: float
    ARPEGGIO_INTERVAL: float
    INTERVAL_RATING: float
    SPACE_INTERVAL_RATING: float
    HORN_MODE_INTERVAL: float
    LINE_INTERVAL_RATING: int

    SPACE_FILLS: bool
    STRICT_LIMITED: bool
    MUSIC_START_LINE: int
    MUSIC_PATH: str
