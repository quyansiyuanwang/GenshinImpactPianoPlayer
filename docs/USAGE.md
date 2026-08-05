# Usage

Run the player with a score file:

```powershell
uv run python main.py path\to\score.txt
```

Run the terminal as Administrator when global hotkeys or keyboard output do not work. Keep the target application focused while playing.

## Score Format

Configuration lines appear before note content:

```text
version = 1.0
ARPEGGIO_INTERVAL = 0.05
ARPEGGIO_AUTO = true
INTERVAL_RATING = 0.2
SPACE_INTERVAL_RATING = 1.0
LINE_INTERVAL_RATING = 0.0

(QWE) / Q [WE] [(QW)E]
```

Supported piano keys are `QWERTYU`, `ASDFGHJ`, and `ZXCVBNM`. A single letter is a note, `(QWE)` is a chord, `[QWE]` is an arpeggio, and `/` is only a visual separator. A literal space is a rest.

## Hotkeys

| Key | Action |
| --- | --- |
| `F8` | Play or pause |
| `F2` | Quit |
| `Left` / `Right` | Move one pending note backward / forward |
| `Ctrl+Left` / `Ctrl+Right` | Move to the previous / next line |
| `+` / `-` | Adjust speed by 0.01x |
| `Ctrl+=` / `Ctrl+-` | Adjust speed by 0.1x |
| `,` / `.` | Adjust note interval |
| `[` / `]` | Adjust manual arpeggio interval |
| `F3` | Toggle automatic arpeggio timing |
| `Up` / `Down` | Adjust line interval |
| `Page Up` / `Page Down` | Adjust segment length |
| `F4` | Toggle strict segment mode |
| `F7` | Toggle sustain |
| `F9` | Save configuration |
| `F5` / `F6` | Reload / reparse the score |

Seeking during playback cancels the current wait, releases sustained keys, and resumes from the selected pending note. At the end of the score, playback stops without replaying the final note.

Arpeggio timing defaults to automatic: each interval is `INTERVAL_RATING / arpeggio element count`. Press `[` or `]` to switch to manual timing and adjust `ARPEGGIO_INTERVAL`; press `F3` to switch back. The selected mode is saved as `ARPEGGIO_AUTO`. Both modes wait only between arpeggio elements, with no extra delay after the final element.
