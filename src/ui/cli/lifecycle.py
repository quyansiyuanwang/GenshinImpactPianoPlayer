"""Application lifecycle and hotkey orchestration."""

from __future__ import annotations

import curses
import keyboard
import locale
import time
from typing import Any
from src.application.command_bus import CommandResult
from src.application.events import InputEvent, InputKind, KeyCode
from src.application.config.constants import DEFAULT_HOTKEYS
from src.ui.cli.input.adapters import CursesInputAdapter
from src.application.host_protocol import ApplicationHost


class LifecycleMixin(ApplicationHost):
    """Application lifecycle behavior."""

    def run(self) -> None:
        """Run the CLI interface."""
        # curses derives its multibyte encoding from the active process locale.
        # This is especially important for wide Chinese glyphs on Windows.
        try:
            locale.setlocale(locale.LC_ALL, "")
        except locale.Error:
            # Continue with Python's startup locale on minimal environments.
            pass
        # Parse score
        try:
            entries, errors = self.file_loader.load_paths(self.file_paths)
            self.playlist_errors = errors
            if not entries:
                print("Error: no supported score files found")
                for error in errors:
                    print(f"Warning: {error}")
                return
            self.playlist.add_paths([entry.path for entry in entries])
            first = self.playlist.current
            if first is None:
                return
            loaded, message = self.track_controller.load(first.path)
            if not loaded:
                print(message)
                return
            for error in errors:
                print(f"Warning: {error}")
        except Exception as e:
            print(f"Error loading scores: {e}")
            return

        # Run with curses
        curses.wrapper(self._run_with_curses)

    def _run_with_curses(self, stdscr: Any) -> None:
        """Run the CLI with curses screen."""
        self.stdscr = stdscr
        self._curses_input = CursesInputAdapter(stdscr)

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
        if self.score is None:
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
                if self._curses_input:
                    terminal_event = self._curses_input.read_available()
                    if terminal_event.kind == InputKind.RESIZE:
                        self._display_score()
                    elif terminal_event.key is not None:
                        if (
                            terminal_event.kind == InputKind.KEY
                            and terminal_event.key == KeyCode.CHARACTER
                        ):
                            if terminal_event.text.lower() == "a":
                                self._playlist_prompt(stdscr, "Add file or directory")
                                continue
                            if terminal_event.text == "/":
                                self._playlist_prompt(
                                    stdscr, "Search playlist", search=True
                                )
                                continue
                        handled = getattr(self, "handle_playlist_event")(terminal_event)
                        result = (
                            None
                            if handled
                            else self.controller.dispatch_event(terminal_event)
                        )
                        if result is not None and result.message:
                            self._flash(result.message)
                if current_time - last_refresh >= 0.5:
                    self._display_score()
                if self._settings_requested:
                    self._settings_requested = False
                    self._run_settings_ui(stdscr)
                    last_refresh = current_time
                elif self._refresh_requested:
                    # A throttled hotkey refresh is waiting for its time slot
                    self._refresh_requested = False
                    self.last_display_time = current_time
                    self._display_score()

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
        # Rebuild the registry while retaining bindings supplied by plugins.
        plugin_bindings = [
            (key, callback, registry.get_description(key))
            for key, callback in registry.get_all_hotkeys().items()
            if key not in DEFAULT_HOTKEYS.values()
        ]
        registry.clear()
        try:
            register_default_hotkeys(self, registry)
        except (KeyError, TypeError, ValueError):
            # A hand-edited profile may contain duplicate or missing bindings.
            # Fall back to the known-good defaults for this session.
            self.hotkeys = DEFAULT_HOTKEYS.copy()
            registry.clear()
            register_default_hotkeys(self, registry)
        for key, callback, description in plugin_bindings:
            if registry.get_callback(key) is None:
                registry.register(key, callback, description, "plugin")
        handler = HotkeyHandler()
        # Keep explicit plugin command bindings while replacing profile-owned
        # built-ins. Legacy plugin hotkeys are rebuilt from the registry below.
        self.controller.clear_bindings(preserve_prefixes=("plugin.",))
        failures: list[tuple[str, str]] = []
        for key, callback in registry.get_all_hotkeys().items():
            try:
                handler.register(key, callback)
                action = next(
                    (
                        name
                        for name, binding in self.hotkeys.items()
                        if binding.lower() == key.lower()
                    ),
                    None,
                )
                command = (
                    "input.toggle_lock"
                    if action == "toggle_output_lock"
                    else f"app.{action}"
                    if action
                    else f"plugin.{key}"
                )

                def invoke(
                    _event: InputEvent, callback: Any = callback
                ) -> CommandResult:
                    callback()
                    return CommandResult.ok()

                self.controller.register_command(command, invoke, replace=True)
                if self.controller.binding_command(key) is None:
                    self.controller.bind_key(key, command)
            except (TypeError, ValueError) as error:
                failures.append((key, str(error)))

        handler.set_event_dispatcher(self.controller.dispatch_event)

        if not failures:
            try:
                handler.start()
                self._hotkey_handler = handler
            except (OSError, RuntimeError) as error:
                failures.append(("global hook", str(error)))
        self._failed_hotkeys = failures
        self.controller.set_locked(self._keyboard_locked)
        handler.set_locked(
            self._keyboard_locked, self.hotkeys.get("toggle_output_lock", "f12")
        )

    def _rebuild_hotkeys(self) -> None:
        """Replace the global handler after a profile change."""
        if hasattr(self, "_hotkey_handler"):
            try:
                self._hotkey_handler.stop()
            except Exception:
                pass
        self._setup_hotkeys()

    def request_settings(self) -> None:
        """Request the curses thread to open the settings UI."""
        self._settings_requested = True
        self._request_refresh()

    def toggle_keyboard_lock(self) -> None:
        """Lock or unlock application control input while playback continues."""
        self._keyboard_locked = not self._keyboard_locked
        self.controller.set_locked(self._keyboard_locked)
        handler = getattr(self, "_hotkey_handler", None)
        if handler:
            handler.set_locked(
                self._keyboard_locked,
                self.hotkeys.get("toggle_output_lock", "f12"),
            )
        self._flash(
            "Keyboard input LOCKED"
            if self._keyboard_locked
            else "Keyboard input unlocked"
        )

    def _playlist_prompt(
        self, stdscr: Any, title: str, *, search: bool = False
    ) -> None:
        """Run a short curses input prompt for playlist operations."""
        try:
            stdscr.nodelay(False)
            stdscr.keypad(True)
            height, width = stdscr.getmaxyx()
            prompt = f"{title}: "
            stdscr.addstr(max(0, height - 1), 0, prompt[: max(1, width - 1)])
            stdscr.refresh()
            raw = stdscr.getstr(
                max(0, height - 1),
                min(len(prompt), max(0, width - 1)),
                max(1, width - len(prompt) - 1),
            )
            value = raw.decode("utf-8", "replace").strip()
            if search:
                self.playlist.search(value)
                self._flash(f"Search: {len(self.playlist.visible_entries)} result(s)")
            elif value:
                getattr(self, "playlist_add_paths")([value])
        except Exception as error:
            self._flash(f"Playlist input failed: {error}")
        finally:
            stdscr.nodelay(True)
            stdscr.keypad(False)
