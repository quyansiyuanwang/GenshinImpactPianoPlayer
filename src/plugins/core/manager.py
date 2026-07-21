"""Plugin manager for loading and managing plugins."""

from typing import Optional, List

from src.plugins.core.plugin import Plugin
from src.plugins.core.context import PluginContext
from src.application.state.state_machine import PluginState, StateTransitionError


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

        Raises:
            ValueError: If plugin with same name already registered
        """
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' is already registered")

        self._plugins[plugin.name] = plugin

        # Initialize if context is available
        if self._context:
            try:
                plugin.initialize(self._context)
                plugin._transition_to_initialized()
            except Exception as e:
                print(f"Failed to initialize plugin '{plugin.name}': {e}")
                try:
                    plugin._state_machine.transition_to(PluginState.ERROR)
                except StateTransitionError:
                    pass

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

    def get_all_plugins(self) -> List[Plugin]:
        """Get all registered plugins.

        Returns:
            List of all plugins
        """
        return list(self._plugins.values())

    def get_enabled_plugins(self) -> List[Plugin]:
        """Get all enabled plugins.

        Returns:
            List of enabled plugins
        """
        return [p for p in self._plugins.values() if p.enabled]

    def enable_plugin(self, name: str) -> None:
        """Enable a plugin.

        Args:
            name: Plugin name

        Raises:
            ValueError: If plugin not found
        """
        plugin = self.get_plugin(name)
        if not plugin:
            raise ValueError(f"Plugin '{name}' not found")

        plugin.on_enable()

    def disable_plugin(self, name: str) -> None:
        """Disable a plugin.

        Args:
            name: Plugin name

        Raises:
            ValueError: If plugin not found
        """
        plugin = self.get_plugin(name)
        if not plugin:
            raise ValueError(f"Plugin '{name}' not found")

        plugin.on_disable()

    def initialize_all(self) -> None:
        """Initialize all registered plugins."""
        if not self._context:
            raise RuntimeError("Plugin context not set")

        for plugin in self._plugins.values():
            if plugin.state == PluginState.REGISTERED:
                try:
                    plugin.initialize(self._context)
                    plugin._transition_to_initialized()
                except Exception as e:
                    print(f"Failed to initialize plugin '{plugin.name}': {e}")
                    try:
                        plugin._state_machine.transition_to(PluginState.ERROR)
                    except StateTransitionError:
                        pass

    def cleanup_all(self) -> None:
        """Cleanup all plugins."""
        for plugin in self._plugins.values():
            try:
                plugin.cleanup()
            except Exception as e:
                print(f"Error cleaning up plugin '{plugin.name}': {e}")

    def get_plugin_count(self) -> int:
        """Get total number of registered plugins.

        Returns:
            Number of plugins
        """
        return len(self._plugins)

    def get_plugin_states(self) -> dict[str, str]:
        """Get state of all plugins.

        Returns:
            Dictionary mapping plugin name to state
        """
        return {name: plugin.state.value for name, plugin in self._plugins.items()}


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance.

    Returns:
        Global PluginManager instance
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def _reset_for_testing() -> None:
    """Reset the global plugin manager for testing.

    WARNING: This should only be called from test code.
    """
    global _plugin_manager
    _plugin_manager = None
