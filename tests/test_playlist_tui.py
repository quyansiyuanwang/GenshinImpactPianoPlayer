"""Playlist focus and terminal input behavior."""

import curses
from pathlib import Path

from src.application.events import InputEvent, KeyCode
from src.application.playlist import PlaylistEntry
from src.cli import CLI
from src.ui.cli.input.adapters import CursesInputAdapter


class InputScreen:
    def __init__(self, value: int) -> None:
        self.value = value

    def getch(self) -> int:
        return self.value

    def getmaxyx(self) -> tuple[int, int]:
        return 24, 80


def key(code: KeyCode) -> InputEvent:
    return InputEvent(InputEvent.character("x").kind, code)


def test_curses_adapter_normalizes_tab_and_navigation() -> None:
    assert CursesInputAdapter(InputScreen(9)).read_event().key == KeyCode.TAB
    assert (
        CursesInputAdapter(InputScreen(curses.KEY_DOWN)).read_event().key
        == KeyCode.DOWN
    )


def test_tab_focus_enables_playlist_cursor_navigation(tmp_path: Path) -> None:
    cli = CLI("score.txt")
    for name in ("one.txt", "two.txt", "three.txt"):
        cli.playlist.add(PlaylistEntry.from_path(tmp_path / name))

    assert cli.handle_playlist_event(key(KeyCode.TAB))
    assert cli.playlist_focus
    assert cli.handle_playlist_event(key(KeyCode.DOWN))
    assert cli.playlist.visible_index == 1
    assert cli.handle_playlist_event(key(KeyCode.END))
    assert cli.playlist.visible_index == 2
    assert cli.handle_playlist_event(key(KeyCode.HOME))
    assert cli.playlist.visible_index == 0


def test_playlist_focus_reserves_global_navigation() -> None:
    cli = CLI("score.txt")
    cli.playlist_focus = True
    result = cli._dispatch_global_event(key(KeyCode.DOWN))
    assert result is not None
    assert result.success
