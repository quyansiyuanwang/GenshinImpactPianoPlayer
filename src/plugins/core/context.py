"""Plugin context for providing access to core components."""

from typing import Any, Callable, Optional

from src.application.command_bus import CommandResult
from src.application.events import InputEvent


class PluginContext:
    """Context provided to plugins with access to core components."""

    def __init__(
        self,
        player: Any = None,
        cli: Any = None,
        config: Optional[dict[str, Any]] = None,
        controller: Any = None,
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
        self.controller = controller or getattr(cli, "controller", None)
        self._hotkeys: dict[str, Callable[[], None]] = {}
        self._commands: set[str] = set()

    def register_command(
        self,
        name: str,
        handler: Callable[[InputEvent], CommandResult],
        description: str = "",
    ) -> None:
        """Register a named command with the application's command bus."""
        if self.controller is None:
            raise RuntimeError("Plugin context has no application controller")
        self.controller.register_command(name, handler, replace=True)
        self._commands.add(name)

    def bind_key(self, binding: str, command: str) -> None:
        """Bind a key combination to a previously registered command."""
        if self.controller is None:
            raise RuntimeError("Plugin context has no application controller")
        self.controller.bind_key(binding, command)

    def register_hotkey(self, key: str, callback: Callable[[], None]) -> None:
        """Register a custom hotkey.

        Args:
            key: Hotkey string (e.g., "ctrl+p", "f10")
            callback: Function to call when hotkey is pressed
        """
        # Route new applications through the command controller.  The registry
        # registration remains for compatibility with integrations that inspect
        # plugin hotkeys during a hotkey rebuild.
        if self.controller is not None:
            command = f"plugin.{len(self._commands) + 1}.{key.lower()}"

            def invoke(_event: InputEvent) -> CommandResult:
                callback()
                return CommandResult.ok()

            try:
                self.register_command(command, invoke, f"Plugin hotkey: {key}")
                self.bind_key(key, command)
            except (TypeError, ValueError):
                # Built-in/profile bindings take precedence over plugin keys.
                pass

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
