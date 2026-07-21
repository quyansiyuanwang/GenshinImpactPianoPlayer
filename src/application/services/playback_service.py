"""Playback service for controlling music playback."""

from typing import Optional, Callable

from src.core.domain.score import ParsedScore
from src.core.player.player import Player
from src.core.keyboard.controller import KeyboardController
from src.application.state.state_machine import PlayerState as PSM_State


class PlaybackService:
    """Service for playback control operations."""

    def __init__(self) -> None:
        """Initialize playback service."""
        self._player: Optional[Player] = None
        self._keyboard_controller: Optional[KeyboardController] = None

    @property
    def player(self) -> Optional[Player]:
        """Get current player instance.

        Returns:
            Current Player or None
        """
        return self._player

    def initialize_player(
        self,
        score: ParsedScore,
        progress_callback: Optional[Callable[[int, int, int, int], None]] = None,
    ) -> Player:
        """Initialize a new player with a score.

        Args:
            score: Parsed score to play
            progress_callback: Optional callback for progress updates

        Returns:
            Initialized Player
        """
        # Create keyboard controller if not exists
        if self._keyboard_controller is None:
            self._keyboard_controller = KeyboardController()

        # Create player
        self._player = Player(score, self._keyboard_controller)

        # Set progress callback if provided
        if progress_callback:
            self._player.set_progress_callback(progress_callback)

        return self._player

    def play(self) -> None:
        """Start or resume playback.

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        self._player.play()

    def pause(self) -> None:
        """Pause playback.

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        self._player.pause()

    def resume(self) -> None:
        """Resume playback from paused state.

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        self._player.resume()

    def stop(self) -> None:
        """Stop playback and reset position.

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        self._player.stop()

    def toggle_play_pause(self) -> None:
        """Toggle between play and pause states.

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        state = self._player.get_state()

        if state == PSM_State.PLAYING:
            self.pause()
        elif state == PSM_State.PAUSED:
            self.resume()
        elif state in (PSM_State.STOPPED, PSM_State.LOADED):
            self.play()

    def is_playing(self) -> bool:
        """Check if playback is currently active.

        Returns:
            True if playing, False otherwise
        """
        if self._player is None:
            return False

        return self._player.is_playing()

    def is_paused(self) -> bool:
        """Check if playback is paused.

        Returns:
            True if paused, False otherwise
        """
        if self._player is None:
            return False

        return self._player.is_paused()

    def is_stopped(self) -> bool:
        """Check if playback is stopped.

        Returns:
            True if stopped, False otherwise
        """
        if self._player is None:
            return True

        return self._player.is_stopped()

    def get_progress(self) -> tuple[int, int]:
        """Get current playback progress.

        Returns:
            Tuple of (current_line, total_lines)

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        return self._player.get_progress()

    def skip_forward(self, notes: int = 1) -> None:
        """Skip forward by N notes.

        Args:
            notes: Number of notes to skip

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        for _ in range(notes):
            self._player.skip_forward_notes(1)

    def skip_backward(self, notes: int = 1) -> None:
        """Skip backward by N notes.

        Args:
            notes: Number of notes to skip

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        for _ in range(notes):
            self._player.skip_backward_notes(1)

    def skip_forward_line(self, lines: int = 1) -> None:
        """Skip forward by N lines.

        Args:
            lines: Number of lines to skip

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        for _ in range(lines):
            self._player.skip_forward_line()

    def skip_backward_line(self, lines: int = 1) -> None:
        """Skip backward by N lines.

        Args:
            lines: Number of lines to skip

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        for _ in range(lines):
            self._player.skip_backward_line()

    def jump_to_line(self, line_number: int) -> None:
        """Jump to a specific line.

        Args:
            line_number: Line number to jump to (0-based)

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        self._player.jump_to_line(line_number)

    def set_speed(self, multiplier: float) -> None:
        """Set playback speed multiplier.

        Args:
            multiplier: Speed multiplier (0.1 - 10.0)

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        self._player.set_speed(multiplier)

    def adjust_speed(self, delta: float) -> None:
        """Adjust playback speed by delta.

        Args:
            delta: Amount to adjust speed (positive or negative)

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        current = self._player._speed_multiplier
        new_speed = max(0.1, min(10.0, current + delta))
        self._player.set_speed(new_speed)

    def get_current_config(self) -> dict[str, float | int | bool]:
        """Get current playback configuration.

        Returns:
            Dictionary with current configuration values

        Raises:
            ValueError: If no player is initialized
        """
        if self._player is None:
            raise ValueError("No player initialized")

        return {
            "speed_multiplier": self._player._speed_multiplier,
            "arpeggio_interval": self._player._arpeggio_interval,
            "interval_rating": self._player._interval_rating,
            "line_interval_rating": self._player._line_interval_rating,
            "space_interval_rating": self._player._space_interval_rating,
            "empty_line_interval_rating": self._player._empty_line_interval_rating,
            "segment_length": self._player._segment_length,
            "segment_strict": self._player._segment_strict,
            "sustain_enabled": self._player.get_sustain_enabled(),
        }
