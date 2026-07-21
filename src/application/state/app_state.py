"""Application state management."""

from typing import Optional, Callable

from src.application.state.state_machine import AppStateMachine, AppState
from src.application.config.manager import ConfigManager
from src.application.services.file_service import FileService
from src.application.services.playback_service import PlaybackService


class ApplicationState:
    """Manages the overall application state and coordinates services."""

    def __init__(self) -> None:
        """Initialize application state."""
        # State machine
        self._state_machine = AppStateMachine()

        # Services
        self._config_manager = ConfigManager()
        self._file_service = FileService()
        self._playback_service = PlaybackService()

        # Callbacks
        self._error_callback: Optional[Callable[[str], None]] = None

    @property
    def state(self) -> AppState:
        """Get current application state.

        Returns:
            Current AppState
        """
        return self._state_machine.current_state

    @property
    def config_manager(self) -> ConfigManager:
        """Get configuration manager.

        Returns:
            ConfigManager instance
        """
        return self._config_manager

    @property
    def file_service(self) -> FileService:
        """Get file service.

        Returns:
            FileService instance
        """
        return self._file_service

    @property
    def playback_service(self) -> PlaybackService:
        """Get playback service.

        Returns:
            PlaybackService instance
        """
        return self._playback_service

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for error notifications.

        Args:
            callback: Function to call when errors occur
        """
        self._error_callback = callback

    def initialize(self) -> None:
        """Initialize the application.

        Transitions state from UNINITIALIZED to INITIALIZING to READY.
        """
        try:
            self._state_machine.transition_to(AppState.INITIALIZING)

            # Initialize services
            # (Services are already initialized in __init__)

            # Transition to ready
            self._state_machine.transition_to(AppState.READY)

        except Exception as e:
            self._handle_error(f"Initialization failed: {e}")
            self._state_machine.set_error(str(e))

    def start(self) -> None:
        """Start the application.

        Transitions state from READY to RUNNING.
        """
        try:
            if self._state_machine.current_state == AppState.READY:
                self._state_machine.transition_to(AppState.RUNNING)
        except Exception as e:
            self._handle_error(f"Failed to start: {e}")

    def pause(self) -> None:
        """Pause the application.

        Transitions state from RUNNING to PAUSED.
        """
        try:
            if self._state_machine.current_state == AppState.RUNNING:
                # Pause playback if active
                if self._playback_service.is_playing():
                    self._playback_service.pause()

                self._state_machine.transition_to(AppState.PAUSED)
        except Exception as e:
            self._handle_error(f"Failed to pause: {e}")

    def resume(self) -> None:
        """Resume the application.

        Transitions state from PAUSED to RUNNING.
        """
        try:
            if self._state_machine.current_state == AppState.PAUSED:
                self._state_machine.transition_to(AppState.RUNNING)
        except Exception as e:
            self._handle_error(f"Failed to resume: {e}")

    def shutdown(self) -> None:
        """Shutdown the application.

        Transitions state to SHUTTING_DOWN then TERMINATED.
        """
        try:
            # Stop playback if active
            if self._playback_service.player:
                self._playback_service.stop()

            self._state_machine.transition_to(AppState.SHUTTING_DOWN)

            # Cleanup services
            # (No explicit cleanup needed for current services)

            self._state_machine.transition_to(AppState.TERMINATED)

        except Exception as e:
            self._handle_error(f"Shutdown error: {e}")
            # Force transition to terminated
            try:
                self._state_machine.transition_to(AppState.SHUTTING_DOWN)
                self._state_machine.transition_to(AppState.TERMINATED)
            except Exception:
                pass

    def _handle_error(self, error_message: str) -> None:
        """Handle an error.

        Args:
            error_message: Error message
        """
        if self._error_callback:
            self._error_callback(error_message)
        else:
            print(f"Error: {error_message}")

    def is_running(self) -> bool:
        """Check if application is running.

        Returns:
            True if running, False otherwise
        """
        return self._state_machine.current_state == AppState.RUNNING

    def is_ready(self) -> bool:
        """Check if application is ready.

        Returns:
            True if ready, False otherwise
        """
        return self._state_machine.current_state == AppState.READY

    def is_error(self) -> bool:
        """Check if application is in error state.

        Returns:
            True if in error state, False otherwise
        """
        return self._state_machine.current_state == AppState.ERROR

    def get_error_info(self) -> Optional[str]:
        """Get error information if in error state.

        Returns:
            Error message or None
        """
        return self._state_machine.get_error_info()
