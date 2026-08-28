"""Core playback engine for GIPianoPlayer."""

import time
from threading import Event, RLock, Thread
from typing import Callable, List, Optional, Protocol

from src.application.config.constants import (
    MAX_ARPEGGIO_INTERVAL,
    MAX_INTERVAL,
    MAX_SPEED,
    MIN_ARPEGGIO_INTERVAL,
    MIN_INTERVAL,
    MIN_SPEED,
)
from src.core.domain.note import Note, NoteType
from src.core.domain.score import ParsedScore
from src.application.state.state_machine import (
    PlayerStateMachine,
    PlayerState as PSM_State,
    StateTransitionError,
)

# Re-export PlayerState for convenience
PlayerState = PSM_State

__all__ = ["Player", "PlayerState"]

SUSTAIN_RETRIGGER_INTERVAL = 0.02


class KeyboardControllerProtocol(Protocol):
    """Keyboard operations used by the playback engine."""

    def press_key(self, key: str) -> None: ...

    def release_key(self, key: str) -> None: ...

    def tap_key(self, key: str) -> None: ...

    def press_keys_simultaneously(self, keys: List[str]) -> None: ...


class Player:
    """Core playback engine that plays parsed scores."""

    def __init__(
        self, score: ParsedScore, keyboard_controller: KeyboardControllerProtocol
    ):
        self.score = score
        self.keyboard = keyboard_controller

        # Playback state machine
        self._state_machine = PlayerStateMachine()
        self._state_machine.transition_to(PSM_State.LOADING)
        # Score is loaded in __init__, so transition to LOADED
        self._state_machine.transition_to(PSM_State.LOADED)

        # Register state transition callbacks
        self._state_machine.on_transition(
            PSM_State.PLAYING, PSM_State.PAUSED, self._release_sustained_keys
        )
        self._state_machine.on_transition(
            PSM_State.PLAYING, PSM_State.STOPPED, self._release_sustained_keys
        )
        self._state_machine.on_exit(PSM_State.PLAYING, self._release_sustained_keys)

        # The cursor always points at the next note to play.  A flattened index
        # keeps cross-line seeks atomic and gives the end of a score one stable
        # sentinel value (len(self._positions)).
        self._positions = [
            (line_index, note_index)
            for line_index, line in enumerate(score.lines)
            for note_index, _note in enumerate(line)
        ]
        self._cursor = 0
        self._cursor_generation = 0

        # Prefix sums of line lengths give O(1) note-progress lookups for the
        # UI instead of rescanning the whole score on every frame.
        self._note_prefix = [0]
        for line in score.lines:
            self._note_prefix.append(self._note_prefix[-1] + len(line))
        self._control_lock = RLock()
        self._sustain_lock = RLock()

        # Control events
        self._pause_event = Event()
        self._stop_event = Event()
        self._wake_event = Event()
        self._pause_event.set()  # Not paused initially

        # Playback parameters (can be adjusted in real-time)
        self._speed_multiplier = score.config.speed_multiplier
        self._arpeggio_interval = score.config.arpeggio_interval
        self._arpeggio_auto = score.config.arpeggio_auto
        self._interval_rating = score.config.interval_rating
        self._line_interval_rating = score.config.line_interval_rating
        self._space_interval_rating = score.config.space_interval_rating
        self._empty_line_interval_rating = score.config.empty_line_interval_rating
        self._segment_length = score.config.segment_length
        self._segment_strict = score.config.segment_strict
        self._loop_enabled = score.config.loop

        # Sustain mode
        self._sustain_enabled = False
        self._sustained_keys: List[str] = []  # Keys currently being held

        # True when the last playback ran to the end of the score naturally
        self._playback_completed = False

        # Practice aid: repeat the current line until toggled off
        self._line_loop_enabled = False

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
        with self._control_lock:
            current_state = self._state_machine.current_state

            if current_state == PSM_State.PLAYING:
                return

            if current_state == PSM_State.PAUSED:
                self.resume()
                return

            try:
                if current_state in (PSM_State.LOADED, PSM_State.STOPPED):
                    self._state_machine.transition_to(PSM_State.BUFFERING)

                self._state_machine.transition_to(PSM_State.PLAYING)
                self._playback_completed = False
                self._stop_event.clear()
                self._pause_event.set()
                self._wake_event.set()
                self._playback_thread = Thread(target=self._playback_loop, daemon=True)
                self._playback_thread.start()
            except StateTransitionError as error:
                print(f"Cannot start playback: {error}")

    def pause(self) -> None:
        """Pause playback."""
        with self._control_lock:
            try:
                if self._state_machine.current_state == PSM_State.PLAYING:
                    self._state_machine.transition_to(PSM_State.PAUSED)
                    self._pause_event.clear()
                    self._wake_event.set()
            except StateTransitionError as error:
                print(f"Cannot pause: {error}")

    def resume(self) -> None:
        """Resume playback from paused state."""
        with self._control_lock:
            try:
                if self._state_machine.current_state == PSM_State.PAUSED:
                    self._state_machine.transition_to(PSM_State.PLAYING)
                    self._pause_event.set()
                    self._wake_event.set()
            except StateTransitionError as error:
                print(f"Cannot resume: {error}")

    def stop(self) -> None:
        """Stop playback and reset position."""
        with self._control_lock:
            try:
                current_state = self._state_machine.current_state
                if current_state in (PSM_State.PLAYING, PSM_State.PAUSED):
                    self._state_machine.transition_to(PSM_State.STOPPED)

                self._stop_event.set()
                self._pause_event.set()
                self._wake_event.set()
                playback_thread = self._playback_thread
            except StateTransitionError as error:
                print(f"Cannot stop: {error}")
                return

        if playback_thread and playback_thread.is_alive():
            playback_thread.join(timeout=2.0)

        with self._control_lock:
            self._cursor = 0
            self._cursor_generation += 1

    def set_speed(self, multiplier: float) -> None:
        """Set playback speed multiplier."""
        self._speed_multiplier = max(MIN_SPEED, min(MAX_SPEED, multiplier))
        # Wake an in-flight wait so the new speed applies immediately instead
        # of waiting for the current gap to finish.
        self._wake_event.set()

    def set_arpeggio_interval(self, interval: float) -> None:
        """Set a manual arpeggio interval in seconds."""
        with self._control_lock:
            self._arpeggio_interval = max(
                MIN_ARPEGGIO_INTERVAL, min(MAX_ARPEGGIO_INTERVAL, interval)
            )
            self._arpeggio_auto = False

    def set_arpeggio_auto(self, enabled: bool) -> None:
        """Choose inferred or manually configured arpeggio timing."""
        with self._control_lock:
            self._arpeggio_auto = enabled

    def get_arpeggio_auto(self) -> bool:
        """Return whether arpeggio timing is inferred automatically."""
        with self._control_lock:
            return self._arpeggio_auto

    def set_interval_rating(self, rating: float) -> None:
        """Set base interval rating."""
        self._interval_rating = max(MIN_INTERVAL, min(MAX_INTERVAL, rating))

    def set_line_interval_rating(self, rating: float) -> None:
        """Set line interval rating (N empty notes between lines)."""
        self._line_interval_rating = max(0.0, min(10.0, rating))

    def set_space_interval_rating(self, rating: float) -> None:
        """Set space interval rating (multiplier for rest notes)."""
        self._space_interval_rating = max(0.0, min(10.0, rating))

    def set_empty_line_interval_rating(self, rating: float) -> None:
        """Set empty line interval rating (N empty notes for empty lines)."""
        self._empty_line_interval_rating = max(0.0, min(10.0, rating))

    def set_segment_length(self, length: int | float) -> None:
        """Set segment length (N notes per segment, 0 = disabled)."""
        self._segment_length = max(0, min(20, int(length)))

    def toggle_sustain(self) -> None:
        """Toggle sustain mode on/off."""
        with self._sustain_lock:
            self._sustain_enabled = not self._sustain_enabled
            sustain_enabled = self._sustain_enabled
        # If turning off, release all sustained keys
        if not sustain_enabled:
            self._release_sustained_keys()

    def get_sustain_enabled(self) -> bool:
        """Get current sustain mode state."""
        with self._sustain_lock:
            return self._sustain_enabled

    def set_segment_strict(self, strict: bool) -> None:
        """Set segment strict mode explicitly."""
        with self._control_lock:
            self._segment_strict = bool(strict)

    def toggle_segment_strict(self) -> None:
        """Toggle segment strict mode on/off."""
        with self._control_lock:
            self._segment_strict = not self._segment_strict

    def set_loop_enabled(self, enabled: bool) -> None:
        """Choose whether playback restarts after the last note."""
        with self._control_lock:
            self._loop_enabled = bool(enabled)

    def toggle_loop(self) -> None:
        """Toggle looping playback on/off."""
        with self._control_lock:
            self._loop_enabled = not self._loop_enabled

    def get_loop_enabled(self) -> bool:
        """Get current loop mode state."""
        with self._control_lock:
            return self._loop_enabled

    def toggle_line_loop(self) -> None:
        """Toggle repeating the current line on/off (practice aid, not persisted)."""
        with self._control_lock:
            self._line_loop_enabled = not self._line_loop_enabled

    def get_line_loop_enabled(self) -> bool:
        """Get current line repeat state."""
        with self._control_lock:
            return self._line_loop_enabled

    def get_segment_strict(self) -> bool:
        """Get current segment strict mode state."""
        with self._control_lock:
            return self._segment_strict

    def get_state(self) -> PSM_State:
        """Get current player state.

        Returns:
            Current player state
        """
        with self._control_lock:
            return self._state_machine.current_state

    def is_playing(self) -> bool:
        """Check if player is currently playing.

        Returns:
            True if playing
        """
        return self.get_state() == PSM_State.PLAYING

    def is_paused(self) -> bool:
        """Check if player is paused.

        Returns:
            True if paused
        """
        return self.get_state() == PSM_State.PAUSED

    def is_stopped(self) -> bool:
        """Check if player is stopped.

        Returns:
            True if stopped
        """
        return self.get_state() == PSM_State.STOPPED

    def is_finished(self) -> bool:
        """Check if the last playback ran to the end of the score naturally.

        Returns:
            True if playback completed the whole score
        """
        with self._control_lock:
            return self._playback_completed

    def _release_sustained_keys(self) -> None:
        """Release all currently sustained keys."""
        with self._sustain_lock:
            keys = self._sustained_keys.copy()
            self._sustained_keys.clear()

        for key in keys:
            self.keyboard.release_key(key)

    def jump_to_line(self, line_number: int) -> None:
        """Jump to a specific line."""
        if not 0 <= line_number < len(self.score.lines):
            return

        for index, (current_line, _current_note) in enumerate(self._positions):
            if current_line == line_number:
                self._seek(index)
                return

    def jump_to_start(self) -> None:
        """Seek to the first note of the score."""
        self._seek(0)

    def jump_to_end(self) -> None:
        """Seek past the last note of the score."""
        self._seek(len(self._positions))

    def skip_forward_line(self) -> None:
        """Skip forward by 1 line."""
        with self._control_lock:
            current_line = self._current_line()
            target = next(
                (
                    index
                    for index, (line, _note) in enumerate(self._positions)
                    if line > current_line
                ),
                len(self._positions),
            )
        self._seek(target)

    def skip_backward_line(self) -> None:
        """Skip backward to the first note of the previous line."""
        with self._control_lock:
            current_line = self._current_line()
            target_line = current_line - 1
            if target_line < 0:
                target = 0
            else:
                target = next(
                    (
                        index
                        for index, (line, _note) in enumerate(self._positions)
                        if line == target_line
                    ),
                    0,
                )
        self._seek(target)

    def skip_forward_notes(self, notes: int = 1) -> None:
        """Skip forward by N notes."""
        with self._control_lock:
            target = min(len(self._positions), self._cursor + max(0, notes))
        self._seek(target)

    def skip_backward_notes(self, notes: int = 1) -> None:
        """Skip backward by N notes."""
        with self._control_lock:
            target = max(0, self._cursor - max(0, notes))
        self._seek(target)

    def get_progress(self) -> tuple[int, int]:
        """Get current progress as (current_line, total_lines)."""
        with self._control_lock:
            return (self._current_line(), len(self.score.lines))

    def get_position(self) -> tuple[int, int]:
        """Get the next pending position as zero-based line and note indexes."""
        with self._control_lock:
            if not self._positions:
                return (0, 0)
            if self._cursor >= len(self._positions):
                line, note = self._positions[-1]
                return (line, note + 1)
            return self._positions[self._cursor]

    def get_note_progress(self) -> tuple[int, int]:
        """Get note-level progress as (played_or_pending, total) note counts."""
        with self._control_lock:
            if not self._positions:
                return (0, 0)
            if self._cursor >= len(self._positions):
                return (self._note_prefix[-1], self._note_prefix[-1])
            line, note = self._positions[self._cursor]
            return (self._note_prefix[line] + note, self._note_prefix[-1])

    def _current_line(self) -> int:
        """Return the cursor line, including a stable value at score end."""
        if not self._positions:
            return 0
        if self._cursor >= len(self._positions):
            return len(self.score.lines)
        return self._positions[self._cursor][0]

    def _seek(self, target: int) -> None:
        """Atomically move the cursor and interrupt active playback waits."""
        with self._control_lock:
            target = min(max(target, 0), len(self._positions))
            if target == self._cursor:
                return
            self._cursor = target
            self._cursor_generation += 1
            self._playback_completed = False
        self._release_sustained_keys()
        self._wake_event.set()

    def _notify_progress(self, line: int, note: int, total_notes: int) -> None:
        """Notify the UI after a note has been dispatched."""
        if self._progress_callback:
            self._progress_callback(line, len(self.score.lines), note, total_notes)

    def _repeat_current_line(self, line_index: int) -> bool:
        """Rewind to the start of the current line when line repeat is active.

        Returns:
            True when the line end was handled by repeating the line
        """
        with self._control_lock:
            if not self._line_loop_enabled:
                return False
            first = next(
                (
                    index
                    for index, (line_no, _note) in enumerate(self._positions)
                    if line_no == line_index
                ),
                None,
            )
            if first is None:
                return False

        self._seek(first)
        with self._control_lock:
            generation = self._cursor_generation
        self._wait_repeated_before_next(
            self._interval_rating,
            int(self._line_interval_rating),
            generation,
            self._next_pending_keys(generation),
        )
        return True

    def _wait_repeated(self, duration: float, count: int, generation: int) -> bool:
        """Wait for repeated virtual rests, stopping at the first interruption."""
        for _ in range(max(0, count)):
            if not self._wait(duration, generation):
                return False
        return True

    def _wait(self, duration: float, generation: int) -> bool:
        """Wait while allowing pause, stop, seek, and speed changes to take effect."""
        # `remaining` is kept in unscaled seconds and re-scaled on every loop so
        # a speed change while waiting shortens or lengthens the same gap.
        remaining = max(0.0, duration)

        while remaining > 0:
            self._pause_event.wait()
            if self._stop_event.is_set():
                return False

            with self._control_lock:
                speed = self._speed_multiplier
            started = time.monotonic()
            interrupted = self._wake_event.wait(remaining / speed)
            elapsed = time.monotonic() - started
            self._wake_event.clear()

            if self._pause_event.is_set():
                remaining = max(0.0, remaining - elapsed * speed)

            with self._control_lock:
                if self._cursor_generation != generation:
                    return False
            if self._stop_event.is_set():
                return False
            if not interrupted:
                return True

        return True

    def _next_pending_keys(self, generation: int) -> List[str]:
        """Return the first physical keys of the next score event."""
        with self._control_lock:
            if self._cursor_generation != generation or self._cursor >= len(
                self._positions
            ):
                return []
            line_index, note_index = self._positions[self._cursor]
            note = self.score.lines[line_index][note_index]

        if note.type == NoteType.ARPEGGIO:
            return self._keys_from_item(note.keys[0]) if note.keys else []
        return [key for key in note.keys if isinstance(key, str) and key != " "]

    @staticmethod
    def _keys_from_item(item: str | Note) -> List[str]:
        """Flatten one arpeggio element into physical keys."""
        if isinstance(item, str):
            return [item]
        return [key for key in item.keys if isinstance(key, str)]

    def _wait_before_next(
        self, duration: float, generation: int, next_keys: List[str]
    ) -> bool:
        """Use an existing gap to release keys that must be retriggered next."""
        with self._sustain_lock:
            needs_early_release = bool(
                set(next_keys).intersection(self._sustained_keys)
            )
        if not needs_early_release:
            return self._wait(duration, generation)

        with self._control_lock:
            speed = self._speed_multiplier
        release_lead = min(SUSTAIN_RETRIGGER_INTERVAL, duration / speed)
        before_release = max(0.0, duration - release_lead * speed)
        if not self._wait(before_release, generation):
            return False

        with self._control_lock:
            if self._cursor_generation != generation:
                return False
        self._release_repeated_sustained_keys(next_keys)
        return self._wait(release_lead * speed, generation)

    def _wait_repeated_before_next(
        self, duration: float, count: int, generation: int, next_keys: List[str]
    ) -> bool:
        """Wait for virtual rests while preserving time for a repeated next key."""
        for _ in range(max(0, count - 1)):
            if not self._wait(duration, generation):
                return False
        return (
            self._wait_before_next(duration, generation, next_keys) if count else True
        )

    def _playback_loop(self) -> None:
        """Main playback loop running in separate thread."""
        while not self._stop_event.is_set():
            self._pause_event.wait()
            if self._stop_event.is_set():
                break

            with self._control_lock:
                if self._cursor >= len(self._positions):
                    if not (self._loop_enabled and self._positions):
                        break
                    # Loop mode: rewind to the first note and keep playing
                    self._cursor = 0
                    self._cursor_generation += 1
                    self._playback_completed = False
                    wrap_generation = self._cursor_generation
                else:
                    wrap_generation = None

            if wrap_generation is not None:
                # Leave a line-sized gap at the wrap point, releasing any keys
                # the first note must retrigger.
                self._release_sustained_keys()
                if not self._wait_repeated_before_next(
                    self._interval_rating,
                    int(self._line_interval_rating),
                    wrap_generation,
                    self._next_pending_keys(wrap_generation),
                ):
                    continue

                with self._control_lock:
                    if self._cursor_generation != wrap_generation:
                        continue

            with self._control_lock:
                if self._cursor >= len(self._positions):
                    break
                cursor = self._cursor
                generation = self._cursor_generation
                line_index, note_index = self._positions[cursor]
                line = self.score.lines[line_index]
                note = line[note_index]
                # Reserve the next cursor before dispatching input so a hotkey
                # observed during a key press always navigates from the next note.
                self._cursor += 1

            if note.type == NoteType.EMPTY_LINE:
                completed = self._wait_repeated(
                    self._interval_rating,
                    int(self._empty_line_interval_rating),
                    generation,
                )
            else:
                completed = self._play_note(note, generation)

            if not completed or self._stop_event.is_set():
                continue

            with self._control_lock:
                if self._cursor_generation != generation:
                    continue
                at_line_end = note_index == len(line) - 1

            self._notify_progress(line_index, note_index, len(line))

            if at_line_end:
                if self._repeat_current_line(line_index):
                    continue
                if line_index < len(self.score.lines) - 1:
                    self._wait_repeated_before_next(
                        self._interval_rating,
                        int(self._line_interval_rating),
                        generation,
                        self._next_pending_keys(generation),
                    )
            elif note.type == NoteType.SINGLE and note.keys[0] == " ":
                self._wait_before_next(
                    self._interval_rating * self._space_interval_rating,
                    generation,
                    self._next_pending_keys(generation),
                )
            elif note.type == NoteType.ARPEGGIO:
                self._wait_before_next(
                    self._interval_rating,
                    generation,
                    self._next_pending_keys(generation),
                )
            else:
                self._wait_before_next(
                    self._interval_rating,
                    generation,
                    self._next_pending_keys(generation),
                )

        with self._control_lock:
            if self._state_machine.current_state == PSM_State.PLAYING:
                try:
                    self._state_machine.transition_to(PSM_State.STOPPED)
                    self._playback_completed = True
                except StateTransitionError:
                    pass
            self._cursor = 0
            self._cursor_generation += 1

    def _play_note(self, note: Note, generation: int) -> bool:
        """Dispatch one score note and return False when it was interrupted."""
        if note.type == NoteType.SINGLE:
            key = note.keys[0]
            assert isinstance(key, str), "SINGLE note key must be string"
            if key != " ":
                return self._play_keys([key], generation)
            return True

        if note.type == NoteType.CHORD:
            return self._play_keys(
                [key for key in note.keys if isinstance(key, str)], generation
            )

        if note.type == NoteType.ARPEGGIO:
            interval = self._get_arpeggio_interval(len(note.keys))
            for index, item in enumerate(note.keys):
                keys = self._keys_from_item(item)
                if not self._play_keys(keys, generation):
                    return False
                if index < len(note.keys) - 1 and not self._wait_before_next(
                    interval,
                    generation,
                    self._keys_from_item(note.keys[index + 1]),
                ):
                    return False
        return True

    def _infer_arpeggio_interval(self, note_count: int) -> float:
        """Divide one note duration evenly across an arpeggio's elements."""
        if note_count <= 0:
            return 0.0
        with self._control_lock:
            return self._interval_rating / note_count

    def _get_arpeggio_interval(self, note_count: int) -> float:
        """Return the inferred or manually selected arpeggio spacing."""
        with self._control_lock:
            if not self._arpeggio_auto:
                return self._arpeggio_interval
        return self._infer_arpeggio_interval(note_count)

    def _play_keys(self, keys: List[str], _generation: int) -> bool:
        """Dispatch a single key or chord, honoring sustain mode."""
        if not keys:
            return True

        with self._sustain_lock:
            sustain_enabled = self._sustain_enabled
        if not sustain_enabled:
            if len(keys) == 1:
                self.keyboard.tap_key(keys[0])
            else:
                self.keyboard.press_keys_simultaneously(keys)
            return True

        self._release_sustained_keys()
        with self._sustain_lock:
            if not self._sustain_enabled:
                if len(keys) == 1:
                    self.keyboard.tap_key(keys[0])
                else:
                    self.keyboard.press_keys_simultaneously(keys)
                return True
            for key in keys:
                self.keyboard.press_key(key)
                self._sustained_keys.append(key)
        return True

    def _release_repeated_sustained_keys(self, next_keys: List[str]) -> None:
        """Release only held keys that the upcoming event must retrigger."""
        next_key_set = set(next_keys)
        with self._sustain_lock:
            keys_to_release = [
                key for key in self._sustained_keys if key in next_key_set
            ]
            self._sustained_keys = [
                key for key in self._sustained_keys if key not in next_key_set
            ]

        for key in keys_to_release:
            self.keyboard.release_key(key)
