"""Command-line interface for GIPianoPlayer."""

import time
import os
import curses
import keyboard
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.core.parser.score_parser import ScoreParser, NoteType, ParsedScore, Note
from src.core.player.player import Player
from src.application.state.state_machine import PlayerState as PSM_State
from src.core.keyboard.controller import KeyboardController
from src.application.config.constants import (
    DEFAULT_HOTKEYS,
    SKIP_SMALL,
    SKIP_LARGE,
    DISPLAY_REFRESH_RATE,
)


class CLI:
    """Command-line interface with keyboard shortcuts."""

    def __init__(self, file_path: str, hotkeys: Optional[Dict[str, str]] = None):
        self.file_path = file_path
        self.player: Optional[Player] = None
        self.running = False
        self.score: Optional[ParsedScore] = None
        self.display_active = False
        self.last_display_time = 0.0  # float for time.time()
        self.original_content = ""
        self.stdscr: Any | None = None  # curses screen object
        self._failed_hotkeys: list[
            tuple[str, str]
        ] = []  # Track failed hotkey registrations
        self._message = ""  # Transient status message shown on the status line
        self._message_until = 0.0  # time.time() after which the message hides

        # Use custom hotkeys or defaults
        self.hotkeys = hotkeys if hotkeys is not None else DEFAULT_HOTKEYS.copy()

    def _flash(self, message: str, duration: float = 2.5) -> None:
        """Show a transient status message on the status line."""
        self._message = message
        self._message_until = time.time() + duration
        self._display_score()

    def _format_score_line(self, line: List[Note]) -> str:
        """Format a score line as text, preserving visual separators."""
        # Check if this is an empty line
        if len(line) == 1 and line[0].type == NoteType.EMPTY_LINE:
            # Only show [Empty Line] if interval > 0
            display_empty = (
                self.player._empty_line_interval_rating > 0 if self.player else False
            )
            return "[Empty Line] " if display_empty else ""

        result = ""

        for note in line:
            if note.type == NoteType.SINGLE:
                if note.keys[0] == " ":
                    # Space is a rest
                    result += "_ "
                else:
                    result += f"{note.keys[0]} "
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

    def _display_score(self) -> None:
        """Display the full score with current position highlighted using curses."""
        if not self.display_active or not self.stdscr:
            return

        try:
            # Get terminal size (recalculate every time for real-time adaptation)
            height, width = self.stdscr.getmaxyx()

            # Erase (not clear) to avoid full-repaint flicker on fast refreshes
            self.stdscr.erase()

            if not self.score:
                self.stdscr.addstr(0, 0, "No score loaded.")
                self.stdscr.refresh()
                return

            # Get current position
            current_line, total_lines = (
                self.player.get_progress()
                if self.player
                else (0, len(self.score.lines))
            )
            current_note = self.player.get_position()[1] if self.player else 0

            separator_width = min(width - 1, 100)

            # Build config lines to get actual count
            config_lines: List[str] = []
            if self.player:
                speed = self.player._speed_multiplier
                interval = self.player._interval_rating
                arpeggio_interval = self.player._arpeggio_interval
                arpeggio_auto = self.player.get_arpeggio_auto()
                line_interval = self.player._line_interval_rating
                space_interval = self.player._space_interval_rating
                empty_line_interval = self.player._empty_line_interval_rating
                segment_length = self.player._segment_length
                segment_strict = self.player.get_segment_strict()
                sustain_enabled = self.player.get_sustain_enabled()

                config_lines.append(
                    f"  Speed: {speed:.2f}x          [+/- or Ctrl+ +/-] Adjust speed"
                )
                arpeggio_mode = (
                    "automatic (note interval / arpeggio note count)"
                    if arpeggio_auto
                    else f"manual ({arpeggio_interval:.3f}s)"
                )
                config_lines.append(
                    f"  Arpeggio: {arpeggio_mode}  [[/]] Manual | [{self.hotkeys['toggle_arpeggio_auto']}] Auto"
                )
                config_lines.append(
                    f"  Note Interval: {interval:.3f}s       [</> or ,/.] Adjust interval"
                )
                config_lines.append(
                    f"  Line Interval: {line_interval:.0f} notes  [Up/Down] Adjust line"
                )
                config_lines.append(
                    f"  Space Interval: {space_interval:.1f}x     [Shift+Up/Down] Adjust space"
                )
                config_lines.append(
                    f"  Empty Line: {empty_line_interval:.0f} notes     [Ctrl+Up/Down] Adjust empty line"
                )
                segment_status = (
                    f"{segment_length} notes" if segment_length > 0 else "Disabled"
                )
                strict_indicator = (
                    " (Strict)" if segment_strict and segment_length > 0 else ""
                )
                config_lines.append(
                    f"  Segment Length: {segment_status}{strict_indicator}  [PgUp/PgDn] Adjust | [{self.hotkeys['toggle_segment_strict']}] Toggle Strict"
                )
                sustain_status = "ON" if sustain_enabled else "OFF"
                config_lines.append(
                    f"  Sustain Mode: {sustain_status}        [{self.hotkeys['toggle_sustain']}] Toggle"
                )

            # Calculate footer size
            footer_lines = 0
            footer_lines += 2  # blank + separator
            footer_lines += 2  # status + blank
            footer_lines += 2  # config title + separator
            footer_lines += len(config_lines)  # actual config items
            footer_lines += 1  # blank after config
            if keyboard is not None:
                footer_lines += 3  # control lines (now 3 lines instead of 2)
                if self._failed_hotkeys:
                    footer_lines += 1  # warning line

            header_lines = 5  # title, separator, file, lines, blank

            # Calculate available lines for score display
            available_lines = max(3, height - header_lines - footer_lines)

            # Calculate how many lines we can show before and after current line
            total_score_lines = len(self.score.lines)

            # Determine if we need ellipsis indicators
            has_lines_before = current_line > 0
            has_lines_after = current_line < total_score_lines - 1

            # Reserve space for ellipsis
            score_display_lines = available_lines
            if has_lines_before:
                score_display_lines -= 2
            if has_lines_after:
                score_display_lines -= 2

            # Try to keep current line centered, but adjust if near start/end
            ideal_before = score_display_lines // 2
            ideal_after = score_display_lines - ideal_before - 1

            # Adjust based on actual available lines
            actual_before = min(ideal_before, current_line)
            actual_after = min(ideal_after, total_score_lines - current_line - 1)

            # If we have extra space (near start or end), redistribute it
            if actual_before < ideal_before:
                # Near start, show more after
                actual_after = min(
                    score_display_lines - actual_before - 1,
                    total_score_lines - current_line - 1,
                )
            elif actual_after < ideal_after:
                # Near end, show more before
                actual_before = min(
                    score_display_lines - actual_after - 1, current_line
                )

            start_line = current_line - actual_before
            end_line = current_line + actual_after + 1

            # Now render everything
            row = 0

            # Header
            self.stdscr.addstr(
                row, 0, "GIPianoPlayer - Command Line Interface"[: width - 1]
            )
            row += 1
            self.stdscr.addstr(row, 0, "=" * separator_width)
            row += 1
            display_file_name = (
                os.path.basename(self.file_path)
                .encode("ascii", "replace")
                .decode("ascii")
            )
            self.stdscr.addstr(row, 0, f"File: {display_file_name}"[: width - 1])
            row += 1
            self.stdscr.addstr(row, 0, f"Lines: {len(self.score.lines)}"[: width - 1])
            row += 2

            # Show indicator if there are lines before
            if start_line > 0:
                self.stdscr.addstr(
                    row, 0, f"    ... ({start_line} lines above) ..."[: width - 1]
                )
                row += 2

            # Display visible lines
            for line_idx in range(start_line, end_line):
                if row >= height - 1:  # Prevent writing beyond screen
                    break

                line = self.score.lines[line_idx]
                line_num = f"[{line_idx + 1:3d}] "

                if line_idx < current_line:
                    # Already played - cyan/浅蓝色
                    line_text = self._format_score_line(line)
                    self.stdscr.addstr(
                        row,
                        0,
                        (line_num + line_text)[: width - 1],
                        curses.color_pair(1),
                    )
                elif line_idx == current_line:
                    # Current line - with highlighting
                    col = 0
                    self.stdscr.addstr(row, col, line_num)
                    col += len(line_num)

                    for note_idx, note in enumerate(line):
                        note_text = self._format_note(note) + " "
                        if col + len(note_text) >= width:
                            break

                        if note_idx < current_note:
                            self.stdscr.addstr(
                                row, col, note_text, curses.color_pair(2)
                            )  # Red
                        elif note_idx == current_note:
                            self.stdscr.addstr(
                                row,
                                col,
                                note_text,
                                curses.color_pair(3) | curses.A_BOLD,
                            )  # Yellow bold
                        else:
                            self.stdscr.addstr(row, col, note_text)
                        col += len(note_text)
                else:
                    # Not yet played
                    line_text = self._format_score_line(line)
                    self.stdscr.addstr(row, 0, (line_num + line_text)[: width - 1])
                row += 1

            # Show indicator if there are lines after
            if end_line < len(self.score.lines):
                row += 1
                self.stdscr.addstr(
                    row,
                    0,
                    f"    ... ({len(self.score.lines) - end_line} lines below) ..."[
                        : width - 1
                    ],
                )
                row += 1

            row += 1
            self.stdscr.addstr(row, 0, "=" * separator_width)
            row += 1

            # Status line
            finished = bool(self.player and self.player.is_finished())
            if finished:
                state = "FINISHED"
            else:
                state = (
                    self.player.get_state().value.upper() if self.player else "STOPPED"
                )

            # Calculate note-level progress
            if self.player and total_lines > 0:
                # Count total notes in all lines
                total_notes = sum(len(line) for line in self.score.lines)
                if finished:
                    progress_text = (
                        f"Status: {state} | Line {total_lines}/{total_lines} | "
                        f"Note {total_notes}/{total_notes} | Progress: 100.0%"
                    )
                else:
                    # Count notes up to current position
                    played_notes = sum(
                        len(self.score.lines[i]) for i in range(current_line)
                    )
                    played_notes += current_note
                    progress = (
                        (played_notes / total_notes * 100) if total_notes > 0 else 0
                    )
                    progress_text = f"Status: {state} | Line {current_line + 1}/{total_lines} | Note {played_notes}/{total_notes} | Progress: {progress:.1f}%"
            else:
                progress_text = f"Status: {state} | Line {current_line + 1}/{total_lines} | Progress: 0.0%"

            # Append the transient message while it is still active
            if self._message and time.time() < self._message_until:
                progress_text = f"{progress_text}  |  {self._message}"

            self.stdscr.addstr(
                row,
                0,
                progress_text[: width - 1],
            )
            row += 2

            # Configuration panel
            self.stdscr.addstr(row, 0, "Configuration:")
            row += 1
            self.stdscr.addstr(row, 0, "-" * separator_width)
            row += 1

            # Render config lines
            for config_line in config_lines:
                self.stdscr.addstr(row, 0, config_line[: width - 1])
                row += 1
            row += 1

            if keyboard is not None:
                # Show warning if hotkeys failed to register
                if self._failed_hotkeys:
                    failed_keys = ", ".join(
                        key for key, _error in self._failed_hotkeys[:4]
                    )
                    more = "…" if len(self._failed_hotkeys) > 4 else ""
                    warning_msg = (
                        f"Warning: {len(self._failed_hotkeys)} hotkeys failed: "
                        f"{failed_keys}{more}"
                    )
                    self.stdscr.addstr(
                        row,
                        0,
                        warning_msg[: width - 1],
                        curses.color_pair(2),  # Red color for warning
                    )
                    row += 1

                skip_small_unit = "note" if SKIP_SMALL == 1 else "notes"
                skip_large_unit = "line" if SKIP_LARGE == 1 else "lines"
                self.stdscr.addstr(
                    row,
                    0,
                    f"Controls: [{self.hotkeys['play_pause']}] Play/Pause | [{self.hotkeys['quit']}] Quit | [F9] Save"[
                        : width - 1
                    ],
                )
                row += 1
                self.stdscr.addstr(
                    row,
                    0,
                    f"          [{self.hotkeys['skip_backward']}/{self.hotkeys['skip_forward']}] Skip {SKIP_SMALL} {skip_small_unit} | [{self.hotkeys['skip_backward_large']}/{self.hotkeys['skip_forward_large']}] Skip {SKIP_LARGE} {skip_large_unit}"[
                        : width - 1
                    ],
                )
                row += 1
                self.stdscr.addstr(
                    row,
                    0,
                    f"          [{self.hotkeys['reload']}] Reload | [{self.hotkeys['reparse']}] Reparse"[
                        : width - 1
                    ],
                )

            # Refresh screen
            self.stdscr.refresh()

        except (curses.error, UnicodeError):
            # A narrow terminal or unsupported glyph can interrupt a late draw.
            # The finally block still presents the content already rendered.
            pass
        finally:
            try:
                self.stdscr.refresh()
            except curses.error:
                pass

    def _format_note(self, note: Note) -> str:
        """Format a single note for display."""
        return note.display(show_rest_as_underscore=True)

    def run(self) -> None:
        """Run the CLI interface."""
        # Parse score
        try:
            if not Path(self.file_path).exists():
                print(f"Error: score file not found: {self.file_path}")
                return

            # Read original file content (utf-8-sig tolerates a BOM)
            with open(self.file_path, "r", encoding="utf-8-sig") as f:
                self.original_content = f.read()

            parser = ScoreParser(self.file_path)
            self.score = parser.parse()
        except Exception as e:
            print(f"Error loading score: {e}")
            return

        # Run with curses
        curses.wrapper(self._run_with_curses)

    def _run_with_curses(self, stdscr: Any) -> None:
        """Run the CLI with curses screen."""
        self.stdscr = stdscr

        # Initialize colors (guard calls that unsupported terminals reject)
        try:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_CYAN, -1)  # Cyan/浅蓝色 (played)
            curses.init_pair(2, curses.COLOR_RED, -1)  # Red (played in current line)
            curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Yellow (current note)
        except curses.error:
            pass

        # Hide cursor where the terminal supports it
        try:
            curses.curs_set(0)
        except curses.error:
            pass

        # Non-blocking input - but we don't actually use curses for input
        # since we use keyboard library for global hotkeys
        stdscr.nodelay(True)

        # Disable curses input to avoid interfering with keyboard library
        stdscr.keypad(False)

        # Initialize player
        keyboard_controller = KeyboardController()
        if self.score is not None:
            self.player = Player(self.score, keyboard_controller)
            self.player.set_progress_callback(self._on_progress)
        else:
            # This shouldn't happen as we check in run(), but handle gracefully
            return

        # Load and initialize plugins
        from src.plugins.core.loader import load_plugins_from_config, initialize_plugins

        load_plugins_from_config()
        initialize_plugins(player=self.player, cli=self)

        # Setup keyboard shortcuts if available
        if keyboard is not None:
            self._setup_hotkeys()

        # Activate display mode
        self.display_active = True

        # Display initial score
        self._display_score()

        # Set running flag
        self.running = True

        # Main loop
        last_refresh = time.time()
        try:
            while self.running:
                # Don't use curses getch() - it interferes with keyboard library
                # The keyboard library handles all input via global hooks

                # Periodic refresh (every 0.5 seconds) to catch any missed updates
                current_time = time.time()
                if current_time - last_refresh >= 0.5:
                    self._display_score()
                    last_refresh = current_time

                time.sleep(0.05)
        except KeyboardInterrupt:
            pass

        # Cleanup
        if self.player:
            self.player.stop()

        # Stop hotkey handler
        if hasattr(self, "_hotkey_handler"):
            try:
                self._hotkey_handler.stop()
            except Exception:
                pass

        self.display_active = False

    def _setup_hotkeys(self) -> None:
        """Register CLI and plugin bindings with one global hook."""
        if keyboard is None:
            return

        from src.ui.cli.input.default_hotkeys import register_default_hotkeys
        from src.ui.cli.input.hotkey_handler import HotkeyHandler
        from src.ui.cli.input.hotkey_registry import get_hotkey_registry

        registry = get_hotkey_registry()
        register_default_hotkeys(self, registry)
        handler = HotkeyHandler()
        failures: list[tuple[str, str]] = []
        for key, callback in registry.get_all_hotkeys().items():
            try:
                handler.register(key, callback)
            except (TypeError, ValueError) as error:
                failures.append((key, str(error)))

        if not failures:
            try:
                handler.start()
                self._hotkey_handler = handler
            except (OSError, RuntimeError) as error:
                failures.append(("global hook", str(error)))
        self._failed_hotkeys = failures

    def toggle_play_pause(self) -> None:
        """Toggle between play and pause."""
        if not self.player:
            return

        state = self.player.get_state()
        if state == PSM_State.PLAYING:
            self.player.pause()
            # Force display update when paused
            self._display_score()
        elif state == PSM_State.PAUSED:
            self.player.resume()
            # Force display update when resumed
            self._display_score()
        elif state in (PSM_State.STOPPED, PSM_State.LOADED):
            self.player.play()

    def adjust_speed(self, delta: float) -> None:
        """Adjust playback speed."""
        if not self.player:
            return

        current = self.player._speed_multiplier
        new_speed = current + delta
        self.player.set_speed(new_speed)
        if self.player._speed_multiplier == current:
            # The player clamped the request: report the limit reached
            self._flash("Speed limit reached")
        else:
            # Always force display update
            self._display_score()

    def adjust_arpeggio(self, delta: float) -> None:
        """Adjust manual arpeggio interval and leave automatic mode."""
        if not self.player:
            return

        current = self.player._arpeggio_interval
        new_interval = current + delta
        self.player.set_arpeggio_interval(new_interval)
        # Always force display update
        self._display_score()

    def toggle_arpeggio_auto(self) -> None:
        """Toggle inferred arpeggio timing."""
        if not self.player:
            return

        self.player.set_arpeggio_auto(not self.player.get_arpeggio_auto())
        self._display_score()

    def adjust_interval(self, delta: float) -> None:
        """Adjust note interval rating."""
        if not self.player:
            return

        current = self.player._interval_rating
        new_interval = max(0.01, current + delta)  # Minimum 0.01s
        self.player.set_interval_rating(new_interval)
        # Always force display update
        self._display_score()

    def adjust_line_interval(self, delta: float) -> None:
        """Adjust line interval rating (N empty notes)."""
        if not self.player:
            return

        current = self.player._line_interval_rating
        new_rating = max(0.0, current + delta)
        self.player.set_line_interval_rating(new_rating)
        # Always force display update
        self._display_score()

    def adjust_space_interval(self, delta: float) -> None:
        """Adjust space interval rating (multiplier for rest notes)."""
        if not self.player:
            return

        current = self.player._space_interval_rating
        new_rating = max(0.0, current + delta)
        self.player.set_space_interval_rating(new_rating)
        # Always force display update
        self._display_score()

    def adjust_empty_line_interval(self, delta: float) -> None:
        """Adjust empty line interval rating (N empty notes for empty lines)."""
        if not self.player:
            return

        current = self.player._empty_line_interval_rating
        new_rating = max(0.0, current + delta)
        self.player.set_empty_line_interval_rating(new_rating)
        # Empty lines are included or dropped at parse time, so reparse to
        # apply the new rating to the score currently loaded in memory.
        self.reparse("Empty line interval updated")

    def adjust_segment_length(self, delta: int) -> None:
        """Adjust segment length (N notes per segment)."""
        if not self.player:
            return

        current = self.player._segment_length
        new_length = max(0, current + delta)
        self.player.set_segment_length(new_length)
        # Segment padding/truncation happens at parse time, so reparse to
        # apply the new length to the score currently loaded in memory.
        self.reparse("Segment length updated")

    def skip_backward(self) -> None:
        """Skip backward by 1 note."""
        if not self.player:
            return
        self.player.skip_backward_notes(1)
        # Always force display update
        self._display_score()

    def skip_forward(self) -> None:
        """Skip forward by 1 note."""
        if not self.player:
            return
        self.player.skip_forward_notes(1)
        # Always force display update
        self._display_score()

    def skip_backward_large(self) -> None:
        """Skip backward by 1 line."""
        if not self.player:
            return
        self.player.skip_backward_line()
        # Always force display update
        self._display_score()

    def skip_forward_large(self) -> None:
        """Skip forward by 1 line."""
        if not self.player:
            return
        self.player.skip_forward_line()
        # Always force display update
        self._display_score()

    def quit(self) -> None:
        """Quit the application."""
        # Cleanup plugins
        from src.plugins.core.loader import cleanup_plugins

        cleanup_plugins()

        # Stop player
        if self.player:
            self.player.stop()

        self.running = False

    def save_config(self) -> None:
        """Save current configuration to file."""
        if not self.player or not self.original_content:
            return

        try:
            # Get current configuration values
            speed_multiplier = self.player._speed_multiplier
            arpeggio_interval = self.player._arpeggio_interval
            arpeggio_auto = self.player.get_arpeggio_auto()
            interval_rating = self.player._interval_rating
            line_interval_rating = self.player._line_interval_rating
            space_interval_rating = self.player._space_interval_rating
            empty_line_interval_rating = self.player._empty_line_interval_rating
            segment_length = self.player._segment_length
            segment_strict = self.player.get_segment_strict()

            # Parse the original content
            lines = self.original_content.split("\n")
            new_lines = []
            config_section = True
            config_updated = {
                "speed_multiplier": False,
                "arpeggio_interval": False,
                "arpeggio_auto": False,
                "interval_rating": False,
                "line_interval_rating": False,
                "space_interval_rating": False,
                "empty_line_interval_rating": False,
                "segment_length": False,
                "segment_strict": False,
            }

            for line in lines:
                stripped = line.strip()

                # Check if we're past the config section
                if stripped.startswith("---") or (
                    stripped and not stripped.startswith("#") and "=" not in stripped
                ):
                    config_section = False
                    # Insert missing configs ONCE when we first exit config section
                    if any(not v for v in config_updated.values()):
                        insert_lines: list[str] = []
                        if not config_updated["speed_multiplier"]:
                            insert_lines.append(
                                f"SPEED_MULTIPLIER = {speed_multiplier}"
                            )
                        if not config_updated["arpeggio_interval"]:
                            insert_lines.append(
                                f"ARPEGGIO_INTERVAL = {arpeggio_interval}"
                            )
                        if not config_updated["arpeggio_auto"]:
                            insert_lines.append(f"ARPEGGIO_AUTO = {arpeggio_auto}")
                        if not config_updated["interval_rating"]:
                            insert_lines.append(f"INTERVAL_RATING = {interval_rating}")
                        if not config_updated["line_interval_rating"]:
                            insert_lines.append(
                                f"LINE_INTERVAL_RATING = {line_interval_rating}"
                            )
                        if not config_updated["space_interval_rating"]:
                            insert_lines.append(
                                f"SPACE_INTERVAL_RATING = {space_interval_rating}"
                            )
                        if not config_updated["empty_line_interval_rating"]:
                            insert_lines.append(
                                f"EMPTY_LINE_INTERVAL_RATING = {empty_line_interval_rating}"
                            )
                        if not config_updated["segment_length"]:
                            insert_lines.append(f"SEGMENT_LENGTH = {segment_length}")
                        if not config_updated["segment_strict"]:
                            insert_lines.append(f"SEGMENT_STRICT = {segment_strict}")

                        if insert_lines:
                            # Insert before the separator or first score line
                            for insert_line in insert_lines:
                                new_lines.append(insert_line)

                        # Mark all as updated
                        for key in config_updated:
                            config_updated[key] = True

                if config_section and "=" in line:
                    key, _ = line.split("=", 1)
                    key = key.strip().lower()

                    if key == "speed_multiplier":
                        new_lines.append(f"SPEED_MULTIPLIER = {speed_multiplier}")
                        config_updated["speed_multiplier"] = True
                    elif key == "arpeggio_interval":
                        new_lines.append(f"ARPEGGIO_INTERVAL = {arpeggio_interval}")
                        config_updated["arpeggio_interval"] = True
                    elif key == "arpeggio_auto":
                        new_lines.append(f"ARPEGGIO_AUTO = {arpeggio_auto}")
                        config_updated["arpeggio_auto"] = True
                    elif key == "interval_rating":
                        new_lines.append(f"INTERVAL_RATING = {interval_rating}")
                        config_updated["interval_rating"] = True
                    elif key == "line_interval_rating":
                        new_lines.append(
                            f"LINE_INTERVAL_RATING = {line_interval_rating}"
                        )
                        config_updated["line_interval_rating"] = True
                    elif key == "space_interval_rating":
                        new_lines.append(
                            f"SPACE_INTERVAL_RATING = {space_interval_rating}"
                        )
                        config_updated["space_interval_rating"] = True
                    elif key == "empty_line_interval_rating":
                        new_lines.append(
                            f"EMPTY_LINE_INTERVAL_RATING = {empty_line_interval_rating}"
                        )
                        config_updated["empty_line_interval_rating"] = True
                    elif key == "segment_length":
                        new_lines.append(f"SEGMENT_LENGTH = {segment_length}")
                        config_updated["segment_length"] = True
                    elif key == "segment_strict":
                        new_lines.append(f"SEGMENT_STRICT = {segment_strict}")
                        config_updated["segment_strict"] = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)

            # Write back to file
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))

            # Update original content
            self.original_content = "\n".join(new_lines)

            self._flash("Configuration saved")

        except Exception:
            self._flash("Save failed - see terminal for details")

    def reload(self) -> None:
        """Reload the score file from disk (re-read and re-parse)."""
        if not self.player:
            return

        try:
            # Stop current playback
            was_playing = self.player.get_state() == PSM_State.PLAYING
            sustain_enabled = self.player.get_sustain_enabled()
            self.player.stop()

            # Re-read file content (utf-8-sig tolerates a BOM)
            with open(self.file_path, "r", encoding="utf-8-sig") as f:
                self.original_content = f.read()

            # Re-parse the score (will read config from file)
            parser = ScoreParser(self.file_path)
            self.score = parser.parse()

            # Create new player with new score (uses config from parsed score)
            keyboard_controller = KeyboardController()
            self.player = Player(self.score, keyboard_controller)
            self.player.set_progress_callback(self._on_progress)
            if sustain_enabled:
                self.player.toggle_sustain()

            # Re-initialize plugins with new player
            # Force re-initialization by updating context and calling initialize directly

            plugin_errors = self._reinitialize_plugins()

            # Resume playback if it was playing
            if was_playing:
                self.player.play()

            self._flash(self._reload_message("Score reloaded", plugin_errors))

        except Exception:
            self._flash("Reload failed")

    def _reinitialize_plugins(self) -> int:
        """Point all loaded plugins at the current player and CLI.

        Returns:
            Number of plugins that failed to re-initialize
        """
        from src.plugins.core.manager import get_plugin_manager
        from src.plugins.core.context import PluginContext

        plugin_manager = get_plugin_manager()
        new_context = PluginContext(player=self.player, cli=self)
        plugin_manager.set_context(new_context)

        failures = 0
        for plugin in plugin_manager.get_all_plugins():
            try:
                plugin.initialize(new_context)
            except Exception:
                failures += 1
        return failures

    @staticmethod
    def _reload_message(base: str, plugin_errors: int) -> str:
        """Compose a status message, mentioning plugin failures if any."""
        if plugin_errors:
            return f"{base} ({plugin_errors} plugin error{'s' if plugin_errors != 1 else ''})"
        return base

    def reparse(self, message: str = "Score reparsed") -> None:
        """Reparse the score with current configuration (apply new segment_length, etc.)."""
        if not self.player:
            return

        try:
            # Get current playback state and position
            was_playing = self.player.get_state() == PSM_State.PLAYING
            current_line, _ = self.player.get_progress()

            # Get current configuration
            speed_multiplier = self.player._speed_multiplier
            arpeggio_interval = self.player._arpeggio_interval
            arpeggio_auto = self.player.get_arpeggio_auto()
            interval_rating = self.player._interval_rating
            line_interval_rating = self.player._line_interval_rating
            space_interval_rating = self.player._space_interval_rating
            empty_line_interval_rating = self.player._empty_line_interval_rating
            segment_length = self.player._segment_length
            segment_strict = self.player.get_segment_strict()
            sustain_enabled = self.player.get_sustain_enabled()

            # Stop current playback
            self.player.stop()

            # Save current config to file first
            self.save_config()

            # Re-parse the score (will use updated config from file)
            parser = ScoreParser(self.file_path)
            self.score = parser.parse()

            # Create new player with reparsed score
            keyboard_controller = KeyboardController()
            self.player = Player(self.score, keyboard_controller)
            self.player.set_progress_callback(self._on_progress)

            plugin_errors = self._reinitialize_plugins()

            # Restore configuration (in case file save failed)
            self.player.set_speed(speed_multiplier)
            self.player.set_arpeggio_interval(arpeggio_interval)
            self.player.set_arpeggio_auto(arpeggio_auto)
            self.player.set_interval_rating(interval_rating)
            self.player.set_line_interval_rating(line_interval_rating)
            self.player.set_space_interval_rating(space_interval_rating)
            self.player.set_empty_line_interval_rating(empty_line_interval_rating)
            self.player.set_segment_length(segment_length)
            self.player.set_segment_strict(segment_strict)
            if sustain_enabled:
                self.player.toggle_sustain()

            # Restore position (clamp to new score length)
            if self.score and current_line < len(self.score.lines):
                self.player.jump_to_line(current_line)

            # Resume playback if it was playing
            if was_playing:
                self.player.play()

            self._flash(self._reload_message(message, plugin_errors))

        except Exception:
            self._flash("Reparse failed")

    def toggle_sustain(self) -> None:
        """Toggle sustain mode on/off."""
        if not self.player:
            return

        self.player.toggle_sustain()
        # Force display update to show new sustain state
        self._display_score()

    def toggle_segment_strict(self) -> None:
        """Toggle segment strict mode on/off."""
        if not self.player:
            return

        self.player.toggle_segment_strict()
        # Segment padding/truncation happens at parse time, so reparse to
        # apply the new strict mode to the score currently loaded in memory.
        self.reparse("Strict segment mode updated")

    def _on_progress(
        self, current_line: int, total_lines: int, current_note: int, total_notes: int
    ) -> None:
        """Progress callback - refresh display with throttling."""
        current_time = time.time()
        # Only refresh at configured rate
        if current_time - self.last_display_time >= DISPLAY_REFRESH_RATE:
            self._display_score()
            self.last_display_time = current_time
