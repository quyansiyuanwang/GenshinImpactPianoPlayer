"""Plugin context for providing access to core components."""

from typing import Any, Callable, Optional


class PluginContext:
    """Context provided to plugins with access to core components."""

    def __init__(
        self,
        player: Any = None,
        cli: Any = None,
        config: Optional[dict[str, Any]] = None,
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
        from src.ui.cli.input.hotkey_registry import get_hotkey_registry

        # Register with global hotkey registry, replacing stale bindings after
        # a reload or reparse created a new player.
        registry = get_hotkey_registry()
        if registry.get_callback(key) is not None:
            registry.unregister(key)

        registry.register(key, callback, f"Plugin hotkey: {key}", "plugin")

        # Also store locally for reference
        self._hotkeys[key] = callback

    def get_hotkeys(self) -> dict[str, Callable[[], None]]:
        """Get all registered hotkeys.

        Returns:
            Dictionary of hotkey -> callback mappings
        """
        return self._hotkeys.copy()

    def get_player(self) -> Any:
        """Get player instance.

        Returns:
            Player instance or None
        """
        return self.player

    def get_cli(self) -> Any:
        """Get CLI instance.

        Returns:
            CLI instance or None
        """
        return self.cli

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
