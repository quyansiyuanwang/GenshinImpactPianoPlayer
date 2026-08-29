"""Tests for the interactive settings widgets and screens."""

from pathlib import Path

from src.application.config.profiles import ProfileStore
from src.application.events import InputEvent, KeyCode
from src.ui.cli.components import TerminalSurface
from src.ui.cli.settings.screens import ScreenResult, SettingsRootScreen
from src.ui.cli.settings.session import SettingsSession
from src.ui.cli.settings.widgets import TableComponent


class Surface:
    def __init__(self, height: int = 24, width: int = 80) -> None:
        self.height = height
        self.width = width
        self.lines: list[tuple[int, int, str]] = []

    def getmaxyx(self) -> tuple[int, int]:
        return self.height, self.width

    def erase(self) -> None:
        self.lines.clear()

    def addstr(self, row: int, col: int, text: str, *_attrs: int) -> None:
        self.lines.append((row, col, text))

    def refresh(self) -> None:
        return


def event(value: str) -> InputEvent:
    return InputEvent.character(value)


def test_table_cursor_supports_navigation_and_paging() -> None:
    table = TableComponent(["Name"], [[str(index)] for index in range(30)])
    table.handle(InputEvent(InputEvent.character("x").kind, KeyCode.END))
    assert table.selected_row() == 29
    table.handle(InputEvent(InputEvent.character("x").kind, KeyCode.HOME))
    assert table.selected_row() == 0
    table.handle(InputEvent(InputEvent.character("x").kind, KeyCode.PAGE_DOWN))
    assert table.selected_row() == 8


def test_hotkey_enter_edits_selected_action(tmp_path: Path) -> None:
    session = SettingsSession(ProfileStore(tmp_path / "profiles.json"))
    screen = SettingsRootScreen(session)
    screen.handle(InputEvent.character("\t"))
    screen.handle(InputEvent(InputEvent.character("x").kind, KeyCode.DOWN))
    screen.handle(InputEvent(InputEvent.character("x").kind, KeyCode.ENTER))
    assert screen.editor is not None
    assert screen.editor.value == session.active_hotkeys["quit"]


def test_hotkey_conflict_keeps_editor_open(tmp_path: Path) -> None:
    session = SettingsSession(ProfileStore(tmp_path / "profiles.json"))
    screen = SettingsRootScreen(session)
    screen.handle(InputEvent.character("\t"))
    screen.handle(InputEvent(InputEvent.character("x").kind, KeyCode.ENTER))
    assert screen.editor is not None
    screen.editor.value = session.active_hotkeys["quit"]
    screen.editor.handle(InputEvent(InputEvent.character("x").kind, KeyCode.ENTER))
    assert screen.editor.active
    assert "already used" in screen.editor.error


def test_mapping_add_delete_and_cancel_rolls_back(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profiles.json")
    session = SettingsSession(store)
    screen = SettingsRootScreen(session)
    screen.mode = "mapping"
    screen._build_tables()
    screen.focus = "table"
    screen.handle(event("a"))
    assert screen.editor is not None
    screen.editor.value = "A=J"
    screen.editor.handle(InputEvent(InputEvent.character("x").kind, KeyCode.ENTER))
    assert session.active_mapping == {"A": "J"}
    screen.handle(InputEvent(InputEvent.character("x").kind, KeyCode.ESCAPE))
    assert session.active_mapping == {}


def test_render_recalculates_layout_after_resize(tmp_path: Path) -> None:
    session = SettingsSession(ProfileStore(tmp_path / "profiles.json"))
    screen = SettingsRootScreen(session)
    surface = Surface(24, 80)
    screen.render(TerminalSurface(surface), screen.layout.bounds)
    assert screen.layout.bounds.width == 80
    surface.width = 40
    surface.height = 12
    screen.handle(InputEvent.resize(40, 12))
    screen.render(TerminalSurface(surface), screen.layout.bounds)
    assert screen.layout.bounds == screen.layout.bounds.__class__(0, 0, 12, 40)
    assert screen.result == ScreenResult.NONE


def test_escape_after_save_keeps_committed_profile(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profiles.json")
    session = SettingsSession(store)
    session.add_mapping_profile("practice")
    session.save()
    session.set_mapping("A", "J")
    session.cancel()
    assert store.active_mapping() == {}
    assert list(store.mapping_profiles()) == ["default", "practice"]
