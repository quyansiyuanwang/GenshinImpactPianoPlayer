"""Interactive settings screens backed by ``InputEvent`` only."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum

from src.application.config.constants import DEFAULT_HOTKEYS
from src.application.events import InputEvent, InputKind, KeyCode
from src.ui.cli.components import Rect, SurfaceLike
from src.ui.cli.settings.layout import SettingsLayout, clip
from src.ui.cli.settings.session import SettingsSession
from src.ui.cli.settings.widgets import (
    BindingTable,
    InlineEditor,
    KeyCaptureComponent,
    MappingTable,
    ProfileList,
    StatusBar,
    TableComponent,
)


class ScreenResult(Enum):
    NONE = "none"
    SAVED = "saved"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class SettingsRootScreen:
    """Full-screen, keyboard-driven settings editor."""

    def __init__(
        self,
        session: SettingsSession,
        on_save: Callable[[SettingsSession], str | None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> None:
        self.session = session
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.mode = "hotkeys"
        self.focus = "profiles"
        self.layout = SettingsLayout.from_size(0, 0)
        self.editor: InlineEditor | None = None
        self.status = StatusBar("Enter edit   Tab switch panel   N new   R rename   D delete   S save   Q quit")
        self.result = ScreenResult.NONE
        self._build_tables()

    def _build_tables(self) -> None:
        if self.mode == "hotkeys":
            rows = []
            descriptions = {
                action: action.replace("_", " ").title() for action in DEFAULT_HOTKEYS
            }
            for action, binding in self.session.active_hotkeys.items():
                rows.append((action, binding, descriptions.get(action, action)))
            self.profile_list = ProfileList(list(self.session.hotkeys))
            self.profile_list.cursor = list(self.session.hotkeys).index(self.session.active_hotkey_profile)
            self.table: TableComponent = BindingTable(rows)
        else:
            self.profile_list = ProfileList(list(self.session.mappings))
            self.profile_list.cursor = list(self.session.mappings).index(self.session.active_mapping_profile)
            self.table = MappingTable(self.session.mapping_items)

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        height, width = surface.getmaxyx()
        self.layout = SettingsLayout.from_size(height, width)
        surface.erase()
        if width < 30 or height < 8:
            surface.addstr(0, 0, clip("Settings: terminal too small (minimum 30x8)", width))
            surface.addstr(min(height - 1, 2), 0, clip("Resize the terminal to continue", width))
            surface.refresh()
            return
        title = f" Settings  /  {'Hotkey bindings' if self.mode == 'hotkeys' else 'Score mapping'} "
        surface.addstr(0, 0, clip(title, width))
        surface.addstr(1, 0, clip("=" * max(0, width - 1), width))
        self.profile_list.focused = self.focus == "profiles"
        self.table.focused = self.focus == "table"
        surface.addstr(self.layout.sidebar.top, self.layout.sidebar.left, clip("[H] Hotkeys  [M] Mapping", self.layout.sidebar.width))
        profile_rect = Rect(
            self.layout.sidebar.top + 1,
            self.layout.sidebar.left,
            max(0, self.layout.sidebar.height - 1),
            self.layout.sidebar.width,
        )
        self.profile_list.render(surface, profile_rect)
        self.table.render(surface, self.layout.content)
        if self.editor and self.editor.active:
            editor_rect = self._editor_rect()
            self.editor.render(surface, editor_rect)
        surface.addstr(self.layout.footer.top, 0, clip("-" * max(0, width - 1), width))
        surface.addstr(self.layout.footer.top + 1, 0, clip(self.status.message, width))
        surface.refresh()

    def handle(self, event: InputEvent) -> bool:
        if event.kind == InputKind.RESIZE:
            if self.editor:
                self.editor.handle(event)
            return True
        if self.editor and self.editor.active:
            handled = self.editor.handle(event)
            if not self.editor.active:
                self.editor = None
            return handled
        if event.kind != InputKind.KEY or event.key is None:
            return False
        if event.key == KeyCode.ESCAPE:
            self.session.cancel()
            self.result = ScreenResult.CANCELLED
            if self.on_cancel:
                self.on_cancel()
            return True
        if _character(event, "q"):
            self.result = ScreenResult.CLOSED
            return True
        if _character(event, "s"):
            return self._save()
        if _character(event, "?"):
            self.status.set_message("↑↓ move  PgUp/PgDn page  Home/End jump  Enter/E edit  Tab focus  N/R/D profile  A mapping  S save  Esc cancel")
            return True
        if _is_tab(event):
            self.focus = "table" if self.focus == "profiles" else "profiles"
            return True
        if self.focus == "profiles":
            if self.profile_list.handle(event):
                return True
            if event.key == KeyCode.ENTER:
                self._select_profile()
                return True
        else:
            if self.table.handle(event):
                return True
            if event.key == KeyCode.ENTER or _character(event, "e"):
                self._edit_selected()
                return True
            if self.mode == "mapping" and _character(event, "a"):
                self._add_mapping()
                return True
            if self.mode == "mapping" and _character(event, "d"):
                self._delete_mapping()
                return True
        if _character(event, "n"):
            self._new_profile()
            return True
        if _character(event, "r"):
            self._rename_profile()
            return True
        if _character(event, "d"):
            self._delete_profile()
            return True
        if _character(event, "m") and self.focus == "profiles":
            self.mode = "mapping"
            self._build_tables()
            return True
        if _character(event, "h") and self.focus == "profiles":
            self.mode = "hotkeys"
            self._build_tables()
            return True
        return False

    def _select_profile(self) -> None:
        name = self.profile_list.selected_name
        if not name:
            return
        try:
            if self.mode == "hotkeys":
                self.session.select_hotkey_profile(name)
            else:
                self.session.select_mapping_profile(name)
            self._build_tables()
            self.status.set_message(f"Selected profile: {name}")
        except KeyError as error:
            self.status.set_message(str(error))

    def _edit_selected(self) -> None:
        row = self.table.selected_row()
        if row >= len(self.table.rows):
            return
        if self.mode == "hotkeys":
            action, binding, _ = self.table.rows[row]

            def submit(value: str) -> str | None:
                try:
                    self.session.set_hotkey(action, value)
                except (KeyError, ValueError) as error:
                    self.status.set_message(str(error))
                    return str(error)
                self._build_tables()
                self.status.set_message(f"Updated {action}")
                return None

            self.editor = KeyCaptureComponent(submit)
            self.editor.value = binding
        else:
            source, target, _ = self.table.rows[row]

            def submit(value: str) -> str | None:
                try:
                    self.session.set_mapping(source, value)
                except ValueError as error:
                    self.status.set_message(str(error))
                    return str(error)
                self._build_tables()
                self.status.set_message(f"Mapped {source} to {value.upper()}")
                return None

            self.editor = InlineEditor(target, f"Output for {source}", submit)

    def _add_mapping(self) -> None:
        def submit(value: str) -> str | None:
            parts = [part.strip() for part in value.split("=")]
            if len(parts) != 2:
                return "Enter mapping as SOURCE=TARGET"
            try:
                self.session.set_mapping(parts[0], parts[1])
            except ValueError as error:
                return str(error)
            self._build_tables()
            self.status.set_message("Mapping added")
            return None

        self.editor = InlineEditor("", "New mapping SOURCE=TARGET", submit)

    def _new_profile(self) -> None:
        def submit(value: str) -> str | None:
            try:
                if self.mode == "hotkeys":
                    self.session.add_hotkey_profile(value)
                else:
                    self.session.add_mapping_profile(value)
            except ValueError as error:
                return str(error)
            self._build_tables()
            self.status.set_message(f"Created profile: {value.strip()}")
            return None

        self.editor = InlineEditor("", "New profile", submit)

    def _activate_profile_cursor(self) -> None:
        name = self.profile_list.selected_name
        if name and name != (self.session.active_hotkey_profile if self.mode == "hotkeys" else self.session.active_mapping_profile):
            self._select_profile()

    def _rename_profile(self) -> None:
        self._activate_profile_cursor()
        current = self.session.active_hotkey_profile if self.mode == "hotkeys" else self.session.active_mapping_profile

        def submit(value: str) -> str | None:
            try:
                if self.mode == "hotkeys":
                    self.session.rename_hotkey_profile(value)
                else:
                    self.session.rename_mapping_profile(value)
            except ValueError as error:
                return str(error)
            self._build_tables()
            self.status.set_message(f"Renamed profile to {value.strip()}")
            return None

        self.editor = InlineEditor(current, "Rename profile", submit)

    def _delete_profile(self) -> None:
        self._activate_profile_cursor()
        try:
            if self.mode == "hotkeys":
                self.session.delete_hotkey_profile()
            else:
                self.session.delete_mapping_profile()
            self._build_tables()
            self.status.set_message("Profile deleted")
        except ValueError as error:
            self.status.set_message(str(error))

    def _delete_mapping(self) -> None:
        if self.table.selected_row() >= len(self.table.rows):
            return
        source = self.table.rows[self.table.selected_row()][0]
        self.session.delete_mapping(source)
        self._build_tables()
        self.status.set_message(f"Deleted mapping {source}")

    def _save(self) -> bool:
        try:
            if self.on_save:
                error = self.on_save(self.session)
                if error:
                    self.status.set_message(error)
                    return True
            else:
                self.session.save()
        except (OSError, ValueError) as error:
            self.status.set_message(str(error))
            return True
        self.result = ScreenResult.SAVED
        self.status.set_message("Settings saved")
        return True

    def _editor_rect(self) -> Rect:
        row = self.table.selected_row() + self.layout.content.top + 2
        max_row = self.layout.footer.top - 2
        top = min(max(self.layout.content.top, row), max(self.layout.content.top, max_row))
        return Rect(top, self.layout.content.left, min(2, self.layout.content.height), self.layout.content.width)


class HotkeyProfileScreen(SettingsRootScreen):
    """Explicit hotkey page type for integrations and tests."""

    def __init__(self, session: SettingsSession, **kwargs: object) -> None:
        super().__init__(session, **kwargs)  # type: ignore[arg-type]
        self.mode = "hotkeys"
        self._build_tables()


class MappingProfileScreen(SettingsRootScreen):
    """Explicit mapping page type for integrations and tests."""

    def __init__(self, session: SettingsSession, **kwargs: object) -> None:
        super().__init__(session, **kwargs)  # type: ignore[arg-type]
        self.mode = "mapping"
        self._build_tables()


def _character(event: InputEvent, value: str) -> bool:
    return event.kind == InputKind.KEY and event.key == KeyCode.CHARACTER and event.text.lower() == value


def _is_tab(event: InputEvent) -> bool:
    return _character(event, "\t")
