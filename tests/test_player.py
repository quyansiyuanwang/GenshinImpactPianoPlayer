"""Playback navigation and state tests."""

import time

from src.application.state.state_machine import PlayerState
from src.core.domain.note import Note, NoteType
from src.core.domain.score import ParsedScore
from src.core.player.player import SUSTAIN_RETRIGGER_INTERVAL, Player
from tests.conftest import FakeKeyboard, make_score


class TimingPlayer(Player):
    """Player variant that records waits without sleeping."""

    def __init__(self, score: ParsedScore, keyboard: FakeKeyboard) -> None:
        super().__init__(score, keyboard)
        self.waits: list[float] = []

    def _wait(self, duration: float, _generation: int) -> bool:
        self.waits.append(duration)
        return True


def test_seek_forward_interrupts_wait_and_continues_at_target() -> None:
    keyboard = FakeKeyboard()
    player = Player(make_score([["Q", "W"], ["E", "R"]], interval=2.0), keyboard)

    player.play()
    assert keyboard.wait_for(("tap", ("Q",)))
    started = time.monotonic()
    player.skip_forward_notes()

    assert keyboard.wait_for(("tap", ("E",)))
    assert time.monotonic() - started < 0.5
    player.stop()


def test_seek_backward_while_paused_replays_target_note() -> None:
    keyboard = FakeKeyboard()
    player = Player(make_score([["Q", "W"]], interval=2.0), keyboard)

    player.play()
    assert keyboard.wait_for(("tap", ("Q",)))
    player.pause()
    player.skip_backward_notes()
    player.resume()

    deadline = time.monotonic() + 1.0
    while (
        keyboard.operations.count(("tap", ("Q",))) < 2 and time.monotonic() < deadline
    ):
        time.sleep(0.01)
    assert keyboard.operations.count(("tap", ("Q",))) == 2
    player.stop()


def test_navigation_crosses_lines_and_clamps_at_boundaries() -> None:
    player = Player(make_score([["Q", "W"], ["E"]]), FakeKeyboard())

    player.skip_backward_notes()
    assert player.get_progress() == (0, 2)
    player.skip_forward_notes(2)
    assert player.get_progress() == (1, 2)
    player.skip_backward_line()
    assert player.get_progress() == (0, 2)
    player.skip_forward_line()
    assert player.get_progress() == (1, 2)
    player.skip_forward_notes(100)
    assert player.get_progress() == (2, 2)


def test_seek_releases_sustained_keys() -> None:
    keyboard = FakeKeyboard()
    player = Player(make_score([["Q", "W"]], interval=2.0), keyboard)
    player.toggle_sustain()
    player.play()

    assert keyboard.wait_for(("press", ("Q",)))
    player.skip_forward_notes()
    assert keyboard.wait_for(("release", ("Q",)))
    player.stop()


def test_playback_stops_and_resets_after_last_note() -> None:
    keyboard = FakeKeyboard()
    player = Player(make_score([["Q"]], interval=0.01), keyboard)

    player.play()
    assert keyboard.wait_for(("tap", ("Q",)))
    deadline = time.monotonic() + 1.0
    while player.get_state() != PlayerState.STOPPED and time.monotonic() < deadline:
        time.sleep(0.01)

    assert player.get_state() == PlayerState.STOPPED
    assert player.get_progress() == (0, 1)
    assert keyboard.operations.count(("tap", ("Q",))) == 1


def test_arpeggio_interval_is_inferred_without_a_trailing_wait() -> None:
    keyboard = FakeKeyboard()
    player = TimingPlayer(make_score([["Q"]], interval=0.2), keyboard)
    arpeggio = Note(NoteType.ARPEGGIO, ["X", "N", "A", "G"])
    player.score.lines = [[arpeggio]]
    player._positions = [(0, 0)]

    player._playback_loop()

    assert player.waits == [0.05, 0.05, 0.05]
    assert keyboard.operations == [
        ("tap", ("X",)),
        ("tap", ("N",)),
        ("tap", ("A",)),
        ("tap", ("G",)),
    ]


def test_note_after_arpeggio_waits_a_full_interval() -> None:
    keyboard = FakeKeyboard()
    player = TimingPlayer(make_score([["Q"]], interval=0.2), keyboard)
    arpeggio = Note(NoteType.ARPEGGIO, ["X", "N", "A", "G"])
    player.score.lines = [[arpeggio, Note(NoteType.SINGLE, ["Q"])]]
    player._positions = [(0, 0), (0, 1)]

    player._playback_loop()

    assert player.waits == [0.05, 0.05, 0.05, 0.05]
    assert keyboard.operations == [
        ("tap", ("X",)),
        ("tap", ("N",)),
        ("tap", ("A",)),
        ("tap", ("G",)),
        ("tap", ("Q",)),
    ]


def test_repeated_sustained_key_is_released_before_retriggering() -> None:
    keyboard = FakeKeyboard()
    player = TimingPlayer(make_score([["Q", "Q"]], interval=0.1), keyboard)
    player.toggle_sustain()

    player._playback_loop()

    assert keyboard.operations == [
        ("press", ("Q",)),
        ("release", ("Q",)),
        ("press", ("Q",)),
    ]
    assert player.waits == [0.08, SUSTAIN_RETRIGGER_INTERVAL]


def test_manual_arpeggio_interval_overrides_inferred_timing() -> None:
    keyboard = FakeKeyboard()
    player = TimingPlayer(make_score([["Q"]], interval=0.2), keyboard)
    arpeggio = Note(NoteType.ARPEGGIO, ["X", "N", "A", "G"])

    player.set_arpeggio_interval(0.03)
    assert not player.get_arpeggio_auto()
    assert player._play_note(arpeggio, 0)

    assert player.waits == [0.03, 0.03, 0.03]
    player.set_arpeggio_auto(True)
    assert player.get_arpeggio_auto()
    assert player._get_arpeggio_interval(len(arpeggio.keys)) == 0.05
