"""Main score screen rendering."""

from __future__ import annotations

import time
from typing import Any, List
from src.application.config.constants import DISPLAY_REFRESH_RATE
from src.core.domain.note import Note, NoteType
from src.application.host_protocol import ApplicationHost
from src.ui.cli.main_renderer import MainRenderer

class MainScreenMixin(ApplicationHost):
    """Extracted application behavior."""

    def _flash(self, message: str, duration: float = 2.5) -> None:
        """Show a transient status message on the status line."""
        self._message = message
        self._message_until = time.time() + duration
        # Throttled: a held key that keeps flashing (e.g. speed limit) must not
        # flood the terminal; the main loop flushes the request within one tick.
        self._request_refresh()
    
    
    def _request_refresh(self) -> None:
        """Throttled refresh for hotkey threads.
    
        Renders immediately when the previous frame is old enough; otherwise
        flags a pending refresh that the main loop flushes within one tick, so
        held-down adjustment keys cannot flood the terminal with repaints.
        """
        now = time.time()
        if now - self.last_display_time >= DISPLAY_REFRESH_RATE:
            self.last_display_time = now
            self._display_score()
            return
        self._refresh_requested = True
    
    
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
        """Display the full score with current position highlighted using curses.
    
        The playback thread (progress callbacks), the keyboard hook thread
        (hotkey actions), and the main loop can all request a frame, so the
        curses work is serialized behind a lock.
        """
        if not self.display_active or not self.stdscr:
            return
    
        with self._render_lock:
            self._render_frame(self.stdscr)
    
    
    def _render_frame(self, stdscr: Any) -> None:
        """Render one full frame (caller must hold the render lock)."""
        MainRenderer().render(self, stdscr)

    def _format_note(self, note: Note) -> str:
        """Format a single note for display."""
        return note.display(show_rest_as_underscore=True)
    
    
    def _on_progress(
        self, current_line: int, total_lines: int, current_note: int, total_notes: int
    ) -> None:
        """Progress callback - refresh display with throttling."""
        current_time = time.time()
        # Only refresh at configured rate
        if current_time - self.last_display_time >= DISPLAY_REFRESH_RATE:
            self._display_score()
            self.last_display_time = current_time
    
