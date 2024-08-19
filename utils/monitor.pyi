from threading import Thread

from Connection import Connection


class Monitor(Thread):
    conn: Connection

    def __init__(self, conn: Connection) -> None:
        super().__init__()
        ...

    def run(self): ...


def replace_all(text: str) -> str: ...


def user_enter_monitor() -> str: ...
