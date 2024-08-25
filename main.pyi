from typing import Union, List, Any, Dict, Literal

from Connection import Connection
from GenshinImpactPianoPlayer import PianoPlayer
from ShortcutKeyManager import ShortcutKeyManager
from utils import Monitor


def load_config() -> None: ...


def load_shortcut_keys() -> ShortcutKeyManager: ...


def load_all() -> Dict[
    Literal['music', 'connection', 'monitor'],
    Union[PianoPlayer, Connection, Monitor]
]: ...


def play(music: PianoPlayer, connection: Connection) -> None: ...


def main(argv: List[Any]) -> None: ...
