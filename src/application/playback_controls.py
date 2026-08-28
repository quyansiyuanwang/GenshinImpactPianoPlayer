"""Playback parameter and mode commands."""

from __future__ import annotations

from src.application.state.state_machine import PlayerState as PSM_State
from src.application.host_protocol import ApplicationHost

class PlaybackControlsMixin(ApplicationHost):
    """Application command methods."""

    def toggle_play_pause(self) -> None:
        """Toggle between play and pause."""
        if not self.player:
            return
    
        state = self.player.get_state()
        if state == PSM_State.PLAYING:
            self.player.pause()
            # Force display update when paused
            self._display_score()
        elif state == PSM_State.PAUSED:
            self.player.resume()
            # Force display update when resumed
            self._display_score()
        elif state in (PSM_State.STOPPED, PSM_State.LOADED):
            self.player.play()
    
    
    
    def adjust_speed(self, delta: float) -> None:
        """Adjust playback speed."""
        if not self.player:
            return
    
        current = self.player._speed_multiplier
        new_speed = current + delta
        self.player.set_speed(new_speed)
        if self.player._speed_multiplier == current:
            # The player clamped the request: report the limit reached
            self._flash("Speed limit reached")
        else:
            # Always force display update
            self._request_refresh()
    
    
    
    def adjust_arpeggio(self, delta: float) -> None:
        """Adjust manual arpeggio interval and leave automatic mode."""
        if not self.player:
            return
    
        current = self.player._arpeggio_interval
        new_interval = current + delta
        self.player.set_arpeggio_interval(new_interval)
        # Always force display update
        self._request_refresh()
    
    
    
    def toggle_arpeggio_auto(self) -> None:
        """Toggle inferred arpeggio timing."""
        if not self.player:
            return
    
        self.player.set_arpeggio_auto(not self.player.get_arpeggio_auto())
        self._display_score()
    
    
    
    def adjust_interval(self, delta: float) -> None:
        """Adjust note interval rating."""
        if not self.player:
            return
    
        current = self.player._interval_rating
        new_interval = max(0.01, current + delta)  # Minimum 0.01s
        self.player.set_interval_rating(new_interval)
        # Always force display update
        self._request_refresh()
    
    
    
    def adjust_line_interval(self, delta: float) -> None:
        """Adjust line interval rating (N empty notes)."""
        if not self.player:
            return
    
        current = self.player._line_interval_rating
        new_rating = max(0.0, current + delta)
        self.player.set_line_interval_rating(new_rating)
        # Always force display update
        self._request_refresh()
    
    
    
    def adjust_space_interval(self, delta: float) -> None:
        """Adjust space interval rating (multiplier for rest notes)."""
        if not self.player:
            return
    
        current = self.player._space_interval_rating
        new_rating = max(0.0, current + delta)
        self.player.set_space_interval_rating(new_rating)
        # Always force display update
        self._request_refresh()
    
    
    
    def adjust_empty_line_interval(self, delta: float) -> None:
        """Adjust empty line interval rating (N empty notes for empty lines)."""
        if not self.player:
            return
    
        current = self.player._empty_line_interval_rating
        new_rating = max(0.0, current + delta)
        self.player.set_empty_line_interval_rating(new_rating)
    
        # Empty lines are included or dropped at parse time, so reparse to
        # apply the new rating to the score currently loaded in memory.
        self.reparse("Empty line interval updated")
    
    
    
    def adjust_segment_length(self, delta: int) -> None:
        """Adjust segment length (N notes per segment)."""
        if not self.player:
            return
    
        current = self.player._segment_length
        new_length = max(0, current + delta)
        self.player.set_segment_length(new_length)
        # Segment padding/truncation happens at parse time, so reparse to
        # apply the new length to the score currently loaded in memory.
        self.reparse("Segment length updated")
    
    
    
    def toggle_sustain(self) -> None:
        """Toggle sustain mode on/off."""
        if not self.player:
            return
    
        self.player.toggle_sustain()
        # Force display update to show new sustain state
        self._display_score()
    
    
    
    def toggle_segment_strict(self) -> None:
        """Toggle segment strict mode on/off."""
        if not self.player:
            return
    
        self.player.toggle_segment_strict()
        # Segment padding/truncation happens at parse time, so reparse to
        # apply the new strict mode to the score currently loaded in memory.
        self.reparse("Strict segment mode updated")
    
    
    
    def toggle_loop(self) -> None:
        """Toggle looping playback on/off."""
        if not self.player:
            return
    
        self.player.toggle_loop()
        self._flash(f"Loop {'ON' if self.player.get_loop_enabled() else 'OFF'}")
    
    
    
    def toggle_line_loop(self) -> None:
        """Toggle repeating the current line (practice aid)."""
        if not self.player:
            return
    
        self.player.toggle_line_loop()
        state = "ON" if self.player.get_line_loop_enabled() else "OFF"
        self._flash(f"Line repeat {state}")
    
    
    
    def toggle_output_lock(self) -> None:
        """Lock or unlock the simulated key output (panic switch)."""
        if not self.player:
            return
    
        self.player.toggle_output_lock()
        if self.player.get_output_locked():
            self._flash("Key output LOCKED - position keeps advancing")
        else:
            self._flash("Key output unlocked")
    
    
