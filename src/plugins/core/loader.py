"""Plugin loader for GIPianoPlayer.

Loads and manages plugins from configuration.
"""

import importlib
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found,no-redef]

from src.plugins.core.plugin import Plugin
from src.plugins.core.context import PluginContext
from src.plugins.core.manager import get_plugin_manager


def load_plugins_from_config(config_path: str | Path = "plugins.toml") -> None:
    """Load plugins from configuration file.

    Args:
        config_path: Path to plugins.toml configuration file
    """
    config_path = Path(config_path)

    # In packaged environment, look for plugins.toml next to the executable
    if not config_path.exists():
        if getattr(sys, "frozen", False):
            # Running as packaged exe
            exe_dir = Path(sys.executable).parent
            config_path = exe_dir / "plugins.toml"

            # If still not found, try using sys._MEIPASS (PyInstaller temp directory)
            if not config_path.exists() and hasattr(sys, "_MEIPASS"):
                config_path = Path(sys._MEIPASS) / "plugins.toml"

    if not config_path.exists():
        print(f"Plugin config not found: {config_path}")
        return

    # Load configuration
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    plugin_config = config.get("plugins", {})
    enabled_plugins = plugin_config.get("enabled", [])

    # Add custom plugin paths to sys.path
    custom_paths = plugin_config.get("custom_paths", {}).get("paths", [])
    for path in custom_paths:
        if Path(path).exists():
            sys.path.insert(0, str(Path(path).resolve()))

    # Load built-in plugins
    manager = get_plugin_manager()

    for plugin_name in enabled_plugins:
        try:
            plugin = _load_plugin(plugin_name, plugin_config)
            if plugin:
                manager.register_plugin(plugin)
        except Exception as e:
            print(f"Failed to load plugin '{plugin_name}': {e}")


def _load_plugin(name: str, config: dict[str, Any]) -> Plugin | None:
    """Load a single plugin by name.

    Args:
        name: Plugin name
        config: Plugin configuration

    Returns:
        Plugin instance or None if loading failed
    """
    # Try to import from builtin config plugins first
    try:
        from src.plugins.builtin.config.config_manager import (
            ConfigManagerPlugin,
            IntervalAdjustmentPlugin,
            ModeTogglePlugin,
            SegmentAdjustmentPlugin,
            SpeedAdjustmentPlugin,
        )

        if name == "config_manager":
            return ConfigManagerPlugin()
        if name == "speed_adjustment":
            return SpeedAdjustmentPlugin()
        if name == "interval_adjustment":
            return IntervalAdjustmentPlugin()
        if name == "segment_adjustment":
            return SegmentAdjustmentPlugin()
        if name == "mode_toggle":
            return ModeTogglePlugin()
    except ImportError:
        pass

    # Try to import from built-in plugins
    try:
        module = importlib.import_module("src.plugins")
        # Convert snake_case to PascalCase
        class_name = "".join(word.capitalize() for word in name.split("_")) + "Plugin"
        plugin_class = getattr(module, class_name)
        return plugin_class()  # type: ignore[no-any-return]
    except (ImportError, AttributeError):
        pass

    # Try to import from custom plugins
    try:
        module = importlib.import_module(f"plugins.{name}")
        plugin_class = getattr(module, "Plugin")
        return plugin_class()  # type: ignore[no-any-return]
    except (ImportError, AttributeError) as e:
        print(f"Could not import plugin '{name}': {e}")
        return None


def initialize_plugins(player: Any = None, cli: Any = None) -> None:
    """Initialize all loaded plugins with context.

    Args:
        player: Player instance
        cli: CLI instance
    """
    manager = get_plugin_manager()
    context = PluginContext(
        player=player,
        cli=cli,
        controller=getattr(cli, "controller", None),
    )
    manager.set_context(context)
    manager.initialize_all()


def cleanup_plugins() -> None:
    """Cleanup all plugins."""
    manager = get_plugin_manager()
    manager.cleanup_all()
