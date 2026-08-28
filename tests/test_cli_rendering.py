"""CLI display regression tests."""

import curses
from pathlib import Path

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

    def erase(self) -> None:
        self.clear()

    def addstr(self, row: int, _column: int, text: str, *_attributes: int) -> None:
        if row >= 24:
            raise curses.error()
        self.lines.append(text)

    def refresh(self) -> None:
        self.refreshed = True


def _make_cli_with_screen() -> tuple[CLI, LimitedScreen]:
    cli = CLI("D:/scores/繁星、新生，与你.qymusic")
    cli.score = make_score([["Q", "W"], ["E", "R"]])
    cli.player = Player(cli.score, FakeKeyboard())
    cli.display_active = True
    screen = LimitedScreen()
    cli.stdscr = screen
    return cli, screen


def test_display_refreshes_on_small_terminal_with_unicode_file_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli, screen = _make_cli_with_screen()
    monkeypatch.setattr(curses, "color_pair", lambda _number: 0)
    monkeypatch.setattr(curses, "A_BOLD", 0)

    cli._display_score()

    assert screen.refreshed
    assert "GIPianoPlayer - Command Line Interface" in screen.lines
    assert any("????" in line for line in screen.lines)


def test_display_reports_finished_after_natural_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli, screen = _make_cli_with_screen()
    assert cli.player is not None
    monkeypatch.setattr(curses, "color_pair", lambda _number: 0)
    monkeypatch.setattr(curses, "A_BOLD", 0)

    cli.player._playback_completed = True  # set by the player after a full run
    cli._display_score()

    assert any("FINISHED" in line for line in screen.lines)
    assert any("Progress: 100.0%" in line for line in screen.lines)


def test_display_shows_transient_status_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli, screen = _make_cli_with_screen()
    monkeypatch.setattr(curses, "color_pair", lambda _number: 0)
    monkeypatch.setattr(curses, "A_BOLD", 0)

    cli._flash("Configuration saved")

    assert any("Configuration saved" in line for line in screen.lines)


def test_display_lists_parse_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    cli, screen = _make_cli_with_screen()
    assert cli.score is not None
    cli.score.warnings = [
        "line 2: ignored 'O'",
        "line 3: ignored '@'",
        "line 4: ignored '#'",
    ]
    monkeypatch.setattr(curses, "color_pair", lambda _number: 0)
    monkeypatch.setattr(curses, "A_BOLD", 0)

    cli._display_score()

    assert any("3 unknown characters ignored" in line for line in screen.lines)
    assert any("line 2: ignored 'O'" in line for line in screen.lines)


def test_separator_fills_as_playback_progresses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli, screen = _make_cli_with_screen()
    assert cli.player is not None
    monkeypatch.setattr(curses, "color_pair", lambda _number: 0)
    monkeypatch.setattr(curses, "A_BOLD", 0)

    def full_bars() -> int:
        return sum(1 for line in screen.lines if line and set(line) == {"="})

    cli._display_score()
    assert full_bars() == 1  # only the header separator

    cli.player.jump_to_end()
    cli._display_score()
    assert full_bars() == 2  # header separator + completed progress bar


def test_save_config_rounds_float_dust(tmp_path: Path) -> None:
    from src.core.parser.score_parser import ScoreParser

    score_path = tmp_path / "dust.qymusic"
    score_path.write_text("SPEED_MULTIPLIER = 1.0\n---\nQ\n", encoding="utf-8")
    cli = CLI(str(score_path))
    cli.original_content = score_path.read_text(encoding="utf-8")
    cli.score = ScoreParser(str(score_path)).parse()
    cli.player = Player(cli.score, FakeKeyboard())

    # Simulate dust from repeated +0.01 hotkey adjustments
    cli.player.set_speed(1.3000000000000003)
    cli.save_config()

    content = score_path.read_text(encoding="utf-8")
    assert "SPEED_MULTIPLIER = 1.3\n" in content
    assert "0000003" not in content
