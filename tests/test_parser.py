"""Score parser tests."""

from pathlib import Path

from src.core.domain.note import NoteType
from src.core.parser.score_parser import ScoreParser


SAMPLE_SCORE = Path(__file__).with_name("sample_score.txt")


def test_parses_score_configuration_and_chord() -> None:
    score = ScoreParser(str(SAMPLE_SCORE)).parse()

    assert score.config.version == 1.0
    assert score.config.arpeggio_interval == 0.05
    assert score.config.arpeggio_auto
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


def test_parser_reads_manual_arpeggio_mode(tmp_path: Path) -> None:
    score_path = tmp_path / "manual_arpeggio.qymusic"
    score_path.write_text("ARPEGGIO_AUTO = false\n[QWE]\n", encoding="utf-8")

    score = ScoreParser(str(score_path)).parse()

    assert not score.config.arpeggio_auto
