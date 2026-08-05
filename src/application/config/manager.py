"""Configuration manager for handling configuration loading, saving, and validation."""

from pathlib import Path
from typing import Optional

from src.core.domain.config import PlayConfig
from src.application.config.constants import (
    DEFAULT_VERSION,
    DEFAULT_SPEED_MULTIPLIER,
    DEFAULT_ARPEGGIO_INTERVAL,
    DEFAULT_ARPEGGIO_AUTO,
    DEFAULT_INTERVAL_RATING,
    DEFAULT_LINE_INTERVAL_RATING,
    DEFAULT_SPACE_INTERVAL_RATING,
    DEFAULT_EMPTY_LINE_INTERVAL_RATING,
    DEFAULT_SEGMENT_LENGTH,
    DEFAULT_SEGMENT_STRICT,
)


class ConfigManager:
    """Manages configuration loading, saving, and validation."""

    def __init__(self) -> None:
        """Initialize configuration manager."""
        self._current_config: Optional[PlayConfig] = None
        self._config_path: Optional[Path] = None

    @property
    def current_config(self) -> Optional[PlayConfig]:
        """Get current configuration.

        Returns:
            Current PlayConfig or None if not loaded
        """
        return self._current_config

    def create_default_config(self) -> PlayConfig:
        """Create a default configuration.

        Returns:
            Default PlayConfig
        """
        return PlayConfig(
            version=DEFAULT_VERSION,
            speed_multiplier=DEFAULT_SPEED_MULTIPLIER,
            arpeggio_interval=DEFAULT_ARPEGGIO_INTERVAL,
            interval_rating=DEFAULT_INTERVAL_RATING,
            line_interval_rating=DEFAULT_LINE_INTERVAL_RATING,
            space_interval_rating=DEFAULT_SPACE_INTERVAL_RATING,
            empty_line_interval_rating=DEFAULT_EMPTY_LINE_INTERVAL_RATING,
            segment_length=DEFAULT_SEGMENT_LENGTH,
            segment_strict=DEFAULT_SEGMENT_STRICT,
            arpeggio_auto=DEFAULT_ARPEGGIO_AUTO,
        )

    def load_from_file(self, file_path: Path) -> PlayConfig:
        """Load configuration from TOML file.

        Args:
            file_path: Path to configuration file

        Returns:
            Loaded PlayConfig

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If configuration is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        try:
            import tomllib  # Python 3.11+
        except ImportError:
            import tomli as tomllib  # type: ignore[import-not-found,no-redef]

        with open(file_path, "rb") as f:
            data = tomllib.load(f)

        config_data = data.get("config", {})

        config = PlayConfig(
            version=config_data.get("version", DEFAULT_VERSION),
            speed_multiplier=config_data.get(
                "speed_multiplier", DEFAULT_SPEED_MULTIPLIER
            ),
            arpeggio_interval=config_data.get(
                "arpeggio_interval", DEFAULT_ARPEGGIO_INTERVAL
            ),
            interval_rating=config_data.get("interval_rating", DEFAULT_INTERVAL_RATING),
            line_interval_rating=config_data.get(
                "line_interval_rating", DEFAULT_LINE_INTERVAL_RATING
            ),
            space_interval_rating=config_data.get(
                "space_interval_rating", DEFAULT_SPACE_INTERVAL_RATING
            ),
            empty_line_interval_rating=config_data.get(
                "empty_line_interval_rating", DEFAULT_EMPTY_LINE_INTERVAL_RATING
            ),
            segment_length=config_data.get("segment_length", DEFAULT_SEGMENT_LENGTH),
            segment_strict=config_data.get("segment_strict", DEFAULT_SEGMENT_STRICT),
            arpeggio_auto=config_data.get("arpeggio_auto", DEFAULT_ARPEGGIO_AUTO),
        )

        # Validate configuration
        config.validate()

        self._current_config = config
        self._config_path = file_path

        return config

    def save_to_file(self, config: PlayConfig, file_path: Path) -> None:
        """Save configuration to TOML file.

        Args:
            config: Configuration to save
            file_path: Path to save configuration

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate before saving
        config.validate()

        content = self._generate_toml_content(config)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        self._current_config = config
        self._config_path = file_path

    def _generate_toml_content(self, config: PlayConfig) -> str:
        """Generate TOML content from configuration.

        Args:
            config: Configuration to convert

        Returns:
            TOML content as string
        """
        return f"""# GIPianoPlayer Configuration
# Auto-generated configuration file

[config]
version = {config.version}

# Playback speed multiplier (0.1 - 10.0)
speed_multiplier = {config.speed_multiplier}

# Arpeggio interval in seconds (0.01 - 1.0)
arpeggio_interval = {config.arpeggio_interval}

# Infer arpeggio timing from the note interval
arpeggio_auto = {str(config.arpeggio_auto).lower()}

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

    def update_config(self, **kwargs: float | int | bool) -> PlayConfig:
        """Update current configuration with new values.

        Args:
            **kwargs: Configuration parameters to update

        Returns:
            Updated PlayConfig

        Raises:
            ValueError: If no configuration is loaded or values are invalid
        """
        if self._current_config is None:
            raise ValueError("No configuration loaded")

        # Create a copy and update
        config_dict = {
            "version": kwargs.get("version", self._current_config.version),
            "speed_multiplier": kwargs.get(
                "speed_multiplier", self._current_config.speed_multiplier
            ),
            "arpeggio_interval": kwargs.get(
                "arpeggio_interval", self._current_config.arpeggio_interval
            ),
            "arpeggio_auto": kwargs.get(
                "arpeggio_auto", self._current_config.arpeggio_auto
            ),
            "interval_rating": kwargs.get(
                "interval_rating", self._current_config.interval_rating
            ),
            "line_interval_rating": kwargs.get(
                "line_interval_rating", self._current_config.line_interval_rating
            ),
            "space_interval_rating": kwargs.get(
                "space_interval_rating", self._current_config.space_interval_rating
            ),
            "empty_line_interval_rating": kwargs.get(
                "empty_line_interval_rating",
                self._current_config.empty_line_interval_rating,
            ),
            "segment_length": kwargs.get(
                "segment_length", self._current_config.segment_length
            ),
            "segment_strict": kwargs.get(
                "segment_strict", self._current_config.segment_strict
            ),
        }

        new_config = PlayConfig(**config_dict)  # type: ignore[arg-type]
        new_config.validate()

        self._current_config = new_config
        return new_config

    def reset_to_defaults(self) -> PlayConfig:
        """Reset configuration to defaults.

        Returns:
            Default PlayConfig
        """
        self._current_config = self.create_default_config()
        return self._current_config

    def get_config_path(self) -> Optional[Path]:
        """Get the path of the currently loaded configuration file.

        Returns:
            Path to configuration file or None
        """
        return self._config_path
