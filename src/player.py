"""Core playback engine for GIPianoPlayer."""

import time
from enum import Enum
from threading import Thread, Event
from typing import Optional, Callable, List
from src.parser import ParsedScore, Note, NoteType
from src.keyboard_controller import KeyboardController


class PlayerState(Enum):
    """Playback state."""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class Player:
    """Core playback engine that plays parsed scores."""

    def __init__(self, score: ParsedScore, keyboard_controller: KeyboardController):
        self.score = score
        self.keyboard = keyboard_controller

        # Playback state
        self._state = PlayerState.STOPPED
        self._current_line = 0
        self._current_note = 0

        # Control events
        self._pause_event = Event()
        self._stop_event = Event()
        self._pause_event.set()  # Not paused initially

        # Playback parameters (can be adjusted in real-time)
        self._speed_multiplier = score.config.speed_multiplier
        self._arpeggio_interval = score.config.arpeggio_interval
        self._interval_rating = score.config.interval_rating
        self._line_interval_rating = score.config.line_interval_rating
        self._space_interval_rating = score.config.space_interval_rating
        self._empty_line_interval_rating = score.config.empty_line_interval_rating
        self._segment_length = score.config.segment_length
        self._segment_strict = score.config.segment_strict

        # Sustain mode
        self._sustain_enabled = False
        self._sustained_keys: List[str] = []  # Keys currently being held

        # Playback thread
        self._playback_thread: Optional[Thread] = None

        # Progress callback
        self._progress_callback: Optional[Callable[[int, int, int, int], None]] = None

    def set_progress_callback(
        self, callback: Callable[[int, int, int, int], None]
    ) -> None:
        """Set callback for progress updates: (current_line, total_lines, current_note, total_notes)."""
        self._progress_callback = callback

    def play(self) -> None:
        """Start playback from current position."""
        if self._state == PlayerState.PLAYING:
            return

        if self._state == PlayerState.PAUSED:
            self.resume()
            return

        self._state = PlayerState.PLAYING
        self._stop_event.clear()
        self._pause_event.set()

        self._playback_thread = Thread(target=self._playback_loop, daemon=True)
        self._playback_thread.start()

    def pause(self) -> None:
        """Pause playback."""
        if self._state == PlayerState.PLAYING:
            self._state = PlayerState.PAUSED
            self._pause_event.clear()
            # Release sustained keys when pausing
            self._release_sustained_keys()

    def resume(self) -> None:
        """Resume playback from paused state."""
        if self._state == PlayerState.PAUSED:
            self._state = PlayerState.PLAYING
            self._pause_event.set()

    def stop(self) -> None:
        """Stop playback and reset position."""
        self._state = PlayerState.STOPPED
        self._stop_event.set()
        self._pause_event.set()  # Unblock if paused

        # Release sustained keys when stopping
        self._release_sustained_keys()

        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=2.0)
            # If thread still alive after timeout, it will be cleaned up on next play()
            # This prevents blocking indefinitely

        self._current_line = 0
        self._current_note = 0

    def set_speed(self, multiplier: float) -> None:
        """Set playback speed multiplier."""
        if not isinstance(multiplier, (int, float)):
            raise TypeError(
                f"Speed multiplier must be numeric, got {type(multiplier).__name__}"
            )
        self._speed_multiplier = max(0.1, min(10.0, multiplier))

    def set_arpeggio_interval(self, interval: float) -> None:
        """Set arpeggio interval in seconds."""
        if not isinstance(interval, (int, float)):
            raise TypeError(
                f"Arpeggio interval must be numeric, got {type(interval).__name__}"
            )
        self._arpeggio_interval = max(0.01, min(1.0, interval))

    def set_interval_rating(self, rating: float) -> None:
        """Set base interval rating."""
        if not isinstance(rating, (int, float)):
            raise TypeError(
                f"Interval rating must be numeric, got {type(rating).__name__}"
            )
        self._interval_rating = max(0.01, min(5.0, rating))

    def set_line_interval_rating(self, rating: float) -> None:
        """Set line interval rating (N empty notes between lines)."""
        if not isinstance(rating, (int, float)):
            raise TypeError(
                f"Line interval rating must be numeric, got {type(rating).__name__}"
            )
        self._line_interval_rating = max(0.0, min(10.0, rating))

    def set_space_interval_rating(self, rating: float) -> None:
        """Set space interval rating (multiplier for rest notes)."""
        if not isinstance(rating, (int, float)):
            raise TypeError(
                f"Space interval rating must be numeric, got {type(rating).__name__}"
            )
        self._space_interval_rating = max(0.0, min(10.0, rating))

    def set_empty_line_interval_rating(self, rating: float) -> None:
        """Set empty line interval rating (N empty notes for empty lines)."""
        if not isinstance(rating, (int, float)):
            raise TypeError(
                f"Empty line interval rating must be numeric, got {type(rating).__name__}"
            )
        self._empty_line_interval_rating = max(0.0, min(10.0, rating))

    def set_segment_length(self, length: int) -> None:
        """Set segment length (N notes per segment, 0 = disabled)."""
        if not isinstance(length, (int, float)):
            raise TypeError(
                f"Segment length must be numeric, got {type(length).__name__}"
            )
        self._segment_length = max(0, min(20, int(length)))

    def toggle_sustain(self) -> None:
        """Toggle sustain mode on/off."""
        self._sustain_enabled = not self._sustain_enabled
        # If turning off, release all sustained keys
        if not self._sustain_enabled:
            self._release_sustained_keys()

    def get_sustain_enabled(self) -> bool:
        """Get current sustain mode state."""
        return self._sustain_enabled

    def toggle_segment_strict(self) -> None:
        """Toggle segment strict mode on/off."""
        self._segment_strict = not self._segment_strict

    def get_segment_strict(self) -> bool:
        """Get current segment strict mode state."""
        return self._segment_strict

    def _release_sustained_keys(self) -> None:
        """Release all currently sustained keys."""
        if not self._sustained_keys:
            return

        for key in self._sustained_keys:
            self.keyboard.release_key(key)
        self._sustained_keys.clear()
        # Add a small delay after releasing to ensure the game/software registers it
        time.sleep(0.02)  # 20ms delay after releasing keys

    def jump_to_line(self, line_number: int) -> None:
        """Jump to a specific line."""
        if 0 <= line_number < len(self.score.lines):
            self._current_line = line_number
            self._current_note = 0

    def skip_forward_line(self) -> None:
        """Skip forward by 1 line."""
        if self._current_line < len(self.score.lines) - 1:
            self._current_line += 1
            self._current_note = 0

    def skip_backward_line(self) -> None:
        """Skip backward by 1 line."""
        if self._current_line > 0:
            self._current_line -= 1
            self._current_note = 0

    def skip_forward_notes(self, notes: int = 1) -> None:
        """Skip forward by N notes."""
        remaining = notes
        while remaining > 0 and self._current_line < len(self.score.lines):
            line = self.score.lines[self._current_line]
            notes_in_line = len(line) - self._current_note

            if remaining >= notes_in_line:
                # Skip to next line
                remaining -= notes_in_line
                self._current_line += 1
                self._current_note = 0
                # Check bounds after incrementing
                if self._current_line >= len(self.score.lines):
                    # Reached end, clamp to last valid position
                    self._current_line = len(self.score.lines) - 1
                    self._current_note = len(self.score.lines[self._current_line]) - 1
                    remaining = 0
            else:
                # Skip within current line
                self._current_note += remaining
                remaining = 0

    def skip_backward_notes(self, notes: int = 1) -> None:
        """Skip backward by N notes."""
        remaining = notes
        while remaining > 0 and (self._current_line > 0 or self._current_note > 0):
            if remaining <= self._current_note:
                # Skip within current line
                self._current_note -= remaining
                remaining = 0
            else:
                # Skip to previous line
                remaining -= self._current_note
                if self._current_line > 0:
                    self._current_line -= 1
                    # Set to last note of previous line (len - 1, not len)
                    self._current_note = max(
                        0, len(self.score.lines[self._current_line]) - 1
                    )
                else:
                    self._current_note = 0
                    remaining = 0

    def get_progress(self) -> tuple[int, int]:
        """Get current progress as (current_line, total_lines)."""
        return (self._current_line, len(self.score.lines))

    def get_state(self) -> PlayerState:
        """Get current playback state."""
        return self._state

    def _playback_loop(self) -> None:
        """Main playback loop running in separate thread."""
        while self._current_line < len(self.score.lines):
            # Check if stopped
            if self._stop_event.is_set():
                break

            # Wait if paused
            self._pause_event.wait()

            # Check again after unpausing
            if self._stop_event.is_set():
                break

            # Play current line
            line = self.score.lines[self._current_line]
            self._play_line(line)

            # Line interval (N empty notes between lines)
            if (
                self._current_line < len(self.score.lines) - 1
                and self._line_interval_rating > 0
            ):
                # Simulate N empty notes
                for _ in range(int(self._line_interval_rating)):
                    if self._stop_event.is_set():
                        break
                    self._pause_event.wait()
                    self._sleep(self._interval_rating)

            # Move to next line
            self._current_line += 1
            self._current_note = 0

        # Playback finished
        self._state = PlayerState.STOPPED
        self._current_line = 0
        self._current_note = 0

    def _play_line(self, line: list[Note]) -> None:
        """Play a single line of notes."""
        # Check if this is an empty line
        if len(line) == 1 and line[0].type == NoteType.EMPTY_LINE:
            # Empty line - simulate N empty notes
            for _ in range(int(self._empty_line_interval_rating)):
                if self._stop_event.is_set():
                    break
                self._pause_event.wait()
                self._sleep(self._interval_rating)
            return

        for i, note in enumerate(line):
            # Check if stopped
            if self._stop_event.is_set():
                break

            # Wait if paused
            self._pause_event.wait()

            self._current_note = i

            # Update progress for every note to show real-time playback
            if self._progress_callback:
                self._progress_callback(
                    self._current_line,
                    len(self.score.lines),
                    self._current_note,
                    len(line),
                )

            # Play the note
            self._play_note(note)

            # Every note (including space, chord, arpeggio) should have interval after it
            # Except the last note in the line
            if i < len(line) - 1:
                # Use space_interval_rating for rest notes, normal interval for others
                if note.type == NoteType.SINGLE and note.keys[0] == " ":
                    self._sleep(self._interval_rating * self._space_interval_rating)
                else:
                    self._sleep(self._interval_rating)

    def _play_note(self, note: Note) -> None:
        """Play a single note (single, chord, or arpeggio)."""
        if note.type == NoteType.SINGLE:
            # For SINGLE notes, keys[0] is always a string
            key = note.keys[0]
            assert isinstance(key, str), "SINGLE note key must be string"

            if key == " ":
                # Space is an empty note (rest) - no action needed, just skip
                # In sustain mode, keep holding previous keys
                pass
            else:
                # Non-rest note: release previous sustained keys if in sustain mode
                if self._sustain_enabled:
                    self._release_sustained_keys()
                    # Press and hold the new key
                    self.keyboard.press_key(key)
                    self._sustained_keys.append(key)
                else:
                    # Normal tap
                    self.keyboard.tap_key(key)

        elif note.type == NoteType.CHORD:
            # For CHORD notes, all keys are strings
            chord_keys = [k for k in note.keys if isinstance(k, str)]

            # Non-rest note: release previous sustained keys if in sustain mode
            if self._sustain_enabled:
                self._release_sustained_keys()
                # Press and hold all keys in the chord
                for key in chord_keys:
                    self.keyboard.press_key(key)
                    self._sustained_keys.append(key)
            else:
                # Normal chord
                self.keyboard.press_keys_simultaneously(chord_keys)

        elif note.type == NoteType.ARPEGGIO:
            # Non-rest note: release ALL previous sustained keys before starting arpeggio
            if self._sustain_enabled:
                self._release_sustained_keys()

            for idx, key in enumerate(note.keys):
                if isinstance(key, str):
                    if self._sustain_enabled:
                        # For arpeggio in sustain mode, release previous note in THIS arpeggio
                        if idx > 0:
                            prev_key = note.keys[idx - 1]
                            if (
                                isinstance(prev_key, str)
                                and prev_key in self._sustained_keys
                            ):
                                self.keyboard.release_key(prev_key)
                                self._sustained_keys.remove(prev_key)
                                # Small delay after releasing to ensure registration
                                time.sleep(0.02)
                        # Press and hold current note
                        self.keyboard.press_key(key)
                        self._sustained_keys.append(key)
                    else:
                        self.keyboard.tap_key(key)
                elif isinstance(key, Note):
                    # Nested chord within arpeggio
                    if self._sustain_enabled:
                        # Release previous arpeggio note before nested chord
                        if idx > 0:
                            prev_key = note.keys[idx - 1]
                            if (
                                isinstance(prev_key, str)
                                and prev_key in self._sustained_keys
                            ):
                                self.keyboard.release_key(prev_key)
                                self._sustained_keys.remove(prev_key)
                                # Small delay after releasing to ensure registration
                                time.sleep(0.02)
                            elif isinstance(prev_key, Note):
                                # Previous was also a chord, release all its keys
                                for pk in prev_key.keys:
                                    if (
                                        isinstance(pk, str)
                                        and pk in self._sustained_keys
                                    ):
                                        self.keyboard.release_key(pk)
                                        self._sustained_keys.remove(pk)
                                time.sleep(0.02)

                        # Play nested chord (will add its keys to sustained_keys)
                        chord_keys = [k for k in key.keys if isinstance(k, str)]
                        for chord_key in chord_keys:
                            self.keyboard.press_key(chord_key)
                            self._sustained_keys.append(chord_key)
                    else:
                        # Normal nested chord
                        chord_keys = [k for k in key.keys if isinstance(k, str)]
                        self.keyboard.press_keys_simultaneously(chord_keys)

                # Arpeggio interval (except after last key)
                if idx < len(note.keys) - 1:
                    self._sleep(self._arpeggio_interval)

    def _sleep(self, duration: float) -> None:
        """Sleep for specified duration adjusted by speed multiplier."""
        if duration > 0:
            time.sleep(duration / self._speed_multiplier)
