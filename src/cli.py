"""Command-line interface for GIPianoPlayer."""

import sys
import time
import os
import curses
from typing import Optional, Dict
from src.parser import ScoreParser, NoteType
from src.player import Player, PlayerState
from src.keyboard_controller import KeyboardController
from src.constants import (
    DEFAULT_HOTKEYS,
    SKIP_SMALL,
    SKIP_LARGE,
    SPEED_STEP,
    ARPEGGIO_STEP,
    INTERVAL_STEP,
    DISPLAY_REFRESH_RATE,
    DISPLAY_LINES_BEFORE,
    DISPLAY_LINES_AFTER,
    SPEED_STEP_LARGE,
)

try:
    import keyboard
except ImportError:
    keyboard = None


class CLI:
    """Command-line interface with keyboard shortcuts."""

    def __init__(self, file_path: str, hotkeys: Optional[Dict[str, str]] = None):
        self.file_path = file_path
        self.player: Optional[Player] = None
        self.running = False
        self.score = None
        self.display_active = False
        self.last_display_time = 0
        self.original_content = ""
        self.stdscr = None  # curses screen object

        # Use custom hotkeys or defaults
        self.hotkeys = hotkeys if hotkeys is not None else DEFAULT_HOTKEYS.copy()

        # Check if keyboard library is available
        if keyboard is None:
            print(
                "Warning: 'keyboard' library not installed. Hotkeys will not be available."
            )
            print("Install with: pip install keyboard")

    def _format_score_line(self, line) -> str:
        """Format a score line as text, preserving visual separators."""
        result = ""
        prev_was_space = False

        for note in line:
            if note.type == NoteType.SINGLE:
                if note.keys[0] == " ":
                    # Space is a rest - track it
                    prev_was_space = True
                    result += "_ "
                else:
                    result += f"{note.keys[0]} "
                    prev_was_space = False
            elif note.type == NoteType.CHORD:
                result += f"({''.join(note.keys)}) "
                prev_was_space = False
            elif note.type == NoteType.ARPEGGIO:
                arp_content = ""
                for key in note.keys:
                    if isinstance(key, str):
                        arp_content += key
                    else:  # Nested chord
                        arp_content += f"({''.join(key.keys)})"
                result += f"[{arp_content}] "
                prev_was_space = False

        return result.rstrip()

    def _display_score(self) -> None:
        """Display the full score with current position highlighted using curses."""
        if not self.display_active or not self.stdscr:
            return

        try:
            # Get terminal size (recalculate every time for real-time adaptation)
            height, width = self.stdscr.getmaxyx()

            # Clear screen for fresh render
            self.stdscr.clear()

            # Get current position
            current_line, total_lines = (
                self.player.get_progress()
                if self.player
                else (0, len(self.score.lines))
            )
            current_note = self.player._current_note if self.player else 0

            separator_width = min(width - 1, 100)

            # Build config lines to get actual count
            config_lines = []
            if self.player:
                speed = self.player._speed_multiplier
                arp_interval = self.player._arpeggio_interval
                interval = self.player._interval_rating
                line_interval = self.player._line_interval_rating
                segment_length = self.player._segment_length
                sustain_enabled = self.player.get_sustain_enabled()

                config_lines.append(
                    f"  Speed: {speed:.2f}x          [+/- or Ctrl+ +/-] Adjust speed"
                )
                config_lines.append(
                    f"  Arpeggio Interval: {arp_interval:.3f}s   [[/]] Adjust arpeggio"
                )
                config_lines.append(
                    f"  Note Interval: {interval:.3f}s       [</> or ,/.] Adjust interval"
                )
                config_lines.append(
                    f"  Line Interval: {line_interval:.0f} notes  [Up/Down] Adjust line"
                )
                segment_status = (
                    f"{segment_length} notes" if segment_length > 0 else "Disabled"
                )
                config_lines.append(
                    f"  Segment Length: {segment_status}  [PgUp/PgDn] Adjust segment"
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
            self.stdscr.addstr(
                row, 0, f"File: {os.path.basename(self.file_path)}"[: width - 1]
            )
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
            state = self.player.get_state().value.upper() if self.player else "STOPPED"

            # Calculate note-level progress
            if self.player and total_lines > 0:
                # Count total notes in all lines
                total_notes = sum(len(line) for line in self.score.lines)
                # Count notes up to current position
                played_notes = sum(len(self.score.lines[i]) for i in range(current_line))
                played_notes += current_note
                progress = (played_notes / total_notes * 100) if total_notes > 0 else 0
                progress_text = f"Status: {state} | Line {current_line + 1}/{total_lines} | Note {played_notes}/{total_notes} | Progress: {progress:.1f}%"
            else:
                progress_text = f"Status: {state} | Line {current_line + 1}/{total_lines} | Progress: 0.0%"

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
                    f"          [{self.hotkeys['skip_backward']}/{self.hotkeys['skip_forward']}] Skip {SKIP_SMALL} notes | [{self.hotkeys['skip_backward_large']}/{self.hotkeys['skip_forward_large']}] Skip {SKIP_LARGE} lines"[
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

        except curses.error:
            # Ignore curses errors (e.g., writing outside screen bounds)
            pass

    def _format_note(self, note) -> str:
        """Format a single note for display."""
        if note.type == NoteType.SINGLE:
            if note.keys[0] == " ":
                return "_"
            else:
                return note.keys[0]
        elif note.type == NoteType.CHORD:
            return f"({''.join(note.keys)})"
        elif note.type == NoteType.ARPEGGIO:
            arp_content = ""
            for key in note.keys:
                if isinstance(key, str):
                    arp_content += key
                else:
                    arp_content += f"({''.join(key.keys)})"
            return f"[{arp_content}]"
        return ""

    def run(self) -> None:
        """Run the CLI interface."""
        # Parse score
        try:
            # Read original file content
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.original_content = f.read()

            parser = ScoreParser(self.file_path)
            self.score = parser.parse()
        except Exception as e:
            print(f"Error loading score: {e}")
            return

        # Run with curses
        curses.wrapper(self._run_with_curses)

    def _run_with_curses(self, stdscr) -> None:
        """Run the CLI with curses screen."""
        self.stdscr = stdscr

        # Initialize colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)  # Cyan/浅蓝色 (played)
        curses.init_pair(2, curses.COLOR_RED, -1)  # Red (played in current line)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Yellow (current note)

        # Hide cursor
        curses.curs_set(0)

        # Non-blocking input
        stdscr.nodelay(True)

        # Initialize player
        keyboard_controller = KeyboardController()
        self.player = Player(self.score, keyboard_controller)
        self.player.set_progress_callback(self._on_progress)

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
                # Check for key events (including resize)
                try:
                    key = stdscr.getch()
                    if key == curses.KEY_RESIZE:
                        # Terminal was resized, force redraw
                        curses.resize_term(*stdscr.getmaxyx())
                        self._display_score()
                except curses.error:
                    pass

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

        self.display_active = False

    def _setup_hotkeys(self) -> None:
        """Setup keyboard shortcuts using configured hotkeys."""
        if keyboard is None:
            return

        keyboard.add_hotkey(self.hotkeys["play_pause"], self._toggle_play_pause)
        keyboard.add_hotkey(
            self.hotkeys["speed_up"], lambda: self._adjust_speed(SPEED_STEP)
        )
        keyboard.add_hotkey(
            self.hotkeys["speed_down"], lambda: self._adjust_speed(-SPEED_STEP)
        )
        keyboard.add_hotkey(
            self.hotkeys["speed_up_large"], lambda: self._adjust_speed(SPEED_STEP_LARGE)
        )
        keyboard.add_hotkey(
            self.hotkeys["speed_down_large"],
            lambda: self._adjust_speed(-SPEED_STEP_LARGE),
        )
        keyboard.add_hotkey(
            self.hotkeys["arpeggio_faster"],
            lambda: self._adjust_arpeggio(-ARPEGGIO_STEP),
        )
        keyboard.add_hotkey(
            self.hotkeys["arpeggio_slower"],
            lambda: self._adjust_arpeggio(ARPEGGIO_STEP),
        )
        keyboard.add_hotkey(
            self.hotkeys["interval_shorter"],
            lambda: self._adjust_interval(-INTERVAL_STEP),
        )
        keyboard.add_hotkey(
            self.hotkeys["interval_longer"],
            lambda: self._adjust_interval(INTERVAL_STEP),
        )
        keyboard.add_hotkey(
            self.hotkeys["line_interval_less"], lambda: self._adjust_line_interval(-1.0)
        )  # Down = less
        keyboard.add_hotkey(
            self.hotkeys["line_interval_more"], lambda: self._adjust_line_interval(1.0)
        )  # Up = more
        keyboard.add_hotkey(
            self.hotkeys["segment_length_less"], lambda: self._adjust_segment_length(-1)
        )  # PgDn = less
        keyboard.add_hotkey(
            self.hotkeys["segment_length_more"], lambda: self._adjust_segment_length(1)
        )  # PgUp = more
        keyboard.add_hotkey(self.hotkeys["skip_backward"], self._skip_backward)
        keyboard.add_hotkey(self.hotkeys["skip_forward"], self._skip_forward)
        keyboard.add_hotkey(
            self.hotkeys["skip_backward_large"], self._skip_backward_large
        )
        keyboard.add_hotkey(
            self.hotkeys["skip_forward_large"], self._skip_forward_large
        )
        keyboard.add_hotkey(self.hotkeys["quit"], self._quit)
        keyboard.add_hotkey("f9", self._save_config)  # F9 to save config
        keyboard.add_hotkey(self.hotkeys["reload"], self._reload)  # F5 to reload
        keyboard.add_hotkey(self.hotkeys["reparse"], self._reparse)  # F6 to reparse
        keyboard.add_hotkey(
            self.hotkeys["toggle_sustain"], self._toggle_sustain
        )  # F7 to toggle sustain

    def _toggle_play_pause(self) -> None:
        """Toggle between play and pause."""
        if not self.player:
            return

        state = self.player.get_state()
        if state == PlayerState.PLAYING:
            self.player.pause()
            # Force display update when paused
            self._display_score()
        elif state == PlayerState.PAUSED:
            self.player.resume()
            # Force display update when resumed
            self._display_score()
        elif state == PlayerState.STOPPED:
            self.player.play()

    def _adjust_speed(self, delta: float) -> None:
        """Adjust playback speed."""
        if not self.player:
            return

        current = self.player._speed_multiplier
        new_speed = current + delta
        self.player.set_speed(new_speed)
        # Always force display update
        self._display_score()

    def _adjust_arpeggio(self, delta: float) -> None:
        """Adjust arpeggio interval."""
        if not self.player:
            return

        current = self.player._arpeggio_interval
        new_interval = current + delta
        self.player.set_arpeggio_interval(new_interval)
        # Always force display update
        self._display_score()

    def _adjust_interval(self, delta: float) -> None:
        """Adjust note interval rating."""
        if not self.player:
            return

        current = self.player._interval_rating
        new_interval = max(0.01, current + delta)  # Minimum 0.01s
        self.player.set_interval_rating(new_interval)
        # Always force display update
        self._display_score()

    def _adjust_line_interval(self, delta: float) -> None:
        """Adjust line interval rating (N empty notes)."""
        if not self.player:
            return

        current = self.player._line_interval_rating
        new_rating = max(0.0, current + delta)
        self.player.set_line_interval_rating(new_rating)
        # Always force display update
        self._display_score()

    def _adjust_segment_length(self, delta: int) -> None:
        """Adjust segment length (N notes per segment)."""
        if not self.player:
            return

        current = self.player._segment_length
        new_length = max(0, current + delta)
        self.player.set_segment_length(new_length)
        # Always force display update
        self._display_score()

    def _skip_backward(self) -> None:
        """Skip backward by 1 note."""
        if not self.player:
            return
        self.player.skip_backward_notes(1)
        # Always force display update
        self._display_score()

    def _skip_forward(self) -> None:
        """Skip forward by 1 note."""
        if not self.player:
            return
        self.player.skip_forward_notes(1)
        # Always force display update
        self._display_score()

    def _skip_backward_large(self) -> None:
        """Skip backward by 1 line."""
        if not self.player:
            return
        self.player.skip_backward_line()
        # Always force display update
        self._display_score()

    def _skip_forward_large(self) -> None:
        """Skip forward by 1 line."""
        if not self.player:
            return
        self.player.skip_forward_line()
        # Always force display update
        self._display_score()

    def _quit(self) -> None:
        """Quit the application."""
        self.running = False

    def _save_config(self) -> None:
        """Save current configuration to file."""
        if not self.player or not self.original_content:
            return

        try:
            # Get current configuration values
            speed_multiplier = self.player._speed_multiplier
            arpeggio_interval = self.player._arpeggio_interval
            interval_rating = self.player._interval_rating
            line_interval_rating = self.player._line_interval_rating
            segment_length = self.player._segment_length

            # Parse the original content
            lines = self.original_content.split("\n")
            new_lines = []
            config_section = True
            config_updated = {
                "speed_multiplier": False,
                "arpeggio_interval": False,
                "interval_rating": False,
                "line_interval_rating": False,
                "segment_length": False,
            }

            for line in lines:
                stripped = line.strip()

                # Check if we're past the config section
                if stripped.startswith("---") or (
                    stripped and not stripped.startswith("#") and "=" not in stripped
                ):
                    config_section = False

                if config_section and "=" in line:
                    key, _ = line.split("=", 1)
                    key = key.strip().lower()

                    if key == "speed_multiplier":
                        new_lines.append(f"SPEED_MULTIPLIER = {speed_multiplier}")
                        config_updated["speed_multiplier"] = True
                    elif key == "arpeggio_interval":
                        new_lines.append(f"ARPEGGIO_INTERVAL = {arpeggio_interval}")
                        config_updated["arpeggio_interval"] = True
                    elif key == "interval_rating":
                        new_lines.append(f"INTERVAL_RATING = {interval_rating}")
                        config_updated["interval_rating"] = True
                    elif key == "line_interval_rating":
                        new_lines.append(
                            f"LINE_INTERVAL_RATING = {line_interval_rating}"
                        )
                        config_updated["line_interval_rating"] = True
                    elif key == "segment_length":
                        new_lines.append(f"SEGMENT_LENGTH = {segment_length}")
                        config_updated["segment_length"] = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)

                # If we just passed config section, add missing configs
                if not config_section and any(not v for v in config_updated.values()):
                    insert_lines = []
                    if not config_updated["speed_multiplier"]:
                        insert_lines.append(f"SPEED_MULTIPLIER = {speed_multiplier}")
                    if not config_updated["arpeggio_interval"]:
                        insert_lines.append(f"ARPEGGIO_INTERVAL = {arpeggio_interval}")
                    if not config_updated["interval_rating"]:
                        insert_lines.append(f"INTERVAL_RATING = {interval_rating}")
                    if not config_updated["line_interval_rating"]:
                        insert_lines.append(
                            f"LINE_INTERVAL_RATING = {line_interval_rating}"
                        )
                    if not config_updated["segment_length"]:
                        insert_lines.append(f"SEGMENT_LENGTH = {segment_length}")

                    if insert_lines:
                        # Insert before the separator or first score line
                        idx = len(new_lines) - 1
                        for insert_line in reversed(insert_lines):
                            new_lines.insert(idx, insert_line)

                    # Mark all as updated
                    for key in config_updated:
                        config_updated[key] = True

            # Write back to file
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))

            # Update original content
            self.original_content = "\n".join(new_lines)

            # Show success message briefly (will be cleared on next display update)
            # We can't use _print here as display is active, so we'll update display
            self._display_score()

        except Exception as e:
            # Silently fail - don't disrupt playback
            pass

    def _reload(self) -> None:
        """Reload the score file from disk (re-read and re-parse)."""
        if not self.player:
            return

        try:
            # Stop current playback
            was_playing = self.player.get_state() == PlayerState.PLAYING
            self.player.stop()

            # Re-read file content
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.original_content = f.read()

            # Re-parse the score
            parser = ScoreParser(self.file_path)
            self.score = parser.parse()

            # Create new player with new score
            keyboard_controller = KeyboardController()
            self.player = Player(self.score, keyboard_controller)
            self.player.set_progress_callback(self._on_progress)

            # Resume playback if it was playing
            if was_playing:
                self.player.play()

            # Force display update
            self._display_score()

        except Exception as e:
            # Silently fail - don't disrupt
            pass

    def _reparse(self) -> None:
        """Reparse the score with current configuration (apply new segment_length, etc.)."""
        if not self.player:
            return

        try:
            # Get current playback state and position
            was_playing = self.player.get_state() == PlayerState.PLAYING
            current_line, _ = self.player.get_progress()

            # Get current configuration
            speed_multiplier = self.player._speed_multiplier
            arpeggio_interval = self.player._arpeggio_interval
            interval_rating = self.player._interval_rating
            line_interval_rating = self.player._line_interval_rating
            segment_length = self.player._segment_length

            # Stop current playback
            self.player.stop()

            # Save current config to file first
            self._save_config()

            # Re-parse the score (will use updated config from file)
            parser = ScoreParser(self.file_path)
            self.score = parser.parse()

            # Create new player with reparsed score
            keyboard_controller = KeyboardController()
            self.player = Player(self.score, keyboard_controller)
            self.player.set_progress_callback(self._on_progress)

            # Restore configuration (in case file save failed)
            self.player.set_speed(speed_multiplier)
            self.player.set_arpeggio_interval(arpeggio_interval)
            self.player.set_interval_rating(interval_rating)
            self.player.set_line_interval_rating(line_interval_rating)
            self.player.set_segment_length(segment_length)

            # Restore position (clamp to new score length)
            if current_line < len(self.score.lines):
                self.player.jump_to_line(current_line)

            # Resume playback if it was playing
            if was_playing:
                self.player.play()

            # Force display update
            self._display_score()

        except Exception as e:
            # Silently fail - don't disrupt
            pass

    def _toggle_sustain(self) -> None:
        """Toggle sustain mode on/off."""
        if not self.player:
            return

        self.player.toggle_sustain()
        # Force display update to show new sustain state
        self._display_score()

    def _on_progress(
        self, current_line: int, total_lines: int, current_note: int, total_notes: int
    ) -> None:
        """Progress callback - refresh display with throttling."""
        current_time = time.time()
        # Only refresh at configured rate
        if current_time - self.last_display_time >= DISPLAY_REFRESH_RATE:
            self._display_score()
            self.last_display_time = current_time
