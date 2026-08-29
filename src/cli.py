"""GIPianoPlayer command-line application facade.

The CLI composes independent lifecycle, rendering, and playback services.  It
keeps the historical ``CLI`` entry point for integrations while avoiding a
single module that owns every application concern.
"""

from __future__ import annotations

from threading import Lock
from typing import Any, Dict, Optional

from src.application.config.constants import DEFAULT_HOTKEYS
from src.application.config.profiles import ProfileStore
from src.application.controller import ApplicationController
from src.ui.cli.settings.controller import SettingsController
from src.core.domain.score import ParsedScore
from src.core.player.player import Player
from src.ui.cli.input.adapters import CursesInputAdapter
from src.ui.cli.lifecycle import LifecycleMixin
from src.ui.cli.main_screen import MainScreenMixin
from src.ui.cli.settings_screen import SettingsScreenMixin
from src.ui.cli.screen_manager import ScreenManager
from src.application.file_actions import FileActionsMixin
from src.application.navigation_controls import NavigationControlsMixin
from src.application.playback_controls import PlaybackControlsMixin


class CLI(
    MainScreenMixin,
    LifecycleMixin,
    SettingsScreenMixin,
    PlaybackControlsMixin,
    NavigationControlsMixin,
    FileActionsMixin,
):
    """Compose the application services and expose the stable CLI facade."""

    def __init__(self, file_path: str, hotkeys: Optional[Dict[str, str]] = None):
        self.file_path = file_path
        self.player: Optional[Player] = None
        self.running = False
        self.score: Optional[ParsedScore] = None
        self.display_active = False
        self.last_display_time = 0.0
        self.original_content = ""
        self.stdscr: Any | None = None
        self._failed_hotkeys: list[tuple[str, str]] = []
        self._message = ""
        self._message_until = 0.0
        self._render_lock = Lock()
        self._refresh_requested = False
        self.profile_store = ProfileStore()
        self.settings_controller = SettingsController(self.profile_store, self._apply_settings_session)
        self.hotkeys = self.profile_store.active_hotkeys()
        self.key_mapping = self.profile_store.active_mapping()
        self._keyboard_locked = False
        self._settings_requested = False
        self.controller = ApplicationController()
        self._curses_input: CursesInputAdapter | None = None
        self.screen_manager = ScreenManager()
        if hotkeys is not None:
            self.hotkeys = {**DEFAULT_HOTKEYS, **hotkeys}


__all__ = ["CLI"]
