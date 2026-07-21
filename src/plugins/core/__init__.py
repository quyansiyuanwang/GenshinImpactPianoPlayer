"""Plugin core system.

Import from specific modules to avoid circular imports.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.plugins.core.plugin import Plugin, PluginState
    from src.plugins.core.context import PluginContext
    from src.plugins.core.manager import PluginManager, get_plugin_manager
    from src.plugins.core.loader import (
        load_plugins_from_config,
        initialize_plugins,
        cleanup_plugins,
    )

__all__ = [
    "Plugin",
    "PluginState",
    "PluginContext",
    "PluginManager",
    "get_plugin_manager",
    "load_plugins_from_config",
    "initialize_plugins",
    "cleanup_plugins",
]


def __getattr__(name: str) -> Any:
    """Lazy import to avoid circular dependencies."""
    if name in ("Plugin", "PluginState"):
        from src.plugins.core.plugin import Plugin, PluginState

        return Plugin if name == "Plugin" else PluginState
    elif name == "PluginContext":
        from src.plugins.core.context import PluginContext

        return PluginContext
    elif name in ("PluginManager", "get_plugin_manager"):
        from src.plugins.core.manager import PluginManager, get_plugin_manager

        return PluginManager if name == "PluginManager" else get_plugin_manager
    elif name in ("load_plugins_from_config", "initialize_plugins", "cleanup_plugins"):
        from src.plugins.core.loader import (
            load_plugins_from_config,
            initialize_plugins,
            cleanup_plugins,
        )

        if name == "load_plugins_from_config":
            return load_plugins_from_config
        elif name == "initialize_plugins":
            return initialize_plugins
        else:
            return cleanup_plugins
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
