"""Test CLI display without actually playing."""

import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import ScoreParser, NoteType, Note, ParsedScore
from typing import List


def format_score_line(line: List[Note]) -> str:
    """Format a score line as text."""
    result = ""
    for note in line:
        if note.type == NoteType.SINGLE:
            key = note.keys[0]
            assert isinstance(key, str), "SINGLE note key must be string"
            if key == '/':
                result += "/ "
            else:
                result += f"{key} "
        elif note.type == NoteType.CHORD:
            chord_keys = [k for k in note.keys if isinstance(k, str)]
            result += f"({''.join(chord_keys)}) "
        elif note.type == NoteType.ARPEGGIO:
            arp_content = ""
            for key in note.keys:
                if isinstance(key, str):
                    arp_content += key
                else:  # Nested chord
                    nested_chord_keys = [k for k in key.keys if isinstance(k, str)]
                    arp_content += f"({''.join(nested_chord_keys)})"
            result += f"[{arp_content}] "
    return result.rstrip()


def display_score(score: ParsedScore, current_line: int = 0, current_note: int = 0) -> None:
    """Display the full score with highlighting and auto-scroll."""
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')

    print("GIPianoPlayer - CLI Display Test")
    print("=" * 70)
    print(f"Lines: {len(score.lines)}")
    print()

    # Calculate visible window (show lines around current position)
    window_before = 5
    window_after = 10
    start_line = max(0, current_line - window_before)
    end_line = min(len(score.lines), current_line + window_after + 1)

    # Show indicator if there are lines before
    if start_line > 0:
        print(f"    ... ({start_line} lines above) ...")
        print()

    # Display visible lines
    for line_idx in range(start_line, end_line):
        line = score.lines[line_idx]
        line_text = format_score_line(line)
        line_num = f"[{line_idx + 1:3d}] "

        if line_idx < current_line:
            # Already played - gray
            print(f"\033[90m{line_num}{line_text}\033[0m")
        elif line_idx == current_line:
            # Current line - highlight current note
            print(line_num, end='')
            note_idx = 0
            for note in line:
                note_text = ""
                if note.type == NoteType.SINGLE:
                    key = note.keys[0]
                    assert isinstance(key, str), "SINGLE note key must be string"
                    if key == '/':
                        note_text = "/"
                    else:
                        note_text = key
                elif note.type == NoteType.CHORD:
                    chord_keys = [k for k in note.keys if isinstance(k, str)]
                    note_text = f"({''.join(chord_keys)})"
                elif note.type == NoteType.ARPEGGIO:
                    arp_content = ""
                    for key in note.keys:
                        if isinstance(key, str):
                            arp_content += key
                        else:
                            nested_chord_keys = [k for k in key.keys if isinstance(k, str)]
                            arp_content += f"({''.join(nested_chord_keys)})"
                    note_text = f"[{arp_content}]"

                if note_idx < current_note:
                    # Already played - red
                    print(f"\033[91m{note_text}\033[0m ", end='')
                elif note_idx == current_note:
                    # Currently playing - yellow/bold
                    print(f"\033[93m\033[1m{note_text}\033[0m ", end='')
                else:
                    # Not yet played - normal
                    print(f"{note_text} ", end='')

                note_idx += 1
            print()
        else:
            # Not yet played - normal
            print(f"{line_num}{line_text}")

    # Show indicator if there are lines after
    if end_line < len(score.lines):
        print()
        print(f"    ... ({len(score.lines) - end_line} lines below) ...")

    print()
    print("=" * 70)
    progress = (current_line / len(score.lines) * 100) if len(score.lines) > 0 else 0
    print(f"Status: PLAYING | Line {current_line + 1}/{len(score.lines)} | Progress: {progress:.1f}%")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python test_cli_display.py <score_file>")
        sys.exit(1)

    score_file = sys.argv[1]

    # Parse score
    parser = ScoreParser(score_file)
    score = parser.parse()

    print("Testing CLI display with auto-scroll...")
    print("This will simulate playback display without actually playing.")
    print(f"Total lines: {len(score.lines)}")
    print()
    input("Press Enter to start...")

    # Simulate playback - show more lines to demonstrate scrolling
    num_lines_to_show = min(20, len(score.lines))
    for line_idx in range(num_lines_to_show):
        line = score.lines[line_idx]
        for note_idx in range(len(line)):
            display_score(score, line_idx, note_idx)
            time.sleep(0.15)  # Simulate note interval

    print("\nTest complete!")
    print(f"Displayed {num_lines_to_show} lines with auto-scroll.")


if __name__ == '__main__':
    main()
