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
LOOP = false

(QWE) / Q [WE] [(QW)E]
```

Supported piano keys are `QWERTYU`, `ASDFGHJ`, and `ZXCVBNM`. A single letter is a note, `(QWE)` is a chord, `[QWE]` is an arpeggio, and `/` is only a visual separator. A literal space is a rest. Characters that are not playable keys are skipped, and the header lists what was ignored with its file line number so typos are easy to spot.

## Hotkeys

| Key | Action |
| --- | --- |
| `F8` | Play or pause |
| `F2` | Quit |
| `Left` / `Right` | Move one pending note backward / forward |
| `Ctrl+Left` / `Ctrl+Right` | Move to the previous / next line |
| `Home` / `End` | Jump to the start / end of the score |
| `Insert` | Toggle looping playback |
| `Delete` | Toggle repeating the current line |
| `+` / `-` | Adjust speed by 0.01x |
| `Ctrl+=` / `Ctrl+-` | Adjust speed by 0.1x |
| `,` / `.` | Adjust note interval |
| `[` / `]` | Adjust manual arpeggio interval |
| `F3` | Toggle automatic arpeggio timing |
| `Up` / `Down` | Adjust line interval |
| `Shift+Up` / `Shift+Down` | Adjust space (rest) interval |
| `Ctrl+Up` / `Ctrl+Down` | Adjust empty line interval |
| `Page Up` / `Page Down` | Adjust segment length |
| `F4` | Toggle strict segment mode |
| `F7` | Toggle sustain |
| `F9` | Save configuration |
| `F5` / `F6` | Reload / reparse the score |

Seeking during playback cancels the current wait, releases sustained keys, and resumes from the selected pending note. At the end of the score, playback stops without replaying the final note; the status line reports `FINISHED` until you seek or play again. Speed changes apply to the current wait immediately.

With loop enabled (`Insert`, persisted as `LOOP`), reaching the end restarts from the first note after a line-sized gap instead of stopping; seeking to the end while looping returns to the start. `Delete` toggles line repeat, a practice aid that replays the current line from its first note every time it ends; it is runtime-only and resets when a new score is loaded.

Empty line interval changes (and segment length or strict mode changes) reparse the score so blank lines are added or removed to match the new setting; the file's configuration header is updated at the same time. Pressing the shifted `+` key works the same as `=` for speed.

Arpeggio timing defaults to automatic: each interval is `INTERVAL_RATING / arpeggio element count`. Press `[` or `]` to switch to manual timing and adjust `ARPEGGIO_INTERVAL`; press `F3` to switch back. The selected mode is saved as `ARPEGGIO_AUTO`. Both modes wait only between arpeggio elements; after the final element, the next score event waits for the regular `INTERVAL_RATING`.
