"""Debug script to test playback timing."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.parser import ScoreParser


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python test_timing.py <score_file>")
        sys.exit(1)

    score_file = sys.argv[1]

    print("Timing Debug Mode")
    print("=" * 60)

    # Parse score
    parser = ScoreParser(score_file)
    score = parser.parse()

    print(f"Score: {score_file}")
    print(f"Total lines: {len(score.lines)}")
    print("\nConfiguration:")
    print(f"  ARPEGGIO_INTERVAL: {score.config.arpeggio_interval}s")
    print(f"  INTERVAL_RATING: {score.config.interval_rating}s")
    print(f"  SPACE_INTERVAL_RATING: {score.config.space_interval_rating}x")
    print(f"  LINE_INTERVAL_RATING: {score.config.line_interval_rating}x")
    print()

    # Analyze first few lines
    print("First 3 lines analysis:")
    print("-" * 60)

    for line_idx in range(min(3, len(score.lines))):
        line = score.lines[line_idx]
        print(f"\nLine {line_idx + 1}: {len(line)} notes")

        estimated_time = 0.0
        for note_idx, note in enumerate(line):
            note_desc = ""
            note_time = 0.0

            if note.type.value == "single":
                key = note.keys[0]
                assert isinstance(key, str), "SINGLE note key must be string"
                if key == "/":
                    note_desc = "SPACE"
                    note_time = (
                        score.config.space_interval_rating
                        * score.config.interval_rating
                    )
                else:
                    note_desc = f"Single: {key}"
                    note_time = (
                        score.config.interval_rating if note_idx < len(line) - 1 else 0
                    )
            elif note.type.value == "chord":
                chord_keys = [k for k in note.keys if isinstance(k, str)]
                note_desc = f"Chord: {''.join(chord_keys)}"
                note_time = 0.005  # Chord internal delay
            elif note.type.value == "arpeggio":
                num_keys = len(note.keys)
                note_desc = f"Arpeggio: {num_keys} keys"
                note_time = (num_keys - 1) * score.config.arpeggio_interval

            estimated_time += note_time
            print(f"  [{note_idx + 1}] {note_desc:20s} +{note_time:.3f}s")

        # Line interval
        if line_idx < len(score.lines) - 1:
            line_interval = (
                score.config.line_interval_rating * score.config.interval_rating
            )
            estimated_time += line_interval
            if line_interval > 0:
                print(f"  [END] Line interval: +{line_interval:.3f}s")

        print(f"  Total estimated time: {estimated_time:.3f}s")

    print("\n" + "=" * 60)
    print("Recommendations:")
    print()

    # Calculate notes per second
    total_notes = sum(len(line) for line in score.lines)
    avg_notes_per_line = total_notes / len(score.lines)

    print(f"Total notes: {total_notes}")
    print(f"Average notes per line: {avg_notes_per_line:.1f}")
    print()

    if score.config.interval_rating > 0.05:
        print(f"⚠ INTERVAL_RATING ({score.config.interval_rating}s) might be too high")
        print("  Recommended: 0.01 - 0.05s for smooth playback")
    else:
        print(f"✓ INTERVAL_RATING ({score.config.interval_rating}s) looks good")

    if score.config.arpeggio_interval > 0.03:
        print(
            f"⚠ ARPEGGIO_INTERVAL ({score.config.arpeggio_interval}s) might be too high"
        )
        print("  Recommended: 0.01 - 0.03s for fast arpeggios")
    else:
        print(f"✓ ARPEGGIO_INTERVAL ({score.config.arpeggio_interval}s) looks good")

    print()
    print("Suggested optimized settings:")
    print("  INTERVAL_RATING=0.02")
    print("  ARPEGGIO_INTERVAL=0.02")
    print(f"  SPACE_INTERVAL_RATING={score.config.space_interval_rating}")
    print(f"  LINE_INTERVAL_RATING={score.config.line_interval_rating}")


if __name__ == "__main__":
    main()
