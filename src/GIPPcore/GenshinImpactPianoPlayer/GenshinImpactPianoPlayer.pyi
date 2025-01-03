from typing import Self, List, Optional, Union

from ..Connection import Connection
from ..MusicParse import Syllable
from ..MusicParse import Action

Syllables = List[Syllable]


class PianoPlayer:
    syllables: Syllables
    idx: int
    conn: Connection
    interval_changes: float
    progress_adjust_rating: int

    def __init__(self, syllables: Optional[Syllables] = None, *, connection: Connection): ...

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
    def current_syllable(self) -> Union[Action, Syllable]: ...

    def display_title(self) -> None: ...

    def sleep(self) -> None: ...

    def config_reset(self) -> None: ...

    def restart(self) -> None: ...

    def change_args(self) -> None: ...

    @staticmethod
    def clear() -> None: ...

    def display_music(self, end: int) -> None: ...

    def check_stop(self) -> bool: ...

    def play(self): ...

    def __str__(self) -> str: ...


def clear_and_DDI() -> None: ...


def display_default_info() -> None: ...
