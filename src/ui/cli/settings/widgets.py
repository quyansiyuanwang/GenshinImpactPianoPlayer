"""Reusable cursor, table and inline editor widgets."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from src.application.events import InputEvent, InputKind, KeyCode
from src.ui.cli.components import Component, Rect, SurfaceLike
from src.ui.cli.settings.layout import clip
from src.ui.cli.terminal_text import cell_width, fit_cells


def _text(event: InputEvent, value: str) -> bool:
    return (
        event.kind == InputKind.KEY
        and event.key == KeyCode.CHARACTER
        and event.text.lower() == value
    )


class TableComponent(Component):
    """Selectable table with stable cursor and scrolling."""

    def __init__(
        self, columns: Sequence[str], rows: Sequence[Sequence[str]] = ()
    ) -> None:
        self.columns = list(columns)
        self.rows = [list(row) for row in rows]
        self.cursor = 0
        self.offset = 0
        self.focused = True
        self._visible_rows = 8

    def set_rows(self, rows: Sequence[Sequence[str]]) -> None:
        self.rows = [list(row) for row in rows]
        self.cursor = min(self.cursor, max(0, len(self.rows) - 1))
        self.offset = min(self.offset, self.cursor)

    def selected_row(self) -> int:
        return self.cursor

    def move(self, direction: int) -> None:
        self.cursor = min(max(0, self.cursor + direction), max(0, len(self.rows) - 1))

    def page(self, direction: int, page_size: int) -> None:
        self.move(direction * max(1, page_size))

    def handle(self, event: InputEvent) -> bool:
        if event.kind == InputKind.RESIZE:
            return True
        if event.kind != InputKind.KEY or event.key is None or not self.focused:
            return False
        if event.key == KeyCode.UP:
            self.move(-1)
            return True
        if event.key == KeyCode.DOWN:
            self.move(1)
            return True
        if event.key == KeyCode.PAGE_UP:
            self.page(-1, self._visible_rows)
            return True
        if event.key == KeyCode.PAGE_DOWN:
            self.page(1, self._visible_rows)
            return True
        if event.key == KeyCode.HOME:
            self.cursor = 0
            return True
        if event.key == KeyCode.END:
            self.cursor = max(0, len(self.rows) - 1)
            return True
        return False

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        if rect.height <= 0 or rect.width <= 0:
            return
        widths = self._column_widths(rect.width)
        header = "  " + "  ".join(
            fit_cells(name, max(0, widths[index] - 1))
            for index, name in enumerate(self.columns)
        )
        surface.addstr(rect.top, rect.left, clip(header, rect.width))
        body_height = max(0, rect.height - 1)
        self._visible_rows = max(1, body_height)
        if self.cursor < self.offset:
            self.offset = self.cursor
        if self.cursor >= self.offset + body_height:
            self.offset = self.cursor - body_height + 1
        for visible, row in enumerate(
            self.rows[self.offset : self.offset + body_height]
        ):
            index = self.offset + visible
            marker = "> " if index == self.cursor and self.focused else "  "
            cells = [
                fit_cells(
                    row[column] if column < len(row) else "",
                    max(0, widths[column] - 1),
                )
                for column in range(len(widths))
            ]
            line = clip(marker + "  ".join(cells), rect.width)
            if index == self.cursor and self.focused:
                surface.addstr(
                    rect.top + visible + 1,
                    rect.left,
                    line,
                    getattr(surface, "highlight_attr", 0),
                )
            else:
                surface.addstr(rect.top + visible + 1, rect.left, line)

    def _column_widths(self, width: int) -> list[int]:
        if not self.columns:
            return []
        weights = [max(8, cell_width(column) + 2) for column in self.columns]
        remaining = max(1, width - 2 * len(weights) - 2)
        total = sum(weights)
        return [max(4, remaining * weight // total) for weight in weights]


class ProfileList(TableComponent):
    """One-column profile selector."""

    def __init__(self, names: Sequence[str]) -> None:
        super().__init__(["Profiles"], [[name] for name in names])

    @property
    def selected_name(self) -> str | None:
        return self.rows[self.cursor][0] if self.rows else None


class BindingTable(TableComponent):
    """Action/binding/description table."""

    def __init__(self, actions: Sequence[tuple[str, str, str]]) -> None:
        super().__init__(["Action", "Binding", "Description"], actions)


class MappingTable(TableComponent):
    """Source/output mapping table."""

    def __init__(self, rows: Sequence[tuple[str, str]]) -> None:
        super().__init__(
            ["Source key", "Output key", "Status"],
            [[source, target, "active"] for source, target in rows],
        )


class InlineEditor(Component):
    """Small text editor rendered near the selected row."""

    def __init__(
        self,
        value: str = "",
        title: str = "Edit",
        on_submit: Callable[[str], str | None] | None = None,
    ) -> None:
        self.value = value
        self.title = title
        self.on_submit = on_submit
        self.active = True
        self.error = ""

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        if not self.active or rect.height <= 0:
            return
        surface.addstr(
            rect.top,
            rect.left,
            clip(f"{self.title}: {self.value}", rect.width),
            getattr(surface, "highlight_attr", 0),
        )
        if self.error and rect.height > 1:
            surface.addstr(rect.top + 1, rect.left, clip(self.error, rect.width))

    def handle(self, event: InputEvent) -> bool:
        if event.kind == InputKind.RESIZE:
            return True
        if event.kind != InputKind.KEY or event.key is None:
            return False
        if event.key == KeyCode.ESCAPE:
            self.active = False
            return True
        if event.key == KeyCode.ENTER:
            error = self.on_submit(self.value) if self.on_submit else None
            if error:
                self.error = error
            else:
                self.active = False
            return True
        if event.key == KeyCode.BACKSPACE:
            self.value = self.value[:-1]
            return True
        if event.key == KeyCode.CHARACTER and event.text and event.text.isprintable():
            self.value += event.text
            return True
        return False


class ModalEditor(InlineEditor):
    """Alias retaining an explicit modal vocabulary for callers."""


class KeyCaptureComponent(InlineEditor):
    """Capture one normalized binding supplied by an event source."""

    def __init__(self, on_submit: Callable[[str], str | None] | None = None) -> None:
        super().__init__("", "Recording key (press key, Enter to confirm)", on_submit)
        self.capturing = True

    def handle(self, event: InputEvent) -> bool:
        if event.kind == InputKind.KEY and event.key == KeyCode.ESCAPE:
            self.active = False
            return True
        if (
            self.capturing
            and event.kind == InputKind.KEY
            and event.key is not None
            and event.key not in {KeyCode.ENTER, KeyCode.BACKSPACE}
        ):
            self.value = self._binding_name(event)
            self.capturing = False
            return True
        return super().handle(event)

    @staticmethod
    def _binding_name(event: InputEvent) -> str:
        if event.key == KeyCode.CHARACTER:
            name = event.text.lower()
        elif event.key == KeyCode.FUNCTION:
            name = f"f{event.function_number}"
        else:
            name = event.key.value if event.key else ""
        prefix = "+".join(sorted(event.modifiers))
        return f"{prefix}+{name}" if prefix else name


class StatusBar(Component):
    """One-line feedback area shared by all settings screens."""

    def __init__(self, message: str = "") -> None:
        self.message = message

    def set_message(self, message: str) -> None:
        self.message = message

    def render(self, surface: SurfaceLike, rect: Rect) -> None:
        if rect.height:
            surface.addstr(rect.top, rect.left, clip(self.message, rect.width))
