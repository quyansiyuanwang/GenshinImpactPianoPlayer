"""Main score screen rendering."""

from __future__ import annotations

import curses
import os
import time
import keyboard
from typing import Any, List
from src.application.config.constants import DISPLAY_REFRESH_RATE, SKIP_SMALL, SKIP_LARGE
from src.core.domain.note import Note, NoteType
from src.application.host_protocol import ApplicationHost

class MainScreenMixin(ApplicationHost):
    """Extracted application behavior."""

    def _flash(self, message: str, duration: float = 2.5) -> None:
        """Show a transient status message on the status line."""
        self._message = message
        self._message_until = time.time() + duration
        # Throttled: a held key that keeps flashing (e.g. speed limit) must not
        # flood the terminal; the main loop flushes the request within one tick.
        self._request_refresh()
    
    
    def _request_refresh(self) -> None:
        """Throttled refresh for hotkey threads.
    
        Renders immediately when the previous frame is old enough; otherwise
        flags a pending refresh that the main loop flushes within one tick, so
        held-down adjustment keys cannot flood the terminal with repaints.
        """
        now = time.time()
        if now - self.last_display_time >= DISPLAY_REFRESH_RATE:
            self.last_display_time = now
            self._display_score()
            return
        self._refresh_requested = True
    
    
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
        """Display the full score with current position highlighted using curses.
    
        The playback thread (progress callbacks), the keyboard hook thread
        (hotkey actions), and the main loop can all request a frame, so the
        curses work is serialized behind a lock.
        """
        if not self.display_active or not self.stdscr:
            return
    
        with self._render_lock:
            self._render_frame(self.stdscr)
    
    
    def _render_frame(self, stdscr: Any) -> None:
        """Render one full frame (caller must hold the render lock)."""
        try:
            # Get terminal size (recalculate every time for real-time adaptation)
            height, width = stdscr.getmaxyx()
    
            # Erase (not clear) to avoid full-repaint flicker on fast refreshes
            stdscr.erase()
    
            if not self.score:
                stdscr.addstr(0, 0, "No score loaded.")
                stdscr.refresh()
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
                loop_enabled = self.player.get_loop_enabled()
                loop_status = "ON" if loop_enabled else "OFF"
                config_lines.append(
                    f"  Loop: {loop_status}              [{self.hotkeys['toggle_loop']}] Toggle"
                )
                line_repeat = "ON" if self.player.get_line_loop_enabled() else "OFF"
                config_lines.append(
                    f"  Line Repeat: {line_repeat}        [{self.hotkeys['toggle_line_loop']}] Toggle"
                )
                range_a, range_b = self.player.get_range()
                if range_a is not None and range_b is not None and range_a < range_b:
                    range_status = "looping"
                elif range_a is not None:
                    range_status = "A set"
                elif range_b is not None:
                    range_status = "B set"
                else:
                    range_status = "off"
                config_lines.append(
                    f"  Range: {range_status}       [{self.hotkeys['set_range_a']}/{self.hotkeys['set_range_b']}] Set | [{self.hotkeys['clear_range']}] Clear"
                )
                bookmark = self.player.get_bookmark()
                bookmark_status = f"line {bookmark[0] + 1}" if bookmark else "none"
                config_lines.append(
                    f"  Bookmark: {bookmark_status}    [{self.hotkeys['set_bookmark']}] Set | [{self.hotkeys['jump_to_bookmark']}] Jump"
                )
                key_status = "LOCKED" if self._keyboard_locked else "active"
                config_lines.append(
                    f"  Keyboard Input: {key_status}  [{self.hotkeys['toggle_output_lock']}] Toggle"
                )
    
            # On short terminals drop the less-used rows so the controls stay
            # visible instead of being pushed off-screen.
            if len(config_lines) > 5 and height < 32:
                essential = ("Speed:", "Arpeggio:", "Note Interval:", "Loop:")
                config_lines = [
                    line for line in config_lines if any(k in line for k in essential)
                ]
    
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
            score_warnings = self.score.warnings
            if score_warnings:
                header_lines += 1  # warning line
    
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
            stdscr.addstr(row, 0, "GIPianoPlayer - Command Line Interface"[: width - 1])
            row += 1
            stdscr.addstr(row, 0, "=" * separator_width)
            row += 1
            display_file_name = (
                os.path.basename(self.file_path)
                .encode("ascii", "replace")
                .decode("ascii")
            )
            stdscr.addstr(row, 0, f"File: {display_file_name}"[: width - 1])
            row += 1
            stdscr.addstr(row, 0, f"Lines: {len(self.score.lines)}"[: width - 1])
            row += 1
    
            # Surface characters the parser could not interpret (ASCII-folded
            # like the file name, since they may be arbitrary text)
            if score_warnings:
                preview = "; ".join(score_warnings[:2])
                more = (
                    f" (+{len(score_warnings) - 2} more)"
                    if len(score_warnings) > 2
                    else ""
                )
                warning_text = (
                    f"Warning: {len(score_warnings)} unknown characters ignored: "
                    f"{preview}{more}"
                )
                warning_text = warning_text.encode("ascii", "replace").decode("ascii")
                stdscr.addstr(row, 0, warning_text[: width - 1], curses.color_pair(2))
                row += 1
            row += 1
    
            # Show indicator if there are lines before
            if start_line > 0:
                stdscr.addstr(
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
                    stdscr.addstr(
                        row,
                        0,
                        (line_num + line_text)[: width - 1],
                        curses.color_pair(1),
                    )
                elif line_idx == current_line:
                    # Current line - with highlighting
                    col = 0
                    stdscr.addstr(row, col, line_num)
                    col += len(line_num)
    
                    for note_idx, note in enumerate(line):
                        note_text = self._format_note(note) + " "
                        if col + len(note_text) >= width:
                            break
    
                        if note_idx < current_note:
                            stdscr.addstr(
                                row, col, note_text, curses.color_pair(2)
                            )  # Red
                        elif note_idx == current_note:
                            stdscr.addstr(
                                row,
                                col,
                                note_text,
                                curses.color_pair(3) | curses.A_BOLD,
                            )  # Yellow bold
                        else:
                            stdscr.addstr(row, col, note_text)
                        col += len(note_text)
                else:
                    # Not yet played
                    line_text = self._format_score_line(line)
                    stdscr.addstr(row, 0, (line_num + line_text)[: width - 1])
                row += 1
    
            # Show indicator if there are lines after
            if end_line < len(self.score.lines):
                row += 1
                stdscr.addstr(
                    row,
                    0,
                    f"    ... ({len(self.score.lines) - end_line} lines below) ..."[
                        : width - 1
                    ],
                )
                row += 1
    
            # Status line state and note-level progress (O(1) prefix sums)
            finished = bool(self.player and self.player.is_finished())
            if finished:
                state = "FINISHED"
            else:
                state = (
                    self.player.get_state().value.upper() if self.player else "STOPPED"
                )
    
            played_notes = 0
            total_notes = 0
            if self.player and total_lines > 0:
                played_notes, total_notes = self.player.get_note_progress()
                if finished:
                    played_notes = total_notes
    
            # The separator above the status doubles as a progress bar
            row += 1
            if total_notes > 0:
                fraction = played_notes / total_notes
            else:
                fraction = 1.0 if finished else 0.0
            filled = min(separator_width, max(0, int(separator_width * fraction)))
            stdscr.addstr(row, 0, "=" * filled + "-" * (separator_width - filled))
            row += 1
    
            if finished:
                progress_text = (
                    f"Status: {state} | Line {total_lines}/{total_lines} | "
                    f"Note {total_notes}/{total_notes} | Progress: 100.0%"
                )
            elif total_notes > 0:
                progress = played_notes / total_notes * 100
                progress_text = f"Status: {state} | Line {current_line + 1}/{total_lines} | Note {played_notes}/{total_notes} | Progress: {progress:.1f}%"
            else:
                progress_text = f"Status: {state} | Line {current_line + 1}/{total_lines} | Progress: 0.0%"
    
            # Append the transient message while it is still active
            if self._message and time.time() < self._message_until:
                progress_text = f"{progress_text}  |  {self._message}"
    
            stdscr.addstr(
                row,
                0,
                progress_text[: width - 1],
            )
            row += 2
    
            # Configuration panel
            stdscr.addstr(row, 0, "Configuration:")
            row += 1
            stdscr.addstr(row, 0, "-" * separator_width)
            row += 1
    
            # Render config lines
            for config_line in config_lines:
                stdscr.addstr(row, 0, config_line[: width - 1])
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
                    stdscr.addstr(
                        row,
                        0,
                        warning_msg[: width - 1],
                        curses.color_pair(2),  # Red color for warning
                    )
                    row += 1
    
                skip_small_unit = "note" if SKIP_SMALL == 1 else "notes"
                skip_large_unit = "line" if SKIP_LARGE == 1 else "lines"
                stdscr.addstr(
                    row,
                    0,
                    f"Controls: [{self.hotkeys['play_pause']}] Play/Pause | [{self.hotkeys['quit']}] Quit | [{self.hotkeys['save']}] Save | [{self.hotkeys['open_settings']}] Settings"[
                        : width - 1
                    ],
                )
                row += 1
                stdscr.addstr(
                    row,
                    0,
                    f"          [{self.hotkeys['skip_backward']}/{self.hotkeys['skip_forward']}] Skip {SKIP_SMALL} {skip_small_unit} | [{self.hotkeys['skip_backward_large']}/{self.hotkeys['skip_forward_large']}] Skip {SKIP_LARGE} {skip_large_unit}"[
                        : width - 1
                    ],
                )
                row += 1
                stdscr.addstr(
                    row,
                    0,
                    f"          [{self.hotkeys['reload']}] Reload | [{self.hotkeys['reparse']}] Reparse | [{self.hotkeys['toggle_loop']}] Loop | [{self.hotkeys['jump_to_start']}/{self.hotkeys['jump_to_end']}] Start/End"[
                        : width - 1
                    ],
                )
    
            # Refresh screen
            stdscr.refresh()
    
        except (curses.error, UnicodeError):
            # A narrow terminal or unsupported glyph can interrupt a late draw.
            # The finally block still presents the content already rendered.
            pass
        finally:
            try:
                stdscr.refresh()
            except curses.error:
                pass
    
    
    
    def _format_note(self, note: Note) -> str:
        """Format a single note for display."""
        return note.display(show_rest_as_underscore=True)
    
    
    def _on_progress(
        self, current_line: int, total_lines: int, current_note: int, total_notes: int
    ) -> None:
        """Progress callback - refresh display with throttling."""
        current_time = time.time()
        # Only refresh at configured rate
        if current_time - self.last_display_time >= DISPLAY_REFRESH_RATE:
            self._display_score()
            self.last_display_time = current_time
    
