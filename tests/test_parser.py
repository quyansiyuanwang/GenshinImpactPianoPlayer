"""Score parser tests."""

from pathlib import Path

from src.core.domain.note import NoteType
from src.core.parser.score_parser import ScoreParser


SAMPLE_SCORE = Path(__file__).with_name("sample_score.txt")


def test_parses_score_configuration_and_chord() -> None:
    score = ScoreParser(str(SAMPLE_SCORE)).parse()

    assert score.config.version == 1.0
    assert score.config.arpeggio_interval == 0.05
    assert score.lines[0][0].type == NoteType.CHORD
    assert {key for key in score.lines[0][0].keys if isinstance(key, str)} == {
        "V",
        "A",
        "H",
    }


def test_parsed_keys_are_supported_or_rests() -> None:
    score = ScoreParser(str(SAMPLE_SCORE)).parse()
    valid_keys = set("QWERTYUASDFGHJZXCVBNM ")

    assert all(
        key in valid_keys
        for line in score.lines
        for note in line
        for key in note.keys
        if isinstance(key, str)
    )
