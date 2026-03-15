"""Plugin system for GIPianoPlayer configuration and extensions.

This module provides a plugin architecture for extending the player's functionality.
Plugins can add custom hotkeys, modify playback behavior, or add new features.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional


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

    @abstractmethod
    def initialize(self, context: "PluginContext") -> None:
        """Initialize the plugin with context.

        Called when the plugin is loaded.

        Args:
            context: Plugin context with access to player, CLI, etc.
        """

    def cleanup(self) -> None:
        """Cleanup plugin resources.

        Called when the plugin is unloaded or the application exits.
        """

    def on_enable(self) -> None:
        """Called when plugin is enabled."""
        self.enabled = True

    def on_disable(self) -> None:
        """Called when plugin is disabled."""
        self.enabled = False


class PluginContext:
    """Context provided to plugins with access to core components."""

    def __init__(
        self,
        player: Any = None,
        cli: Any = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize plugin context.

        Args:
            player: Player instance
            cli: CLI instance
            config: Configuration dictionary
        """
        self.player = player
        self.cli = cli
        self.config = config or {}
        self._hotkeys: dict[str, Callable[[], None]] = {}

    def register_hotkey(self, key: str, callback: Callable[[], None]) -> None:
        """Register a custom hotkey.

        Args:
            key: Hotkey string (e.g., "ctrl+p", "f10")
            callback: Function to call when hotkey is pressed
        """
        self._hotkeys[key] = callback

    def get_hotkeys(self) -> dict[str, Callable[[], None]]:
        """Get all registered hotkeys."""
        return self._hotkeys.copy()


class PluginManager:
    """Manages plugin loading, initialization, and lifecycle."""

    def __init__(self) -> None:
        """Initialize plugin manager."""
        self._plugins: dict[str, Plugin] = {}
        self._context: Optional[PluginContext] = None

    def set_context(self, context: PluginContext) -> None:
        """Set the plugin context.

        Args:
            context: Plugin context
        """
        self._context = context

    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin.

        Args:
            plugin: Plugin instance to register
        """
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' is already registered")

        self._plugins[plugin.name] = plugin

        # Initialize if context is available
        if self._context:
            plugin.initialize(self._context)

    def unregister_plugin(self, name: str) -> None:
        """Unregister a plugin.

        Args:
            name: Plugin name
        """
        if name in self._plugins:
            plugin = self._plugins[name]
            plugin.cleanup()
            del self._plugins[name]

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(name)

    def get_all_plugins(self) -> list[Plugin]:
        """Get all registered plugins.

        Returns:
            List of plugin instances
        """
        return list(self._plugins.values())

    def enable_plugin(self, name: str) -> None:
        """Enable a plugin.

        Args:
            name: Plugin name
        """
        plugin = self.get_plugin(name)
        if plugin:
            plugin.on_enable()

    def disable_plugin(self, name: str) -> None:
        """Disable a plugin.

        Args:
            name: Plugin name
        """
        plugin = self.get_plugin(name)
        if plugin:
            plugin.on_disable()

    def initialize_all(self) -> None:
        """Initialize all registered plugins."""
        if not self._context:
            raise RuntimeError("Plugin context not set")

        for plugin in self._plugins.values():
            plugin.initialize(self._context)

    def cleanup_all(self) -> None:
        """Cleanup all plugins."""
        for plugin in self._plugins.values():
            plugin.cleanup()


# Global plugin manager instance
_plugin_manager = PluginManager()


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance.

    Returns:
        Global plugin manager
    """
    return _plugin_manager
