"""Tests for the player engine."""

import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import ScoreParser
from src.player import Player, PlayerState
from src.keyboard_controller import KeyboardController


def test_player_initialization():
    """Test player initialization."""
    parser = ScoreParser('tests/sample_score.txt')
    score = parser.parse()
    keyboard = KeyboardController()
    player = Player(score, keyboard)

    assert player.get_state() == PlayerState.STOPPED
    assert player.get_progress() == (0, len(score.lines))
    print("✓ Player initialization test passed")


def test_player_state_transitions():
    """Test player state transitions."""
    parser = ScoreParser('tests/sample_score.txt')
    score = parser.parse()
    keyboard = KeyboardController()
    player = Player(score, keyboard)

    # Start playing
    player.play()
    time.sleep(0.1)
    assert player.get_state() == PlayerState.PLAYING
    print("✓ Play state test passed")

    # Pause
    player.pause()
    time.sleep(0.1)
    assert player.get_state() == PlayerState.PAUSED
    print("✓ Pause state test passed")

    # Resume
    player.resume()
    time.sleep(0.1)
    assert player.get_state() == PlayerState.PLAYING
    print("✓ Resume state test passed")

    # Stop
    player.stop()
    time.sleep(0.1)
    assert player.get_state() == PlayerState.STOPPED
    print("✓ Stop state test passed")


def test_player_speed_adjustment():
    """Test speed adjustment."""
    parser = ScoreParser('tests/sample_score.txt')
    score = parser.parse()
    keyboard = KeyboardController()
    player = Player(score, keyboard)

    player.set_speed(2.0)
    assert player._speed_multiplier == 2.0

    player.set_speed(0.5)
    assert player._speed_multiplier == 0.5

    print("✓ Speed adjustment test passed")


def test_player_parameter_adjustment():
    """Test parameter adjustments."""
    parser = ScoreParser('tests/sample_score.txt')
    score = parser.parse()
    keyboard = KeyboardController()
    player = Player(score, keyboard)

    player.set_arpeggio_interval(0.1)
    assert player._arpeggio_interval == 0.1

    player.set_space_interval_rating(2.0)
    assert player._space_interval_rating == 2.0

    player.set_line_interval_rating(1.5)
    assert player._line_interval_rating == 1.5

    print("✓ Parameter adjustment test passed")


if __name__ == '__main__':
    print("Running player tests...")
    print()

    test_player_initialization()
    test_player_state_transitions()
    test_player_speed_adjustment()
    test_player_parameter_adjustment()

    print()
    print("All tests passed!")
