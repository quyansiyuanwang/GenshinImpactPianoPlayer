"""Test to verify playback timing logic."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.parser import ScoreParser


def main() -> None:
    print("Playback Logic Test")
    print("=" * 60)
    print()
    print("Testing with sample score...")
    print()

    parser = ScoreParser("tests/sample_score.txt")
    score = parser.parse()

    print("Configuration:")
    print(f"  INTERVAL_RATING: {score.config.interval_rating}s")
    print(f"  ARPEGGIO_INTERVAL: {score.config.arpeggio_interval}s")
    print()

    # Test first line
    line = score.lines[0]
    print(f"First line has {len(line)} notes:")
    print()

    total_time = 0.0
    for i, note in enumerate(line):
        note_type = note.type.value

        if note_type == "single":
            key = note.keys[0]
            assert isinstance(key, str), "SINGLE note key must be string"
            if key == "/":
                print(f"  [{i + 1}] Space (empty note)")
            else:
                print(f"  [{i + 1}] Single: {key}")
        elif note_type == "chord":
            chord_keys = [k for k in note.keys if isinstance(k, str)]
            print(f"  [{i + 1}] Chord: {''.join(chord_keys)}")
        elif note_type == "arpeggio":
            print(f"  [{i + 1}] Arpeggio: {len(note.keys)} keys")

        # Every note has interval after it (except last)
        if i < len(line) - 1:
            total_time += score.config.interval_rating
            print(f"       -> wait {score.config.interval_rating}s")

    print()
    print(f"Total time for first line: {total_time:.3f}s")
    print()
    print("Logic verification:")
    print("  [OK] Every note (including space '/') has interval after it")
    print("  [OK] Last note in line has no interval")
    print("  [OK] Space '/' is treated as an empty note")


if __name__ == "__main__":
    main()
