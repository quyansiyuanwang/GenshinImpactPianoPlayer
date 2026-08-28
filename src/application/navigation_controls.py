"""Playback navigation and bookmark commands."""

from __future__ import annotations

from src.application.host_protocol import ApplicationHost

class NavigationControlsMixin(ApplicationHost):
    """Application command methods."""

    def skip_backward(self) -> None:
        """Skip backward by 1 note."""
        if not self.player:
            return
        self.player.skip_backward_notes(1)
        # Always force display update
        self._request_refresh()
    
    
    
    def skip_forward(self) -> None:
        """Skip forward by 1 note."""
        if not self.player:
            return
        self.player.skip_forward_notes(1)
        # Always force display update
        self._request_refresh()
    
    
    
    def skip_backward_large(self) -> None:
        """Skip backward by 1 line."""
        if not self.player:
            return
        self.player.skip_backward_line()
        # Always force display update
        self._request_refresh()
    
    
    
    def skip_forward_large(self) -> None:
        """Skip forward by 1 line."""
        if not self.player:
            return
        self.player.skip_forward_line()
        # Always force display update
        self._request_refresh()
    
    
    
    def set_range_a(self) -> None:
        """Mark the current position as the A-B range start."""
        if not self.player:
            return
    
        self.player.set_range_a()
        line = self.player.get_position()[0] + 1
        if self.player.is_range_active():
            self._flash(f"Range start set at line {line} - looping")
        else:
            self._flash(f"Range start set at line {line}")
    
    
    
    def set_range_b(self) -> None:
        """Mark the current position as the A-B range end."""
        if not self.player:
            return
    
        self.player.set_range_b()
        line = self.player.get_position()[0] + 1
        if self.player.is_range_active():
            self._flash(f"Range end set at line {line} - looping")
        else:
            self._flash(f"Range end set at line {line}")
    
    
    
    def clear_range(self) -> None:
        """Clear the A-B range."""
        if not self.player:
            return
    
        self.player.clear_range()
        self._flash("Range cleared")
    
    
    
    def set_bookmark(self) -> None:
        """Bookmark the current position."""
        if not self.player:
            return
    
        self.player.set_bookmark()
        bookmark = self.player.get_bookmark()
        if bookmark is None:
            self._flash("Nothing to bookmark - score is at its end")
        else:
            self._flash(f"Bookmark set at line {bookmark[0] + 1}")
    
    
    
    def jump_to_bookmark(self) -> None:
        """Jump back to the bookmarked position."""
        if not self.player:
            return
    
        if self.player.jump_to_bookmark():
            self._request_refresh()
            self._flash(
                f"Jumped to bookmark at line {self.player.get_position()[0] + 1}"
            )
        elif self.player.get_bookmark() is not None:
            self._flash("Bookmark position is outside the current score")
        else:
            self._flash("No bookmark set")
    
    
    
    def jump_to_start(self) -> None:
        """Jump to the first note of the score."""
        if not self.player:
            return
    
        self.player.jump_to_start()
        self._display_score()
    
    
    
    def jump_to_end(self) -> None:
        """Jump past the last note of the score."""
        if not self.player:
            return
    
        self.player.jump_to_end()
        self._display_score()
    
    
