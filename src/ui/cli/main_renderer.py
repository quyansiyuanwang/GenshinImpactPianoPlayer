"""Responsive playback-screen renderer."""

from __future__ import annotations

import curses
import os
import time
from typing import Any

from src.application.config.constants import DISPLAY_LINES_AFTER, DISPLAY_LINES_BEFORE
from src.ui.cli.components import Rect, TerminalSurface
from src.ui.cli.main_layout import MainLayout
from src.ui.cli.playback_context import (
    configuration_lines,
    control_hints,
    visible_configuration,
)
from src.ui.cli.playlist.widgets import PlaylistTable
from src.ui.cli.terminal_text import cell_width, clip_cells


class MainRenderer:
    """Render a complete frame from geometry calculated for this exact frame."""

    def render(self, host: Any, stdscr: Any) -> None:
        surface = TerminalSurface(stdscr)
        try:
            height, width = surface.getmaxyx()
            surface.erase()
            layout = MainLayout.from_size(
                height, width, has_playlist=bool(getattr(host, "playlist", None))
            )
            if not host.score:
                surface.addstr(0, 0, "No score loaded.")
                return

            self._render_header(host, surface, layout.header)
            self._render_score(host, surface, layout.score)
            if layout.playlist.height > 0:
                self._render_playlist(host, surface, layout.playlist)
            self._render_status(host, surface, layout.status)
            self._render_details(host, surface, layout.details)
            self._render_footer(host, surface, layout.footer)
        finally:
            surface.refresh()

    def _render_header(self, host: Any, surface: TerminalSurface, rect: Rect) -> None:
        if rect.height <= 0:
            return
        surface.addstr(
            rect.top,
            rect.left,
            clip_cells("GIPianoPlayer - Command Line Interface", rect.width - 1),
            curses.A_BOLD,
        )
        if rect.height >= 2:
            surface.addstr(rect.top + 1, rect.left, "=" * max(0, rect.width - 1))
        if rect.height >= 3:
            name = os.path.basename(host.file_path)
            metadata = f"File: {name}  |  Lines: {len(host.score.lines)}"
            surface.addstr(
                rect.top + 2, rect.left, clip_cells(metadata, rect.width - 1)
            )

    def _render_score(self, host: Any, surface: TerminalSurface, rect: Rect) -> None:
        if rect.height <= 0 or rect.width <= 1:
            return
        current_line = host.player.get_progress()[0] if host.player else 0
        current_note = host.player.get_position()[1] if host.player else 0
        top = rect.top
        available = rect.height
        warnings = host.score.warnings
        if warnings and available:
            preview = "; ".join(warnings[:2])
            message = f"Warning: {len(warnings)} unknown characters ignored: {preview}"
            surface.addstr(
                top,
                rect.left,
                clip_cells(message, rect.width - 1),
                curses.color_pair(2),
            )
            top += 1
            available -= 1
        if available <= 0:
            return

        total = len(host.score.lines)
        start, end, hidden_before, hidden_after = self._score_window(
            total, current_line, available
        )
        row = top
        if hidden_before:
            surface.addstr(
                row,
                rect.left,
                clip_cells(f"  ... {start} lines above ...", rect.width - 1),
            )
            row += 1
        for line_index in range(start, end):
            line = host.score.lines[line_index]
            line_number = f"[{line_index + 1:3d}] "
            target_row = row
            if line_index != current_line:
                text = line_number + host._format_score_line(line)
                attribute = curses.color_pair(1) if line_index < current_line else 0
                surface.addstr(
                    target_row, rect.left, clip_cells(text, rect.width - 1), attribute
                )
                row += 1
                continue
            self._render_current_line(
                host,
                surface,
                target_row,
                rect.left,
                rect.width,
                line_number,
                line,
                current_note,
            )
            row += 1
        if hidden_after and row < top + available:
            surface.addstr(
                row,
                rect.left,
                clip_cells(f"  ... {total - end} lines below ...", rect.width - 1),
            )

    def _score_window(
        self, total: int, current: int, available: int
    ) -> tuple[int, int, bool, bool]:
        maximum = DISPLAY_LINES_BEFORE + 1 + DISPLAY_LINES_AFTER
        capacity = min(maximum, available, total)
        start, end = self._score_bounds(total, current, capacity)
        hidden_before = start > 0
        hidden_after = end < total
        indicator_rows = int(hidden_before) + int(hidden_after)
        capacity = min(maximum, max(1, available - indicator_rows), total)
        start, end = self._score_bounds(total, current, capacity)
        return start, end, start > 0, end < total

    def _score_bounds(self, total: int, current: int, capacity: int) -> tuple[int, int]:
        if total <= 0 or capacity <= 0:
            return 0, 0
        current = min(max(0, current), total - 1)
        before = min(DISPLAY_LINES_BEFORE, current, capacity - 1)
        after = min(DISPLAY_LINES_AFTER, total - current - 1, capacity - before - 1)
        remaining = capacity - before - after - 1
        extra_after = min(remaining, total - current - after - 1)
        after += extra_after
        remaining -= extra_after
        before += min(remaining, current - before)
        return current - before, current + after + 1

    def _render_current_line(
        self,
        host: Any,
        surface: TerminalSurface,
        row: int,
        left: int,
        width: int,
        line_number: str,
        line: Any,
        current_note: int,
    ) -> None:
        surface.addstr(row, left, clip_cells(line_number, width - 1))
        column = left + cell_width(line_number)
        right = left + width - 1
        for note_index, note in enumerate(line):
            note_text = host._format_note(note) + " "
            clipped = clip_cells(note_text, right - column)
            if not clipped:
                break
            if note_index < current_note:
                attribute = curses.color_pair(2)
            elif note_index == current_note:
                attribute = curses.color_pair(3) | curses.A_BOLD
            else:
                attribute = 0
            surface.addstr(row, column, clipped, attribute)
            column += cell_width(clipped)

    def _render_playlist(self, host: Any, surface: TerminalSurface, rect: Rect) -> None:
        if not getattr(host, "playlist", None):
            return
        if rect.left > 0:
            for row in range(rect.top, rect.top + rect.height):
                surface.addstr(row, rect.left - 1, "│")
        PlaylistTable(host.playlist).render(surface, rect)

    def _render_status(self, host: Any, surface: TerminalSurface, rect: Rect) -> None:
        if rect.height <= 0 or rect.width <= 1:
            return
        finished = bool(host.player and host.player.is_finished())
        state = (
            "FINISHED"
            if finished
            else (host.player.get_state().value.upper() if host.player else "STOPPED")
        )
        current_line, total_lines = (
            host.player.get_progress() if host.player else (0, len(host.score.lines))
        )
        played_notes, total_notes = (
            host.player.get_note_progress() if host.player else (0, 0)
        )
        if finished:
            played_notes = total_notes
        fraction = (
            played_notes / total_notes if total_notes else (1.0 if finished else 0.0)
        )
        bar_width = max(0, rect.width - 1)
        filled = min(bar_width, max(0, int(bar_width * fraction)))
        surface.addstr(rect.top, rect.left, "=" * filled + "-" * (bar_width - filled))
        if rect.height < 2:
            return
        percent = 100.0 if finished else fraction * 100
        shown_line = total_lines if finished else min(total_lines, current_line + 1)
        message = (
            f"Status: {state} | Line {shown_line}/{total_lines} | "
            f"Note {played_notes}/{total_notes} | Progress: {percent:.1f}%"
        )
        if host._message and time.time() < host._message_until:
            message += f" | {host._message}"
        surface.addstr(rect.top + 1, rect.left, clip_cells(message, rect.width - 1))

    def _render_details(self, host: Any, surface: TerminalSurface, rect: Rect) -> None:
        if rect.height <= 0 or not host.player:
            return
        details = visible_configuration(configuration_lines(host), rect.height)
        for offset, detail in enumerate(details[: rect.height]):
            surface.addstr(
                rect.top + offset, rect.left, clip_cells(detail, rect.width - 1)
            )

    def _render_footer(self, host: Any, surface: TerminalSurface, rect: Rect) -> None:
        if rect.height <= 0:
            return
        for offset, hint in enumerate(control_hints(host)[: rect.height]):
            surface.addstr(
                rect.top + offset, rect.left, clip_cells(hint, rect.width - 1)
            )
