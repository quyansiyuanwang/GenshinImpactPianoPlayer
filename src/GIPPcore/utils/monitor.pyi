from threading import Thread

from src.GIPPcore.Connection import Connection
from src.GIPPcore.ShortcutKeyManager import ShortcutKeyManager


class Monitor(Thread):
    conn: Connection
    shortcut_key_manager: ShortcutKeyManager

    def __init__(self, conn: Connection, shortcut_key_manager: ShortcutKeyManager) -> None:
        super().__init__()
        ...

    def run(self) -> None: ...

    def check_event(self) -> None: ...


def replace_all(text: str) -> str: ...


def user_enter_monitor() -> str: ...
