# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GIPianoPlayer is a Python application that reads specially formatted text files (musical scores) and simulates keyboard input to "play" piano in games or applications. It supports single notes, chords, arpeggios, and sustain mode.

## Running the Application

```bash
# CLI mode (only mode available)
python main.py tests/sample_score.txt

# The application requires keyboard library with admin/root privileges for hotkeys
```

## Architecture

### Core Components

**Parser (`src/parser.py`)**
- Uses recursive descent parsing for nested brackets (chords and arpeggios)
- Parses configuration from file header (version, intervals, segment_length, etc.)
- Handles segment padding: when `segment_length > 0`, pads segments (delimited by `/`) to N notes with empty notes (rests)
- Stores `_segment_length` during config parsing for use in line parsing
- Only recognizes valid keys: `QWERTYUASDFGHJZXCVBNM` (21 keys total)

**Player (`src/player.py`)**
- Multi-threaded playback engine using `Thread`, `Event` for control
- Sustain mode: holds keys until next non-rest note (releases on pause/stop/quit)
- Adds 20ms delay after releasing sustained keys to ensure game/software registration
- Real-time parameter adjustment during playback (speed, intervals, segment_length)
- Progress callback system for UI updates

**Keyboard Controller (`src/keyboard_controller.py`)**
- Prefers `keyboard` library (raw key events, better for games)
- Falls back to `pynput` if `keyboard` unavailable
- Provides: `press_key()`, `release_key()`, `tap_key()`, `press_keys_simultaneously()`

**CLI (`src/cli.py`)**
- Uses `curses` library (windows-curses on Windows) for terminal UI
- Double-buffered rendering to eliminate flickering
- Dynamic viewport calculation based on terminal height
- Displays score with color coding: cyan (played), red (current line played), yellow (current note)
- Refresh rate: 24 FPS (0.042s interval)

### Configuration System

**Default values in `src/constants.py`:**
- `DEFAULT_VERSION = 1.0`
- `DEFAULT_SPEED_MULTIPLIER = 1.0`
- `DEFAULT_ARPEGGIO_INTERVAL = 0.05`
- `DEFAULT_INTERVAL_RATING = 0.2`
- `DEFAULT_LINE_INTERVAL_RATING = 1.0`
- `DEFAULT_SEGMENT_LENGTH = 0`

**Hotkeys (defined in `src/constants.py`):**
- F8: Play/Pause
- F2: Quit
- F5: Reload (re-read file from disk)
- F6: Reparse (reparse with current config, applies new segment_length)
- F7: Toggle sustain mode
- F9: Save config to file
- +/-: Speed adjustment
- [/]: Arpeggio interval
- ,/.: Note interval
- Up/Down: Line interval (notes between lines)
- PgUp/PgDn: Segment length
- Left/Right: Skip 1 note
- Ctrl+Left/Right: Skip 1 line

### Score File Format

**Configuration section (optional):**
```
version = 1.0
SPEED_MULTIPLIER = 1.0
ARPEGGIO_INTERVAL = 0.05
INTERVAL_RATING = 0.2
LINE_INTERVAL_RATING = 1.0
SEGMENT_LENGTH = 4
---
```

**Score notation:**
- Single note: `Q` `W` `E`
- Chord (simultaneous): `(QWE)`
- Arpeggio (rapid succession): `[QWE]`
- Nested: `[(QW)E]` - chord QW then E in arpeggio
- Rest (empty note): space character (occupies one note position)
- Segment separator: `/` (visual only, ignored unless segment_length > 0)

**Important parsing rules:**
- Space is a rest (empty note), not ignored
- `/` is segment separator; if `segment_length > 0`, segments are padded to N notes with rests
- Every note (including rests) has `interval_rating` delay after it (except last in line)
- Line breaks add `line_interval_rating` empty notes between lines

### Sustain Mode

When enabled (F7):
- Keys are held down until next non-rest note
- Releases all keys on pause/stop/quit
- 20ms delay after releasing keys for game registration
- In arpeggios: each note releases previous note in that arpeggio

### UI Layout Calculation

CLI dynamically calculates footer size:
```python
footer_lines = 2 (blank + separator)
             + 2 (status + blank)
             + 2 (config title + separator)
             + len(config_lines)  # dynamic based on config items
             + 1 (blank after config)
             + 3 (control lines if keyboard available)
```

Score viewport adjusts based on `height - header_lines - footer_lines`.

## Key Implementation Details

1. **Segment padding logic**: Parser splits by `/`, pads each segment to `segment_length` with rest notes if enabled
2. **Sustain key release timing**: Always add 20ms delay after releasing to prevent input loss
3. **Curses color pairs**: 1=cyan (played), 2=red (current line played), 3=yellow (current note)
4. **Config persistence**: F9 saves current runtime config back to score file, F6 reparses with new config
5. **Thread safety**: Player uses `Event` objects for pause/stop control, releases sustained keys on state changes

## Dependencies

- `keyboard>=0.13.5` - Global hotkeys and raw key events (requires admin/root)
- `pynput>=1.7.6` - Fallback keyboard simulation
- `windows-curses>=2.4.1` - Terminal UI on Windows (curses on Unix)

## Common Pitfalls

- Don't forget to release sustained keys on pause/stop/quit
- Always add delay after releasing keys in sustain mode
- Segment padding happens in parser, not player
- Footer line count must be dynamically calculated based on config items
- Space character is a rest note, not whitespace to ignore
