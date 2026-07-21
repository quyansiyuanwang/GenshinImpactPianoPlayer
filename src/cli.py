"""Command-line interface for GIPianoPlayer."""

import time
import os
import sys
import curses
import keyboard
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
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


def get_log_file_path(filename: str) -> str:
    """Get the path for a log file.

    In packaged app, saves to exe directory or user's temp directory.
    In development, saves to current directory.

    Args:
        filename: Name of the log file

    Returns:
        Full path to the log file
    """
    # Try to save next to the executable
    if getattr(sys, "frozen", False):
        # Running as packaged exe
        exe_dir = Path(sys.executable).parent
        log_path = exe_dir / filename

        # Test if we can write to exe directory
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("")
            return str(log_path)
        except (PermissionError, OSError):
            # Can't write to exe directory, use temp directory
            import tempfile

            temp_dir = Path(tempfile.gettempdir()) / "GIPianoPlayer"
            temp_dir.mkdir(exist_ok=True)
            log_path = temp_dir / filename
            return str(log_path)
    else:
        # Running in development, use current directory
        return filename


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

        # Use custom hotkeys or defaults
        self.hotkeys = hotkeys if hotkeys is not None else DEFAULT_HOTKEYS.copy()

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

            # Clear screen for fresh render
            self.stdscr.clear()

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
                arp_interval = self.player._arpeggio_interval
                interval = self.player._interval_rating
                line_interval = self.player._line_interval_rating
                space_interval = self.player._space_interval_rating
                empty_line_interval = self.player._empty_line_interval_rating
                segment_length = self.player._segment_length
                segment_strict = self.player.get_segment_strict()
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
            state = self.player.get_state().value.upper() if self.player else "STOPPED"

            # Calculate note-level progress
            if self.player and total_lines > 0:
                # Count total notes in all lines
                total_notes = sum(len(line) for line in self.score.lines)
                # Count notes up to current position
                played_notes = sum(
                    len(self.score.lines[i]) for i in range(current_line)
                )
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
                # Show warning if hotkeys failed to register
                if self._failed_hotkeys:
                    log_path = getattr(self, "_error_log_path", "hotkey_errors.log")
                    warning_msg = f"Warning: {len(self._failed_hotkeys)} hotkeys failed! See: {log_path}"
                    self.stdscr.addstr(
                        row,
                        0,
                        warning_msg[: width - 1],
                        curses.color_pair(2),  # Red color for warning
                    )
                    row += 1

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

    def _run_with_curses(self, stdscr: Any) -> None:
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

    def _setup_hotkeys_legacy(self) -> None:
        """Setup keyboard shortcuts using scan code based hotkey handler."""
        if keyboard is None:
            return

        from src.ui.cli.input.hotkey_handler import HotkeyHandler, SCAN_CODES
        from src.plugins.core.manager import get_plugin_manager

        # Create hotkey handler
        self._hotkey_handler = HotkeyHandler()

        # Get plugin instances
        plugin_manager = get_plugin_manager()
        speed_plugin = plugin_manager.get_plugin("speed_adjustment")
        interval_plugin = plugin_manager.get_plugin("interval_adjustment")
        segment_plugin = plugin_manager.get_plugin("segment_adjustment")
        mode_plugin = plugin_manager.get_plugin("mode_toggle")

        failed_hotkeys: list[tuple[str, str]] = []

        # Get log file paths
        error_log = get_log_file_path("hotkey_errors.log")
        debug_log = get_log_file_path("hotkey_debug.log")

        try:
            # Log where files are being saved
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 70}\n")
                f.write(f"Hotkey Setup - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Log file location: {error_log}\n")
                f.write(f"{'=' * 70}\n\n")

            # Playback control (function keys work fine)
            self._hotkey_handler.register_by_name("f8", self.toggle_play_pause)
            self._hotkey_handler.register_by_name("f2", self.quit)
            self._hotkey_handler.register_by_name("f5", self.reload)
            self._hotkey_handler.register_by_name("f6", self.reparse)

            # Speed control - use SCAN CODES for symbol keys
            if speed_plugin:
                # Use scan codes for = and - keys (more reliable in packaged apps)
                # Fix lambda closure issue by using default arguments
                with open(error_log, "a", encoding="utf-8") as f:
                    f.write("Registering speed hotkeys with scan codes...\n")
                    f.write(f"  equals (scan {SCAN_CODES['equals']})\n")
                    f.write(f"  minus (scan {SCAN_CODES['minus']})\n")

                def speed_up_callback(log: str = debug_log, cli: "CLI" = self) -> None:
                    try:
                        with open(log, "a", encoding="utf-8") as f:
                            f.write("Speed UP callback called\n")
                        # Get plugin dynamically to handle reload
                        from src.plugins.core.manager import get_plugin_manager

                        plugin = get_plugin_manager().get_plugin("speed_adjustment")
                        if plugin:
                            # Log current speed before adjustment
                            old_speed = (
                                cli.player._speed_multiplier if cli.player else None
                            )
                            with open(log, "a", encoding="utf-8") as f:
                                f.write(f"  Current speed: {old_speed}\n")

                            plugin.adjust_speed(0.01)  # type: ignore

                            # Log new speed after adjustment
                            new_speed = (
                                cli.player._speed_multiplier if cli.player else None
                            )
                            with open(log, "a", encoding="utf-8") as f:
                                f.write(f"  New speed: {new_speed}\n")

                            cli._display_score()  # Force display refresh
                            with open(log, "a", encoding="utf-8") as f:
                                f.write("Speed UP executed successfully\n")
                        else:
                            with open(log, "a", encoding="utf-8") as f:
                                f.write("Speed UP error: plugin not found\n")
                    except Exception as e:
                        with open(log, "a", encoding="utf-8") as f:
                            f.write(f"Speed UP error: {e}\n")
                            import traceback

                            f.write(traceback.format_exc())

                def speed_down_callback(
                    log: str = debug_log, cli: "CLI" = self
                ) -> None:
                    try:
                        with open(log, "a", encoding="utf-8") as f:
                            f.write("Speed DOWN callback called\n")
                        # Get plugin dynamically to handle reload
                        from src.plugins.core.manager import get_plugin_manager

                        plugin = get_plugin_manager().get_plugin("speed_adjustment")
                        if plugin:
                            plugin.adjust_speed(-0.01)  # type: ignore
                            cli._display_score()  # Force display refresh
                            with open(log, "a", encoding="utf-8") as f:
                                f.write("Speed DOWN executed successfully\n")
                        else:
                            with open(log, "a", encoding="utf-8") as f:
                                f.write("Speed DOWN error: plugin not found\n")
                    except Exception as e:
                        with open(log, "a", encoding="utf-8") as f:
                            f.write(f"Speed DOWN error: {e}\n")

                self._hotkey_handler.register_by_scan_code(
                    SCAN_CODES["equals"], speed_up_callback
                )
                self._hotkey_handler.register_by_scan_code(
                    SCAN_CODES["minus"], speed_down_callback
                )

            # Interval control - use SCAN CODES
            if interval_plugin:
                with open(error_log, "a", encoding="utf-8") as f:
                    f.write("Registering interval hotkeys with scan codes...\n")
                    f.write(f"  left_bracket (scan {SCAN_CODES['left_bracket']})\n")
                    f.write(f"  right_bracket (scan {SCAN_CODES['right_bracket']})\n")
                    f.write(f"  comma (scan {SCAN_CODES['comma']})\n")
                    f.write(f"  period (scan {SCAN_CODES['period']})\n")

                # Brackets
                def make_interval_callback(
                    method_name: str, delta: float, cli_ref: "CLI" = self
                ) -> Callable[[], None]:
                    def callback() -> None:
                        from src.plugins.core.manager import get_plugin_manager

                        plugin = get_plugin_manager().get_plugin("interval_adjustment")
                        if plugin:
                            getattr(plugin, method_name)(delta)
                            cli_ref._display_score()

                    return callback

                self._hotkey_handler.register_by_scan_code(
                    SCAN_CODES["left_bracket"],
                    make_interval_callback("adjust_arpeggio", -0.01),
                )
                self._hotkey_handler.register_by_scan_code(
                    SCAN_CODES["right_bracket"],
                    make_interval_callback("adjust_arpeggio", 0.01),
                )
                # Comma and period
                self._hotkey_handler.register_by_scan_code(
                    SCAN_CODES["comma"],
                    make_interval_callback("adjust_interval", -0.01),
                )
                self._hotkey_handler.register_by_scan_code(
                    SCAN_CODES["period"],
                    make_interval_callback("adjust_interval", 0.01),
                )
                # Arrow keys (these work fine with names)
                self._hotkey_handler.register_by_name(
                    "up", make_interval_callback("adjust_line_interval", 1)
                )
                self._hotkey_handler.register_by_name(
                    "down", make_interval_callback("adjust_line_interval", -1)
                )

            # Mode toggles
            if mode_plugin:

                def toggle_sustain_callback(cli_ref: "CLI" = self) -> None:
                    from src.plugins.core.manager import get_plugin_manager

                    plugin = get_plugin_manager().get_plugin("mode_toggle")
                    if plugin:
                        getattr(plugin, "toggle_sustain")()
                        cli_ref._display_score()

                self._hotkey_handler.register_by_name("f7", toggle_sustain_callback)

            # Segment control
            if segment_plugin:

                def make_segment_callback(
                    method_name: str, delta: int | None = None, cli_ref: "CLI" = self
                ) -> Callable[[], None]:
                    def callback() -> None:
                        from src.plugins.core.manager import get_plugin_manager

                        plugin = get_plugin_manager().get_plugin("segment_adjustment")
                        if plugin:
                            if delta is not None:
                                getattr(plugin, method_name)(delta)
                            else:
                                getattr(plugin, method_name)()
                            cli_ref._display_score()

                    return callback

                self._hotkey_handler.register_by_name(
                    "page up", make_segment_callback("adjust_segment_length", 1)
                )
                self._hotkey_handler.register_by_name(
                    "page down", make_segment_callback("adjust_segment_length", -1)
                )
                self._hotkey_handler.register_by_name(
                    "f4", make_segment_callback("toggle_segment_strict")
                )

            # Navigation
            self._hotkey_handler.register_by_name("left", self.skip_backward)
            self._hotkey_handler.register_by_name("right", self.skip_forward)
            self._hotkey_handler.register_by_name("ctrl+left", self.skip_backward_large)
            self._hotkey_handler.register_by_name("ctrl+right", self.skip_forward_large)

            # Register plugin hotkeys from registry
            from src.ui.cli.input.hotkey_registry import get_hotkey_registry

            registry = get_hotkey_registry()
            for key, callback in registry.get_all_hotkeys().items():
                try:
                    with open(error_log, "a", encoding="utf-8") as f:
                        f.write(f"Registering plugin hotkey: {key}\n")
                    self._hotkey_handler.register_by_name(key, callback)
                except Exception as e:
                    with open(error_log, "a", encoding="utf-8") as f:
                        f.write(f"Failed to register plugin hotkey {key}: {e}\n")

            # Start the hotkey handler
            self._hotkey_handler.start()

            # Log success and show user where to find logs
            with open(error_log, "a", encoding="utf-8") as f:
                f.write("=== Hotkey Setup (Scan Code Method) ===\n")
                f.write("Successfully registered hotkeys using scan codes\n")
                f.write(
                    "Symbol keys (=, -, [, ], ,, .) use scan codes for reliability\n\n"
                )

            # Store log paths for display
            self._error_log_path = error_log
            self._debug_log_path = debug_log

        except Exception as e:
            failed_hotkeys.append(("hotkey_setup", str(e)))
            try:
                with open(error_log, "a", encoding="utf-8") as f:
                    f.write(f"Failed to setup hotkeys: {e}\n")
            except Exception:
                pass

        # Store failed hotkeys for later reference
        self._failed_hotkeys = failed_hotkeys

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
        # Always force display update
        self._display_score()

    def adjust_arpeggio(self, delta: float) -> None:
        """Adjust arpeggio interval."""
        if not self.player:
            return

        current = self.player._arpeggio_interval
        new_interval = current + delta
        self.player.set_arpeggio_interval(new_interval)
        # Always force display update
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
        # Always force display update
        self._display_score()

    def adjust_segment_length(self, delta: int) -> None:
        """Adjust segment length (N notes per segment)."""
        if not self.player:
            return

        current = self.player._segment_length
        new_length = max(0, current + delta)
        self.player.set_segment_length(new_length)
        # Always force display update
        self._display_score()

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

            # Show success message briefly (will be cleared on next display update)
            # We can't use _print here as display is active, so we'll update display
            self._display_score()

        except Exception:
            # Silently fail - don't disrupt playback
            pass

    def reload(self) -> None:
        """Reload the score file from disk (re-read and re-parse)."""
        if not self.player:
            return

        try:
            # Stop current playback
            was_playing = self.player.get_state() == PSM_State.PLAYING
            self.player.stop()

            # Re-read file content
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.original_content = f.read()

            # Re-parse the score (will read config from file)
            parser = ScoreParser(self.file_path)
            self.score = parser.parse()

            # Create new player with new score (uses config from parsed score)
            keyboard_controller = KeyboardController()
            self.player = Player(self.score, keyboard_controller)
            self.player.set_progress_callback(self._on_progress)

            # Re-initialize plugins with new player
            # Force re-initialization by updating context and calling initialize directly
            from src.plugins.core.manager import get_plugin_manager
            from src.plugins.core.context import PluginContext

            plugin_manager = get_plugin_manager()
            new_context = PluginContext(player=self.player, cli=self)
            plugin_manager.set_context(new_context)

            # Force re-initialize all plugins (not just REGISTERED ones)
            for plugin in plugin_manager.get_all_plugins():
                try:
                    plugin.initialize(new_context)
                except Exception as e:
                    print(f"Failed to re-initialize plugin '{plugin.name}': {e}")

            # Resume playback if it was playing
            if was_playing:
                self.player.play()

            # Force display update
            self._display_score()

        except Exception:
            # Silently fail - don't disrupt
            pass

    def reparse(self) -> None:
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
            interval_rating = self.player._interval_rating
            line_interval_rating = self.player._line_interval_rating
            space_interval_rating = self.player._space_interval_rating
            empty_line_interval_rating = self.player._empty_line_interval_rating
            segment_length = self.player._segment_length

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

            # Re-initialize plugins with new player
            # Force re-initialization by updating context and calling initialize directly
            from src.plugins.core.manager import get_plugin_manager
            from src.plugins.core.context import PluginContext

            plugin_manager = get_plugin_manager()
            new_context = PluginContext(player=self.player, cli=self)
            plugin_manager.set_context(new_context)

            # Force re-initialize all plugins (not just REGISTERED ones)
            for plugin in plugin_manager.get_all_plugins():
                try:
                    plugin.initialize(new_context)
                except Exception as e:
                    print(f"Failed to re-initialize plugin '{plugin.name}': {e}")

            # Restore configuration (in case file save failed)
            self.player.set_speed(speed_multiplier)
            self.player.set_arpeggio_interval(arpeggio_interval)
            self.player.set_interval_rating(interval_rating)
            self.player.set_line_interval_rating(line_interval_rating)
            self.player.set_space_interval_rating(space_interval_rating)
            self.player.set_empty_line_interval_rating(empty_line_interval_rating)
            self.player.set_segment_length(segment_length)

            # Restore position (clamp to new score length)
            if self.score and current_line < len(self.score.lines):
                self.player.jump_to_line(current_line)

            # Resume playback if it was playing
            if was_playing:
                self.player.play()

            # Force display update
            self._display_score()

        except Exception:
            # Silently fail - don't disrupt
            pass

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
        # Force display update to show new strict state
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
