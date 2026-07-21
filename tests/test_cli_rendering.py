"""CLI display regression tests."""

import curses

import pytest

from src.cli import CLI
from src.core.player.player import Player
from tests.conftest import FakeKeyboard, make_score


class LimitedScreen:
    """Minimal curses screen that rejects writes past a 24-row terminal."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.refreshed = False

    def getmaxyx(self) -> tuple[int, int]:
        return (24, 80)

    def clear(self) -> None:
        self.lines.clear()

    def addstr(self, row: int, _column: int, text: str, *_attributes: int) -> None:
        if row >= 24:
            raise curses.error()
        self.lines.append(text)

    def refresh(self) -> None:
        self.refreshed = True


def test_display_refreshes_on_small_terminal_with_unicode_file_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = CLI("D:/scores/繁星、新生，与你.qymusic")
    cli.score = make_score([["Q", "W"], ["E", "R"]])
    cli.player = Player(cli.score, FakeKeyboard())
    cli.display_active = True
    screen = LimitedScreen()
    cli.stdscr = screen
    monkeypatch.setattr(curses, "color_pair", lambda _number: 0)
    monkeypatch.setattr(curses, "A_BOLD", 0)

    cli._display_score()

    assert screen.refreshed
    assert "GIPianoPlayer - Command Line Interface" in screen.lines
    assert any("????" in line for line in screen.lines)
