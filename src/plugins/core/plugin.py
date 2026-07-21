"""Plugin base class."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.application.state.state_machine import (
    PluginStateMachine,
    PluginState,
    StateTransitionError,
)

if TYPE_CHECKING:
    from src.plugins.core.context import PluginContext

__all__ = ["Plugin", "PluginState"]


class Plugin(ABC):
    """Base class for all plugins.

    Plugins can hook into various aspects of the player:
    - Hotkeys: Add custom keyboard shortcuts
    - Playback: Modify playback behavior
    - Display: Customize UI rendering
    - Configuration: Add custom config parameters
    """

    def __init__(self, name: str, version: str = "1.0.0") -> None:
        """Initialize plugin.

        Args:
            name: Plugin name
            version: Plugin version
        """
        self.name = name
        self.version = version
        self.enabled = True
        self._state_machine = PluginStateMachine()
        self._state_machine.transition_to(PluginState.REGISTERED)

    @abstractmethod
    def initialize(self, context: "PluginContext") -> None:
        """Initialize the plugin with context.

        Called when the plugin is loaded.

        Args:
            context: Plugin context with access to player, CLI, etc.
        """
        pass

    def cleanup(self) -> None:
        """Cleanup plugin resources.

        Called when the plugin is unloaded or the application exits.
        """
        try:
            if self._state_machine.can_transition_to(PluginState.UNLOADING):
                self._state_machine.transition_to(PluginState.UNLOADING)
                self._state_machine.transition_to(PluginState.UNLOADED)
        except StateTransitionError:
            pass

    def on_enable(self) -> None:
        """Called when plugin is enabled."""
        self.enabled = True
        try:
            if self._state_machine.can_transition_to(PluginState.ENABLED):
                self._state_machine.transition_to(PluginState.ENABLED)
        except StateTransitionError:
            pass

    def on_disable(self) -> None:
        """Called when plugin is disabled."""
        self.enabled = False
        try:
            if self._state_machine.can_transition_to(PluginState.DISABLED):
                self._state_machine.transition_to(PluginState.DISABLED)
        except StateTransitionError:
            pass

    @property
    def state(self) -> PluginState:
        """Get current plugin state.

        Returns:
            Current PluginState
        """
        return self._state_machine.current_state

    def _transition_to_initialized(self) -> None:
        """Transition to initialized state after initialize() completes."""
        try:
            if self._state_machine.current_state == PluginState.REGISTERED:
                self._state_machine.transition_to(PluginState.INITIALIZING)
            if self._state_machine.current_state == PluginState.INITIALIZING:
                self._state_machine.transition_to(PluginState.INITIALIZED)
                self._state_machine.transition_to(PluginState.ENABLED)
        except StateTransitionError:
            pass

    def __repr__(self) -> str:
        """String representation of plugin.

        Returns:
            Plugin representation
        """
        return f"<{self.__class__.__name__} {self.name} v{self.version} state={self.state.value}>"
