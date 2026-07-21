"""Display renderer for CLI interface."""

import curses
from typing import List, Any

from src.core.domain.note import Note, NoteType
from src.core.domain.score import ParsedScore


class DisplayRenderer:
    """Handles rendering of the score and UI elements in the terminal."""

    def __init__(self, stdscr: Any) -> None:
        """Initialize display renderer.

        Args:
            stdscr: Curses screen object
        """
        self.stdscr = stdscr
        self._initialize_colors()

    def _initialize_colors(self) -> None:
        """Initialize color pairs for display."""
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)  # Played notes
        curses.init_pair(2, curses.COLOR_RED, -1)  # Current line played
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Current note

    def clear(self) -> None:
        """Clear the screen."""
        self.stdscr.clear()

    def refresh(self) -> None:
        """Refresh the screen."""
        self.stdscr.refresh()

    def get_size(self) -> tuple[int, int]:
        """Get terminal size.

        Returns:
            Tuple of (height, width)
        """
        height, width = self.stdscr.getmaxyx()
        return (height, width)

    def render_score(
        self,
        score: ParsedScore,
        current_line: int,
        current_note: int,
        player_config: dict[str, Any],
    ) -> None:
        """Render the complete score display.

        Args:
            score: Parsed score to display
            current_line: Current line number
            current_note: Current note index
            player_config: Player configuration dictionary
        """
        self.clear()

        height, width = self.get_size()
        separator_width = min(width - 1, 100)

        # Build config lines
        config_lines = self._build_config_lines(player_config)

        # Calculate layout
        header_lines = 2  # Title + separator
        footer_lines = (
            2  # Blank + separator
            + 2  # Status + blank
            + 2  # Config title + separator
            + len(config_lines)
            + 1  # Blank after config
            + 3  # Control lines
        )

        score_viewport_height = height - header_lines - footer_lines
        score_viewport_height = max(1, score_viewport_height)

        # Render header
        y = 0
        y = self._render_header(y, width, separator_width)

        # Render score
        y = self._render_score_lines(
            y,
            score,
            current_line,
            current_note,
            score_viewport_height,
            width,
            player_config,
        )

        # Render footer
        self._render_footer(
            y, width, separator_width, current_line, score, player_config, config_lines
        )

        self.refresh()

    def _build_config_lines(self, player_config: dict[str, Any]) -> List[str]:
        """Build configuration display lines.

        Args:
            player_config: Player configuration

        Returns:
            List of configuration lines
        """
        config_lines = [
            f"  Speed: {player_config.get('speed_multiplier', 1.0):.2f}x",
            f"  Arpeggio Interval: {player_config.get('arpeggio_interval', 0.05):.3f}s",
            f"  Note Interval: {player_config.get('interval_rating', 0.2):.3f}s",
            f"  Line Interval: {player_config.get('line_interval_rating', 1.0):.1f}",
            f"  Space Interval: {player_config.get('space_interval_rating', 1.0):.1f}x",
        ]

        empty_line_rating = player_config.get("empty_line_interval_rating", 0.0)
        if empty_line_rating > 0:
            config_lines.append(f"  Empty Line Interval: {empty_line_rating:.1f}")

        segment_length = player_config.get("segment_length", 0)
        if segment_length > 0:
            segment_strict = player_config.get("segment_strict", False)
            strict_text = " (Strict)" if segment_strict else ""
            config_lines.append(f"  Segment Length: {segment_length}{strict_text}")

        sustain = player_config.get("sustain_enabled", False)
        if sustain:
            config_lines.append("  Sustain: ON")

        return config_lines

    def _render_header(self, y: int, width: int, separator_width: int) -> int:
        """Render header section.

        Args:
            y: Starting y position
            width: Terminal width
            separator_width: Separator line width

        Returns:
            Next y position
        """
        title = "GIPianoPlayer"
        self.stdscr.addstr(y, (width - len(title)) // 2, title, curses.A_BOLD)
        y += 1
        self.stdscr.addstr(y, 0, "=" * separator_width)
        y += 1
        return y

    def _render_score_lines(
        self,
        y: int,
        score: ParsedScore,
        current_line: int,
        current_note: int,
        viewport_height: int,
        width: int,
        player_config: dict[str, Any],
    ) -> int:
        """Render score lines in viewport.

        Args:
            y: Starting y position
            score: Parsed score
            current_line: Current line number
            current_note: Current note index
            viewport_height: Height of score viewport
            width: Terminal width
            player_config: Player configuration

        Returns:
            Next y position
        """
        total_lines = score.get_total_lines()

        # Calculate viewport range
        lines_before = 3

        start_line = max(0, current_line - lines_before)
        end_line = min(total_lines, start_line + viewport_height)

        # Adjust if near end
        if end_line == total_lines:
            start_line = max(0, end_line - viewport_height)

        # Render lines
        for i in range(start_line, end_line):
            if y >= viewport_height + 2:
                break

            line = score.get_line(i)
            line_text = self._format_score_line(line, player_config)

            # Determine color
            if i < current_line:
                color = curses.color_pair(1)  # Cyan - played
            elif i == current_line:
                color = curses.color_pair(2)  # Red - current line
                # Highlight current note
                line_text = self._highlight_current_note(line, current_note, line_text)
            else:
                color = curses.A_NORMAL  # Normal - not played

            # Add line number and content
            line_display = f"{i + 1:4d} | {line_text}"
            if len(line_display) > width - 1:
                line_display = line_display[: width - 1]

            try:
                self.stdscr.addstr(y, 0, line_display, color)
            except curses.error:
                pass

            y += 1

        return y

    def _format_score_line(
        self, line: List[Note], player_config: dict[str, Any]
    ) -> str:
        """Format a score line for display.

        Args:
            line: List of notes
            player_config: Player configuration

        Returns:
            Formatted line string
        """
        # Check if empty line
        if len(line) == 1 and line[0].type == NoteType.EMPTY_LINE:
            display_empty = player_config.get("empty_line_interval_rating", 0) > 0
            return "[Empty Line] " if display_empty else ""

        result = ""
        for note in line:
            result += note.display(show_rest_as_underscore=True) + " "

        return result.rstrip()

    def _highlight_current_note(
        self, line: List[Note], current_note: int, line_text: str
    ) -> str:
        """Highlight the current note in the line.

        Args:
            line: List of notes
            current_note: Current note index
            line_text: Formatted line text

        Returns:
            Line text with current note highlighted
        """
        # This is a simplified version - full implementation would need
        # to track character positions for each note
        return line_text

    def _render_footer(
        self,
        y: int,
        width: int,
        separator_width: int,
        current_line: int,
        score: ParsedScore,
        player_config: dict[str, Any],
        config_lines: List[str],
    ) -> None:
        """Render footer section.

        Args:
            y: Starting y position
            width: Terminal width
            separator_width: Separator width
            current_line: Current line number
            score: Parsed score
            player_config: Player configuration
            config_lines: Configuration display lines
        """
        height, _ = self.get_size()

        # Start from bottom
        y = height - 1

        # Control hints (bottom)
        try:
            self.stdscr.addstr(y, 0, "  F8: Play/Pause  F2: Quit  F5: Reload  F9: Save")
            y -= 1
            self.stdscr.addstr(y, 0, "  +/-: Speed  [/]: Arpeggio  ,/.: Interval")
            y -= 1
            self.stdscr.addstr(y, 0, "  ↑/↓: Line Interval  PgUp/PgDn: Segment")
            y -= 1
        except curses.error:
            pass

        # Blank line
        y -= 1

        # Config section
        for line in reversed(config_lines):
            try:
                self.stdscr.addstr(y, 0, line)
                y -= 1
            except curses.error:
                pass

        try:
            self.stdscr.addstr(y, 0, "-" * separator_width)
            y -= 1
            self.stdscr.addstr(y, 0, "Configuration:")
            y -= 1
        except curses.error:
            pass

        # Blank line
        y -= 1

        # Status line
        total_lines = score.get_total_lines()
        progress_pct = (current_line / total_lines * 100) if total_lines > 0 else 0
        status = f"Line {current_line + 1}/{total_lines} ({progress_pct:.1f}%)"

        try:
            self.stdscr.addstr(y, 0, status)
            y -= 1
        except curses.error:
            pass

        # Separator
        try:
            self.stdscr.addstr(y, 0, "=" * separator_width)
        except curses.error:
            pass

    def show_message(self, message: str) -> None:
        """Show a temporary message.

        Args:
            message: Message to display
        """
        height, width = self.get_size()
        y = height - 1

        try:
            # Clear line
            self.stdscr.addstr(y, 0, " " * (width - 1))
            # Show message
            self.stdscr.addstr(y, 0, message[: width - 1])
            self.refresh()
        except curses.error:
            pass
