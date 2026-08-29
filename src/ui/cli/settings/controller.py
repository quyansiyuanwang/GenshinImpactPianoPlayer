"""Application-facing coordinator for the settings screen."""

from __future__ import annotations

from collections.abc import Callable

from src.application.config.profiles import ProfileStore
from src.ui.cli.settings.screens import ScreenResult, SettingsRootScreen
from src.ui.cli.settings.session import SettingsSession
from src.ui.cli.input.key_binding import KeyBinding


class SettingsController:
    """Create sessions and apply their results without leaking services to UI."""

    def __init__(
        self,
        store: ProfileStore,
        apply: Callable[[SettingsSession], None] | None = None,
    ) -> None:
        self.store = store
        self.apply = apply
        self.session: SettingsSession | None = None
        self.screen: SettingsRootScreen | None = None

    def open(self) -> SettingsRootScreen:
        from src.ui.cli.input.hotkey_registry import get_hotkey_registry

        plugin_bindings: set[str] = set()
        for key, _description in get_hotkey_registry().get_by_category("plugin"):
            try:
                plugin_bindings.add(str(KeyBinding.parse(key)))
            except ValueError:
                continue
        self.session = SettingsSession(self.store, plugin_bindings)

        def save(session: SettingsSession) -> str | None:
            try:
                session.save()
                if self.apply:
                    self.apply(session)
            except (OSError, ValueError) as error:
                return str(error)
            return None

        self.screen = SettingsRootScreen(self.session, on_save=save)
        return self.screen

    def close(self) -> ScreenResult:
        result = self.screen.result if self.screen else ScreenResult.NONE
        self.screen = None
        self.session = None
        return result
