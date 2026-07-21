"""Configuration management plugin for GIPianoPlayer.

Handles all configuration-related operations including:
- Loading configuration from files
- Saving configuration to files
- Adjusting configuration values
- Configuration validation
"""

from pathlib import Path
from typing import TYPE_CHECKING

from src.core.domain.config import PlayConfig
from src.plugins.core.plugin import Plugin
from src.plugins.core.context import PluginContext
from src.application.state.state_machine import (
    ConfigStateMachine,
    ConfigState,
    StateTransitionError,
)

if TYPE_CHECKING:
    from src.cli import CLI
    from src.core.player.player import Player


class ConfigManagerPlugin(Plugin):
    """Plugin for managing configuration."""

    def __init__(self) -> None:
        """Initialize config manager plugin."""
        super().__init__("config_manager", "1.0.0")
        self.cli: "CLI | None" = None
        self.player: "Player | None" = None
        self._config_state = ConfigStateMachine()

    def initialize(self, context: PluginContext) -> None:
        """Initialize plugin with context."""
        self.cli = context.cli
        self.player = context.player

        # Register hotkeys
        context.register_hotkey("f9", self._save_config)

    def _save_config(self) -> None:
        """Save current configuration to file."""
        if not self.enabled or not self.player or not self.cli:
            return

        try:
            # Use CLI's save_config method which saves to the score file
            self.cli.save_config()
            # Force display update to show save confirmation
            self.cli._display_score()
        except Exception as e:
            print(f"\n✗ Failed to save configuration: {e}")

    def _get_current_config(self) -> PlayConfig:
        """Get current configuration from player.

        Returns:
            Current PlayConfig
        """
        if not self.player:
            raise RuntimeError("Player not available")

        return PlayConfig(
            version=1.0,
            speed_multiplier=self.player._speed_multiplier,
            arpeggio_interval=self.player._arpeggio_interval,
            interval_rating=self.player._interval_rating,
            line_interval_rating=self.player._line_interval_rating,
            space_interval_rating=self.player._space_interval_rating,
            empty_line_interval_rating=self.player._empty_line_interval_rating,
            segment_length=self.player._segment_length,
            segment_strict=self.player.get_segment_strict(),
        )

    def _write_config_file(self, path: Path, config: PlayConfig) -> None:
        """Write configuration to TOML file.

        Args:
            path: Path to save configuration
            config: Configuration to save
        """
        content = f"""# GIPianoPlayer Configuration
# Auto-generated configuration file

[config]
version = {config.version}

# Playback speed multiplier (0.1 - 10.0)
speed_multiplier = {config.speed_multiplier}

# Arpeggio interval in seconds (0.01 - 1.0)
arpeggio_interval = {config.arpeggio_interval}

# Base interval between notes in seconds (0.01 - 5.0)
interval_rating = {config.interval_rating}

# Line interval: N empty notes between lines (0.0 - 10.0)
line_interval_rating = {config.line_interval_rating}

# Space interval: multiplier for rest notes (0.0 - 10.0)
space_interval_rating = {config.space_interval_rating}

# Empty line interval: N empty notes for empty lines (0.0 - 10.0)
empty_line_interval_rating = {config.empty_line_interval_rating}

# Segment length: N notes per segment, 0 = disabled (0 - 20)
segment_length = {config.segment_length}

# Segment strict mode: truncate segments exceeding length
segment_strict = {str(config.segment_strict).lower()}
"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def load_config(self, path: Path) -> PlayConfig:
        """Load configuration from file.

        Args:
            path: Path to configuration file

        Returns:
            Loaded PlayConfig
        """
        try:
            self._config_state.transition_to(ConfigState.LOADING)

            try:
                import tomllib  # Python 3.11+
            except ImportError:
                import tomli as tomllib  # type: ignore[import-not-found,no-redef]

            with open(path, "rb") as f:
                data = tomllib.load(f)

            config_data = data.get("config", {})

            config = PlayConfig(
                version=config_data.get("version", 1.0),
                speed_multiplier=config_data.get("speed_multiplier", 1.0),
                arpeggio_interval=config_data.get("arpeggio_interval", 0.05),
                interval_rating=config_data.get("interval_rating", 0.2),
                line_interval_rating=config_data.get("line_interval_rating", 1.0),
                space_interval_rating=config_data.get("space_interval_rating", 1.0),
                empty_line_interval_rating=config_data.get(
                    "empty_line_interval_rating", 0.0
                ),
                segment_length=config_data.get("segment_length", 0),
                segment_strict=config_data.get("segment_strict", False),
            )

            self._config_state.transition_to(ConfigState.LOADED)
            return config

        except Exception as e:
            try:
                self._config_state.transition_to(ConfigState.ERROR)
            except StateTransitionError:
                pass
            raise e

    def apply_config(self, config: PlayConfig) -> None:
        """Apply configuration to player.

        Args:
            config: Configuration to apply
        """
        if not self.player:
            return

        self.player.set_speed(config.speed_multiplier)
        self.player.set_arpeggio_interval(config.arpeggio_interval)
        self.player.set_interval_rating(config.interval_rating)
        self.player.set_line_interval_rating(config.line_interval_rating)
        self.player.set_space_interval_rating(config.space_interval_rating)
        self.player.set_empty_line_interval_rating(config.empty_line_interval_rating)
        self.player.set_segment_length(config.segment_length)
        # Note: segment_strict is set during parsing, not runtime


class SpeedAdjustmentPlugin(Plugin):
    """Plugin for speed adjustment operations."""

    def __init__(self) -> None:
        """Initialize speed adjustment plugin."""
        super().__init__("speed_adjustment", "1.0.0")
        self.player: "Player | None" = None

    def initialize(self, context: PluginContext) -> None:
        """Initialize plugin with context."""
        self.player = context.player

    def adjust_speed(self, delta: float) -> None:
        """Adjust playback speed.

        Args:
            delta: Amount to adjust (positive or negative)
        """
        if not self.enabled or not self.player:
            return

        current = self.player._speed_multiplier
        new_speed = max(0.1, min(10.0, current + delta))
        self.player.set_speed(new_speed)


class IntervalAdjustmentPlugin(Plugin):
    """Plugin for interval adjustment operations."""

    def __init__(self) -> None:
        """Initialize interval adjustment plugin."""
        super().__init__("interval_adjustment", "1.0.0")
        self.player: "Player | None" = None

    def initialize(self, context: PluginContext) -> None:
        """Initialize plugin with context."""
        self.player = context.player

    def adjust_arpeggio(self, delta: float) -> None:
        """Adjust arpeggio interval.

        Args:
            delta: Amount to adjust in seconds
        """
        if not self.enabled or not self.player:
            return

        current = self.player._arpeggio_interval
        new_interval = max(0.01, min(1.0, current + delta))
        self.player.set_arpeggio_interval(new_interval)

    def adjust_interval(self, delta: float) -> None:
        """Adjust note interval.

        Args:
            delta: Amount to adjust in seconds
        """
        if not self.enabled or not self.player:
            return

        current = self.player._interval_rating
        new_interval = max(0.01, min(5.0, current + delta))
        self.player.set_interval_rating(new_interval)

    def adjust_line_interval(self, delta: float) -> None:
        """Adjust line interval.

        Args:
            delta: Amount to adjust (number of empty notes)
        """
        if not self.enabled or not self.player:
            return

        current = self.player._line_interval_rating
        new_interval = max(0.0, min(10.0, current + delta))
        self.player.set_line_interval_rating(new_interval)

    def adjust_space_interval(self, delta: float) -> None:
        """Adjust space interval.

        Args:
            delta: Amount to adjust (multiplier)
        """
        if not self.enabled or not self.player:
            return

        current = self.player._space_interval_rating
        new_interval = max(0.0, min(10.0, current + delta))
        self.player.set_space_interval_rating(new_interval)

    def adjust_empty_line_interval(self, delta: float) -> None:
        """Adjust empty line interval.

        Args:
            delta: Amount to adjust (number of empty notes)
        """
        if not self.enabled or not self.player:
            return

        current = self.player._empty_line_interval_rating
        new_interval = max(0.0, min(10.0, current + delta))
        self.player.set_empty_line_interval_rating(new_interval)


class SegmentAdjustmentPlugin(Plugin):
    """Plugin for segment adjustment operations."""

    def __init__(self) -> None:
        """Initialize segment adjustment plugin."""
        super().__init__("segment_adjustment", "1.0.0")
        self.player: "Player | None" = None

    def initialize(self, context: PluginContext) -> None:
        """Initialize plugin with context."""
        self.player = context.player

    def adjust_segment_length(self, delta: int) -> None:
        """Adjust segment length.

        Args:
            delta: Amount to adjust (number of notes)
        """
        if not self.enabled or not self.player:
            return

        current = self.player._segment_length
        new_length = max(0, min(20, current + delta))
        self.player.set_segment_length(new_length)

    def toggle_segment_strict(self) -> None:
        """Toggle segment strict mode."""
        if not self.enabled or not self.player:
            return

        self.player.toggle_segment_strict()


class ModeTogglePlugin(Plugin):
    """Plugin for mode toggle operations."""

    def __init__(self) -> None:
        """Initialize mode toggle plugin."""
        super().__init__("mode_toggle", "1.0.0")
        self.player: "Player | None" = None

    def initialize(self, context: PluginContext) -> None:
        """Initialize plugin with context."""
        self.player = context.player

    def toggle_sustain(self) -> None:
        """Toggle sustain mode."""
        if not self.enabled or not self.player:
            return

        self.player.toggle_sustain()
