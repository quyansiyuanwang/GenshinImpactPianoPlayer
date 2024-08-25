import os
import sys
from typing import Dict, Callable

from Connection import Connection

DEFAULT_ARPEGGIO_INTERVAL: float = 0.05
DEFAULT_INTERVAL_RATING: float = 0.15
DEFAULT_SPACE_INTERVAL_RATING: float = 0.5
DEFAULT_HORN_MODE_INTERVAL: float = 0.01
DEFAULT_LINE_INTERVAL_RATING: int = 1

SPACE_FILLS: bool = True
IGNORE_BLANK_LINE: bool = True
MUSIC_START_LINE: int = 1
MUSIC_PATH: str = "music.txt"

FIXED_RELATIVE_PATH: str = r'\keysConfig\keyMap.ini'
EXE_PATH: str = os.path.dirname(sys.executable)

DEFAULT_DESCRIPTION_LAMBDA_MAP: Dict[
    str,
    Callable[[Connection], None]
]

DEFAULT_DESCRIPTION_KEY_MAP: Dict[str, str]
