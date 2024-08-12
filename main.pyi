from threading import Thread
from typing import Union, List, Self, Iterable, Any

ARPEGGIO_INTERVAL: float = 0.07
INTERVAL_RATING: float = 0.15
SPACE_INTERVAL_RATING:float = 0.5
MUSIC_START_LINE: int = 1
MUSIC_PATH: str = "music.txt"


class Controller:
    @staticmethod
    def press(key: str, is_arpeggio: bool = False) -> None: ...


class Flag:
    running_flag: bool
    stop_flag: bool
    adjust_interval: float

    def __init__(self) -> None: ...


class Syllable:
    word: Union[str, None]
    is_arpeggio: bool

    def __init__(self, word: str, is_arpeggio: bool = False) -> None: ...

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...


Syllables = Iterable[Syllable]


class PianoPlayer:
    syllables: List[Syllable]
    interval: float

    def __init__(self): ...

    def add_syllables(self, syllables: Syllables) -> Self: ...

    def play(self, flag: Flag): ...

    def __str__(self) -> str: ...


class FileAnalyzer:
    filename: str
    syllables: List[Syllable]
    content: Union[List[str], None]

    def __init__(self, filename: str) -> None: ...

    def read_content(self) -> Self: ...

    @staticmethod
    def content_analyze(content: str) -> Syllables: ...

    def analyze(self) -> PianoPlayer: ...

    def __str__(self) -> str: ...


class Monitor(Thread):
    flag: Flag

    def __init__(self, flag: Flag) -> None:
        super().__init__()
        ...

    def run(self): ...


def user_enter_monitor() -> str: ...


def load_config() -> None: ...


def main(argv: List[Any]) -> None: ...
