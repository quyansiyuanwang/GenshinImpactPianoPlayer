"""Compatibility entry point for the interactive settings TUI."""

from __future__ import annotations

import copy
from typing import Any

from src.application.events import InputKind
from src.application.host_protocol import ApplicationHost
from src.application.state.state_machine import PlayerState as PSM_State
from src.ui.cli.components import TerminalSurface
from src.ui.cli.input.adapters import CursesInputAdapter
from src.ui.cli.settings.screens import ScreenResult
from src.ui.cli.settings.session import SettingsSession
from src.ui.cli.screen_manager import ScreenManager


class SettingsScreenMixin(ApplicationHost):
    """Open the settings screen on the curses thread.

    The mixin remains as a compatibility facade for ``CLI`` and old plugins;
    all actual interaction lives in the backend-neutral settings package.
    """

    def _run_settings_ui(self, stdscr: Any) -> None:
        original_profiles = copy.deepcopy(self.profile_store.data)
        was_playing = bool(self.player and self.player.get_state() == PSM_State.PLAYING)
        if was_playing and self.player:
            self.player.pause()
        handler = getattr(self, "_hotkey_handler", None)
        if handler:
            handler.stop()
        self._stop_input_isolation()
        stdscr.nodelay(False)
        stdscr.keypad(True)

        screen = self.settings_controller.open()
        screen_manager = ScreenManager(screen)
        adapter = CursesInputAdapter(stdscr)
        surface = TerminalSurface(stdscr)
        try:
            while self.running or self.player is not None:
                screen_manager.render(surface)
                event = adapter.read_event()
                if event.kind == InputKind.QUIT:
                    break
                screen_manager.handle(event)
                if screen.result == ScreenResult.CANCELLED:
                    break
                if screen.result == ScreenResult.CLOSED:
                    break
        finally:
            stdscr.nodelay(True)
            stdscr.keypad(False)
            if screen.result == ScreenResult.NONE:
                self.profile_store.data = original_profiles
            self.hotkeys = self.profile_store.active_hotkeys()
            self.key_mapping = self.profile_store.active_mapping()
            self.key_mapping_scans = self.profile_store.mapping_scans()
            if self.player:
                self.player.set_key_mapping(self.key_mapping, self.key_mapping_scans)
            self._rebuild_hotkeys()
            if was_playing and self.player:
                self.player.resume()
            self._display_score()

    def _apply_settings_session(self, session: SettingsSession) -> None:
        """Apply a saved session to runtime services."""
        self.hotkeys = session.active_hotkeys.copy()
        self.key_mapping = session.active_mapping.copy()
        self.key_mapping_scans = copy.deepcopy(session.active_mapping_scans)
        if self.player:
            self.player.set_key_mapping(self.key_mapping, self.key_mapping_scans)
        self._rebuild_hotkeys()


__all__ = ["SettingsScreenMixin"]
