"""Settings screen and profile editing."""

from __future__ import annotations

import copy
import curses
import keyboard
from typing import Any
from src.application.events import InputKind, KeyCode
from src.application.state.state_machine import PlayerState as PSM_State
from src.ui.cli.input.adapters import CursesInputAdapter
from src.application.host_protocol import ApplicationHost

class SettingsScreenMixin(ApplicationHost):
    """Reusable settings screen behavior."""

    @staticmethod
    def _settings_addstr(stdscr: Any, row: int, text: str, col: int = 0) -> None:
        """Draw settings text clipped to the current terminal dimensions."""
        height, width = stdscr.getmaxyx()
        if row < 0 or row >= height or col >= width:
            return
        try:
            stdscr.addstr(row, col, text[: max(0, width - col - 1)])
        except curses.error:
            # A resize can happen between getmaxyx and addstr.
            pass
    
    
    
    def _settings_prompt(self, stdscr: Any, prompt: str) -> str:
        """Read a short line while redrawing safely after terminal resizes."""
        value: list[str] = []
        stdscr.timeout(-1)
        input_adapter = CursesInputAdapter(stdscr)
    
        try:
            while True:
                stdscr.erase()
                self._settings_addstr(stdscr, 0, prompt)
                self._settings_addstr(stdscr, 1, "".join(value))
                stdscr.refresh()
                event = input_adapter.read_event()
                if event.kind == InputKind.RESIZE:
                    continue
                if event.key == KeyCode.ENTER:
                    return "".join(value).strip()
                if event.key == KeyCode.ESCAPE:
                    return ""
                if event.key == KeyCode.BACKSPACE:
                    if value:
                        value.pop()
                elif event.key == KeyCode.CHARACTER and event.text and event.text.isprintable():
                    value.append(event.text)
        finally:
            stdscr.timeout(-1)
    
    
    
    def _run_settings_ui(self, stdscr: Any) -> None:
        """Run the small keyboard/mapping profile editor on the curses thread."""
        original_profiles = copy.deepcopy(self.profile_store.data)
        was_playing = bool(self.player and self.player.get_state() == PSM_State.PLAYING)
        if was_playing and self.player:
            self.player.pause()
        handler = getattr(self, "_hotkey_handler", None)
        if handler:
            handler.stop()
        stdscr.nodelay(False)
        stdscr.keypad(True)
        input_adapter = CursesInputAdapter(stdscr)
        try:
            while True:
                stdscr.erase()
                self._settings_addstr(stdscr, 0, "Settings: [H] Hotkeys  [M] Mapping  [Q] Save/Exit")
                self._settings_addstr(stdscr, 2, "Choose a section")
                stdscr.refresh()
                event = input_adapter.read_event()
                if event.kind == InputKind.RESIZE:
                    continue
                choice = event.text.lower() if event.key == KeyCode.CHARACTER else ""
                if choice == "q":
                    try:
                        self.profile_store.save()
                    except OSError:
                        self._flash("Profile save failed")
                    break
                if event.key == KeyCode.ESCAPE:
                    self.profile_store.data = original_profiles
                    break
                if choice == "h":
                    self._settings_hotkeys_ui(stdscr)
                elif choice == "m":
                    self._settings_mapping_ui(stdscr)
        finally:
            stdscr.nodelay(True)
            stdscr.keypad(False)
            self.hotkeys = self.profile_store.active_hotkeys()
            self.key_mapping = self.profile_store.active_mapping()
            if self.player:
                self.player.set_key_mapping(self.key_mapping)
            self._rebuild_hotkeys()
            if was_playing and self.player:
                self.player.resume()
            self._display_score()
    
    
    
    def _settings_hotkeys_ui(self, stdscr: Any) -> None:
        """Edit the active hotkey profile using line-oriented curses controls."""
        profiles = self.profile_store.hotkey_profiles()
        input_adapter = CursesInputAdapter(stdscr)
        while True:
            stdscr.erase()
            active = str(self.profile_store.data["active_hotkey_profile"])
            self._settings_addstr(stdscr, 0, f"Hotkey profile: {active}")
            self._settings_addstr(stdscr, 1, "[S]elect [N]ew [R]ename [D]elete [E]dit action [Q]uit")
            names = list(profiles)
            for index, name in enumerate(names):
                self._settings_addstr(stdscr, 3 + index, f"{index + 1}. {name}")
            action_row = 4 + len(names)
            self._settings_addstr(stdscr, action_row - 1, "Actions (type the action name to edit):")
            for index, (action, binding) in enumerate(self.hotkeys.items()):
                row = action_row + index
                if row >= stdscr.getmaxyx()[0] - 1:
                    break
                self._settings_addstr(stdscr, row, f"{action}: {binding}")
            stdscr.refresh()
            event = input_adapter.read_event()
            if event.kind == InputKind.RESIZE:
                continue
            choice = event.text.lower() if event.key == KeyCode.CHARACTER else ""
            if choice == "q" or event.key == KeyCode.ESCAPE:
                return
            if choice == "s":
                name = self._settings_prompt(stdscr, "Profile name:")
                if name in profiles:
                    self.profile_store.select_hotkeys(name)
                    self.hotkeys = self.profile_store.active_hotkeys()
            elif choice == "n":
                name = self._settings_prompt(stdscr, "New profile:")
                try:
                    self.profile_store.add_hotkey_profile(name)
                except ValueError:
                    pass
            elif choice == "r":
                new_name = self._settings_prompt(stdscr, "Rename active to:")
                try:
                    self.profile_store.rename_hotkey_profile(active, new_name)
                except ValueError:
                    pass
            elif choice == "d":
                try:
                    self.profile_store.delete_hotkey_profile(active)
                except ValueError:
                    pass
            elif choice == "e":
                action = self._settings_prompt(stdscr, "Action name:")
                if action in self.hotkeys:
                    binding = self._capture_hotkey(stdscr)
                    binding = binding.lower() if binding else ""
                    if binding == "+":
                        binding = "="
                    current = profiles[active]
                    used = {value: key for key, value in current.items() if key != action}
                    from src.ui.cli.input.hotkey_registry import get_hotkey_registry
    
                    plugin_keys = {
                        key for key, _description in get_hotkey_registry().get_by_category("plugin")
                    }
                    if binding and binding not in used and binding not in plugin_keys:
                        current[action] = binding
                        self.hotkeys = current.copy()
    
    
    
    def _capture_hotkey(self, stdscr: Any) -> str:
        """Capture a real global key combination while the settings UI owns input."""
        height, _width = stdscr.getmaxyx()
        self._settings_addstr(stdscr, min(height - 2, 2), "Press the new key combination (Esc cancels)...")
        stdscr.refresh()
        try:
            captured = keyboard.read_hotkey(suppress=False)
            return str(captured)
        except (AttributeError, OSError, RuntimeError):
            return self._settings_prompt(stdscr, "New key (e.g. ctrl+f8):")
    
    
    
    def _settings_mapping_ui(self, stdscr: Any) -> None:
        """Edit one-character score mappings in the active mapping profile."""
        profiles = self.profile_store.mapping_profiles()
        input_adapter = CursesInputAdapter(stdscr)
        while True:
            stdscr.erase()
            active = str(self.profile_store.data["active_mapping_profile"])
            mapping = profiles[active]
            self._settings_addstr(stdscr, 0, f"Mapping profile: {active}  {mapping}")
            self._settings_addstr(stdscr, 1, "[A]dd mapping [D]elete source [S]elect [N]ew [R]ename [X]delete profile [Q]uit")
            stdscr.refresh()
            event = input_adapter.read_event()
            if event.kind == InputKind.RESIZE:
                continue
            choice = event.text.lower() if event.key == KeyCode.CHARACTER else ""
            if choice == "q" or event.key == KeyCode.ESCAPE:
                return
            if choice == "a":
                source = self._settings_prompt(stdscr, "Source key:").upper()
                target = self._settings_prompt(stdscr, "Output key:").upper()
                clean = self.profile_store.validate_mapping({source: target})
                if clean:
                    mapping.update(clean)
            elif choice == "d":
                source = self._settings_prompt(stdscr, "Source key to delete:").upper()
                mapping.pop(source, None)
            elif choice == "s":
                name = self._settings_prompt(stdscr, "Profile name:")
                if name in profiles:
                    self.profile_store.select_mapping(name)
            elif choice == "n":
                name = self._settings_prompt(stdscr, "New profile:")
                try:
                    self.profile_store.add_mapping_profile(name)
                except ValueError:
                    pass
            elif choice == "r":
                new_name = self._settings_prompt(stdscr, "Rename active to:")
                try:
                    self.profile_store.rename_mapping_profile(active, new_name)
                except ValueError:
                    pass
            elif choice == "x":
                try:
                    self.profile_store.delete_mapping_profile(active)
                except ValueError:
                    pass
    
    
