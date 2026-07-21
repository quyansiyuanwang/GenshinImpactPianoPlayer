"""State machine framework for GIPianoPlayer.

Provides a unified state management system for:
- Application lifecycle
- Player control
- Plugin lifecycle
- Configuration management
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Generic, TypeVar

StateT = TypeVar("StateT", bound=Enum)


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


class StateMachine(ABC, Generic[StateT]):
    """Abstract base class for state machines.

    Subclasses must define:
    - State enum type
    - Valid transitions
    - Transition handlers
    """

    def __init__(self, initial_state: StateT) -> None:
        """Initialize state machine.

        Args:
            initial_state: Starting state
        """
        self._current_state = initial_state
        self._previous_state: StateT | None = None
        self._transition_callbacks: dict[
            tuple[StateT, StateT], list[Callable[[], None]]
        ] = {}
        self._state_enter_callbacks: dict[StateT, list[Callable[[], None]]] = {}
        self._state_exit_callbacks: dict[StateT, list[Callable[[], None]]] = {}

    @property
    def current_state(self) -> StateT:
        """Get current state."""
        return self._current_state

    @property
    def previous_state(self) -> StateT | None:
        """Get previous state."""
        return self._previous_state

    @abstractmethod
    def _get_valid_transitions(self) -> dict[StateT, list[StateT]]:
        """Get valid state transitions.

        Returns:
            Dictionary mapping each state to list of valid next states
        """

    def can_transition_to(self, target_state: StateT) -> bool:
        """Check if transition to target state is valid.

        Args:
            target_state: Target state

        Returns:
            True if transition is valid
        """
        valid_transitions = self._get_valid_transitions()
        return target_state in valid_transitions.get(self._current_state, [])

    def transition_to(self, target_state: StateT) -> None:
        """Transition to target state.

        Args:
            target_state: Target state

        Raises:
            StateTransitionError: If transition is invalid
        """
        if not self.can_transition_to(target_state):
            msg = f"Invalid transition: {self._current_state} -> {target_state}"
            raise StateTransitionError(msg)

        # Execute exit callbacks for current state
        for callback in self._state_exit_callbacks.get(self._current_state, []):
            callback()

        # Execute transition callbacks
        transition_key = (self._current_state, target_state)
        for callback in self._transition_callbacks.get(transition_key, []):
            callback()

        # Update state
        self._previous_state = self._current_state
        self._current_state = target_state

        # Execute enter callbacks for new state
        for callback in self._state_enter_callbacks.get(target_state, []):
            callback()

    def on_transition(
        self,
        from_state: StateT,
        to_state: StateT,
        callback: Callable[[], None],
    ) -> None:
        """Register callback for specific transition.

        Args:
            from_state: Source state
            to_state: Target state
            callback: Callback to execute during transition
        """
        key = (from_state, to_state)
        if key not in self._transition_callbacks:
            self._transition_callbacks[key] = []
        self._transition_callbacks[key].append(callback)

    def on_enter(self, state: StateT, callback: Callable[[], None]) -> None:
        """Register callback for entering a state.

        Args:
            state: State to watch
            callback: Callback to execute when entering state
        """
        if state not in self._state_enter_callbacks:
            self._state_enter_callbacks[state] = []
        self._state_enter_callbacks[state].append(callback)

    def on_exit(self, state: StateT, callback: Callable[[], None]) -> None:
        """Register callback for exiting a state.

        Args:
            state: State to watch
            callback: Callback to execute when exiting state
        """
        if state not in self._state_exit_callbacks:
            self._state_exit_callbacks[state] = []
        self._state_exit_callbacks[state].append(callback)


class AppState(Enum):
    """Application lifecycle states."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    TERMINATED = "terminated"


class AppStateMachine(StateMachine[AppState]):
    """State machine for application lifecycle."""

    def __init__(self) -> None:
        """Initialize application state machine."""
        super().__init__(AppState.UNINITIALIZED)
        self._error_info: str | None = None

    def _get_valid_transitions(self) -> dict[AppState, list[AppState]]:
        """Get valid state transitions."""
        return {
            AppState.UNINITIALIZED: [AppState.INITIALIZING],
            AppState.INITIALIZING: [AppState.READY, AppState.ERROR],
            AppState.READY: [AppState.RUNNING, AppState.SHUTTING_DOWN],
            AppState.RUNNING: [AppState.PAUSED, AppState.SHUTTING_DOWN, AppState.ERROR],
            AppState.PAUSED: [AppState.RUNNING, AppState.SHUTTING_DOWN],
            AppState.ERROR: [AppState.SHUTTING_DOWN],
            AppState.SHUTTING_DOWN: [AppState.TERMINATED],
            AppState.TERMINATED: [],
        }

    def set_error(self, error_info: str) -> None:
        """Set error state with information.

        Args:
            error_info: Error description
        """
        self._error_info = error_info
        if self.can_transition_to(AppState.ERROR):
            self.transition_to(AppState.ERROR)

    def get_error_info(self) -> str | None:
        """Get error information.

        Returns:
            Error description if in error state
        """
        return self._error_info if self._current_state == AppState.ERROR else None


class PlayerState(Enum):
    """Player control states."""

    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    BUFFERING = "buffering"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class PlayerStateMachine(StateMachine[PlayerState]):
    """State machine for player control."""

    def __init__(self) -> None:
        """Initialize player state machine."""
        super().__init__(PlayerState.UNLOADED)

    def _get_valid_transitions(self) -> dict[PlayerState, list[PlayerState]]:
        """Get valid state transitions."""
        return {
            PlayerState.UNLOADED: [PlayerState.LOADING],
            PlayerState.LOADING: [PlayerState.LOADED, PlayerState.ERROR],
            PlayerState.LOADED: [PlayerState.BUFFERING, PlayerState.LOADING],
            PlayerState.BUFFERING: [PlayerState.PLAYING, PlayerState.ERROR],
            PlayerState.PLAYING: [
                PlayerState.PAUSED,
                PlayerState.STOPPED,
                PlayerState.BUFFERING,
                PlayerState.ERROR,
            ],
            PlayerState.PAUSED: [PlayerState.PLAYING, PlayerState.STOPPED],
            PlayerState.STOPPED: [PlayerState.LOADING, PlayerState.BUFFERING],
            PlayerState.ERROR: [PlayerState.LOADING],
        }


class PluginState(Enum):
    """Plugin lifecycle states."""

    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"


class PluginStateMachine(StateMachine[PluginState]):
    """State machine for plugin lifecycle."""

    def __init__(self) -> None:
        """Initialize plugin state machine."""
        super().__init__(PluginState.UNREGISTERED)

    def _get_valid_transitions(self) -> dict[PluginState, list[PluginState]]:
        """Get valid state transitions."""
        return {
            PluginState.UNREGISTERED: [PluginState.REGISTERED],
            PluginState.REGISTERED: [PluginState.INITIALIZING, PluginState.UNLOADING],
            PluginState.INITIALIZING: [PluginState.INITIALIZED, PluginState.ERROR],
            PluginState.INITIALIZED: [PluginState.ENABLED, PluginState.UNLOADING],
            PluginState.ENABLED: [PluginState.DISABLED, PluginState.UNLOADING],
            PluginState.DISABLED: [PluginState.ENABLED, PluginState.UNLOADING],
            PluginState.ERROR: [PluginState.UNLOADING],
            PluginState.UNLOADING: [PluginState.UNLOADED],
            PluginState.UNLOADED: [],
        }


class ConfigState(Enum):
    """Configuration management states."""

    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    MODIFIED = "modified"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    SAVING = "saving"
    SAVED = "saved"
    ERROR = "error"


class ConfigStateMachine(StateMachine[ConfigState]):
    """State machine for configuration management."""

    def __init__(self) -> None:
        """Initialize config state machine."""
        super().__init__(ConfigState.UNLOADED)
        self._change_history: list[dict[str, Any]] = []

    def _get_valid_transitions(self) -> dict[ConfigState, list[ConfigState]]:
        """Get valid state transitions."""
        return {
            ConfigState.UNLOADED: [ConfigState.LOADING, ConfigState.VALIDATING],
            ConfigState.LOADING: [ConfigState.LOADED, ConfigState.ERROR],
            ConfigState.LOADED: [
                ConfigState.MODIFIED,
                ConfigState.VALIDATING,
                ConfigState.SAVING,
            ],
            ConfigState.MODIFIED: [ConfigState.VALIDATING, ConfigState.LOADING],
            ConfigState.VALIDATING: [ConfigState.VALID, ConfigState.INVALID],
            ConfigState.VALID: [ConfigState.SAVING, ConfigState.MODIFIED],
            ConfigState.INVALID: [ConfigState.MODIFIED, ConfigState.LOADING],
            ConfigState.SAVING: [ConfigState.SAVED, ConfigState.ERROR],
            ConfigState.SAVED: [ConfigState.MODIFIED, ConfigState.LOADING],
            ConfigState.ERROR: [ConfigState.LOADING],
        }

    def record_change(self, change: dict[str, Any]) -> None:
        """Record configuration change.

        Args:
            change: Change information
        """
        self._change_history.append(change)

    def get_change_history(self) -> list[dict[str, Any]]:
        """Get configuration change history.

        Returns:
            List of changes
        """
        return self._change_history.copy()

    def clear_history(self) -> None:
        """Clear change history."""
        self._change_history.clear()
