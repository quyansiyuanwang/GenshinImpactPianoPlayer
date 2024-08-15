from threading import Thread
from typing import Union, List, Self, Any

ARPEGGIO_INTERVAL: float = 0.07
INTERVAL_RATING: float = 0.15
SPACE_INTERVAL_RATING: float = 0.5
MUSIC_START_LINE: int = 1
HORN_MODE_INTERVAL: float = 0.2
MUSIC_PATH: str = "music.txt"


class Controller:
    last_key: Union[str, None]

    @staticmethod
    def press(syllable: Syllable, display: bool = True) -> None: ...

    @staticmethod
    def release_all() -> None: ...

    @staticmethod
    def delay_press(syllable: Syllable) -> None: ...


class Connection:
    running_flag: bool
    stop_flag: bool
    delay_press: bool
    restart: bool
    adjust_interval: float
    adjust_progress: int
    pg_ad_rating: int

    def __init__(
            self, *,
            running_flag: bool = True,
            stop_flag: bool = True,
            delay_press: bool = False,
            restart: bool = False,
            progress_adjust_rating: int = 1,
            adjust_interval: float = 0,
            adjust_progress: int = 0
    ) -> None: ...


class Syllable:
    words: Union[str, List[Syllable]]
    is_arpeggio: bool
    is_space: bool
    is_multitone: bool
    is_rest: bool

    def __init__(self, word: Union[str, List[Syllable]], is_arpeggio: bool = False) -> None: ...

    @staticmethod
    def analyse(word: str) -> List[Syllable]: ...

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...


Syllables = List[Syllable]


class PianoPlayer:
    syllables: List[Syllable]
    interval: float
    idx: int
    conn: Connection
    interval_changes: float
    pg_ad_rating: int

    def __init__(self, connection: Connection): ...

    @property
    def length(self) -> int: ...

    def add_syllables(self, syllables: Syllables) -> Self: ...

    @property
    def interval_(self) -> float: ...

    @property
    def r_interval(self) -> float: ...

    @interval_.setter
    def interval_(self, value: float) -> None: ...

    @property
    def percentage(self) -> float: ...

    @property
    def current_syllable(self) -> Syllable: ...

    def display_title(self) -> None: ...

    def sleep(self) -> None: ...

    def restart(self) -> None: ...

    def change_args(self) -> None: ...

    def display_music(self, end: int) -> None: ...

    def check_stop(self) -> bool: ...

    def play(self): ...

    def __str__(self) -> str: ...


class FileAnalyzer:
    filename: str
    syllables: List[Syllable]
    content: Union[List[str], None]
    conn: Connection

    def __init__(self, filename: str, connection: Connection) -> None: ...

    def read_content(self) -> Self: ...

    @staticmethod
    def content_analyze(content: str) -> Syllables: ...

    def analyze(self) -> PianoPlayer: ...

    def __str__(self) -> str: ...


class Monitor(Thread):
    conn: Connection

    def __init__(self, conn: Connection) -> None:
        super().__init__()
        ...

    def run(self): ...


def user_enter_monitor() -> str: ...


def load_config() -> None: ...


def display_default_info() -> None: ...


def main(argv: List[Any]) -> None: ...
