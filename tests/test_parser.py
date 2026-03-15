"""Tests for the score parser."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.parser import ScoreParser, NoteType


def test_parse_config() -> None:
    """Test configuration parsing."""
    parser = ScoreParser("tests/sample_score.txt")
    score = parser.parse()

    assert score.config.version == 1.0
    assert score.config.arpeggio_interval == 0.05
    assert score.config.interval_rating == 0.2
    assert score.config.space_interval_rating == 1.0
    assert score.config.line_interval_rating == 0.0
    print("[OK] Config parsing test passed")


def test_parse_single_note() -> None:
    """Test single note parsing."""
    parser = ScoreParser("tests/sample_score.txt")
    score = parser.parse()

    # Find a line with single notes
    for line in score.lines:
        for note in line:
            if note.type == NoteType.SINGLE and note.keys[0] != "/":
                assert len(note.keys) == 1
                key = note.keys[0]
                assert isinstance(key, str), "SINGLE note key must be string"
                assert key in "QWERTYUASDFGHJZXCVBNM"
                print(f"[OK] Single note test passed: {key}")
                return


def test_parse_chord() -> None:
    """Test chord parsing."""
    parser = ScoreParser("tests/sample_score.txt")
    score = parser.parse()

    # First note should be a chord (VAH)
    first_note = score.lines[0][0]
    assert first_note.type == NoteType.CHORD
    chord_keys = {k for k in first_note.keys if isinstance(k, str)}
    assert chord_keys == {"V", "A", "H"}
    print(f"[OK] Chord test passed: {first_note.keys}")


def test_parse_space_marker() -> None:
    """Test space marker parsing."""
    parser = ScoreParser("tests/sample_score.txt")
    score = parser.parse()

    # Find a space marker
    for line in score.lines:
        for note in line:
            if note.type == NoteType.SINGLE and note.keys[0] == "/":
                print("[OK] Space marker test passed")
                return


def test_total_lines() -> None:
    """Test total number of lines parsed."""
    parser = ScoreParser("tests/sample_score.txt")
    score = parser.parse()

    assert len(score.lines) > 0
    print(f"[OK] Total lines test passed: {len(score.lines)} lines")


def test_invalid_keys_filtered() -> None:
    """Test that invalid keys are filtered out."""
    parser = ScoreParser("tests/sample_score.txt")
    score = parser.parse()

    # Check that all keys are valid
    valid_keys = set("QWERTYUASDFGHJZXCVBNM/")
    for line in score.lines:
        for note in line:
            for key in note.keys:
                if isinstance(key, str):
                    assert key in valid_keys, f"Invalid key found: {key}"
    print("[OK] Invalid keys filter test passed")


if __name__ == "__main__":
    print("Running parser tests...")
    print()

    test_parse_config()
    test_parse_single_note()
    test_parse_chord()
    test_parse_space_marker()
    test_total_lines()
    test_invalid_keys_filtered()

    print()
    print("All tests passed!")
