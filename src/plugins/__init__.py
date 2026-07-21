"""Plugin system for GIPianoPlayer."""

# Core plugin system
from src.plugins.core.plugin import Plugin
from src.plugins.core.context import PluginContext
from src.plugins.core.manager import PluginManager, get_plugin_manager
from src.plugins.core.loader import load_plugins_from_config

# Built-in plugins
from src.plugins.builtin.config.config_manager import ConfigManagerPlugin

__all__ = [
    # Core
    "Plugin",
    "PluginContext",
    "PluginManager",
    "get_plugin_manager",
    "load_plugins_from_config",
    # Built-in plugins
    "ConfigManagerPlugin",
]
