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


def test_segment_strict_truncates_each_slash_separated_segment(
    tmp_path: Path,
) -> None:
    score_path = tmp_path / "segment_strict.qymusic"
    score_path.write_text(
        "SEGMENT_LENGTH = 4\n"
        "SEGMENT_STRICT = true\n"
        "---\n"
        "(CNAH)H(NE)E /(NADE)W(NW)(CW) /\n",
        encoding="utf-8",
    )

    score = ScoreParser(str(score_path)).parse()

    assert score.config.segment_length == 4
    assert score.config.segment_strict
    # '/' marks a segment boundary: strict mode truncates each segment to 4
    # notes independently, so the flattened line keeps 4 notes per segment.
    assert len(score.lines[0]) == 8
    first_segment_keys = [note.keys for note in score.lines[0][:4]]
    assert first_segment_keys == [["C", "N", "A", "H"], ["H"], ["N", "E"], ["E"]]
    second_segment_keys = [note.keys for note in score.lines[0][4:8]]
    assert second_segment_keys == [
        ["N", "A", "D", "E"],
        ["W"],
        ["N", "W"],
        ["C", "W"],
    ]


def test_segment_strict_pads_short_segments(tmp_path: Path) -> None:
    score_path = tmp_path / "segment_pad.qymusic"
    score_path.write_text(
        "SEGMENT_LENGTH = 4\nSEGMENT_STRICT = true\n---\nQW /E\n",
        encoding="utf-8",
    )

    score = ScoreParser(str(score_path)).parse()

    assert len(score.lines[0]) == 8
    assert [note.keys for note in score.lines[0][2:4]] == [[" "], [" "]]
    assert [note.keys for note in score.lines[0][5:8]] == [[" "], [" "], [" "]]
