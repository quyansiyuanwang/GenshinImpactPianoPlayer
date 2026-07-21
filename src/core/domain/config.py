"""Configuration domain model."""

from dataclasses import dataclass


@dataclass
class PlayConfig:
    """Configuration for playback parameters."""

    version: float
    speed_multiplier: float  # Playback speed multiplier
    arpeggio_interval: float  # Interval between arpeggio notes (seconds)
    interval_rating: float  # Base interval between notes (seconds)
    line_interval_rating: float  # Line break interval (N empty notes between lines)
    space_interval_rating: float  # Space (rest) note interval multiplier
    empty_line_interval_rating: float  # Empty line interval (N empty notes)
    segment_length: int  # Number of notes per segment (0 = disabled)
    segment_strict: bool  # True = truncate segments, False = pad only

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If any value is out of valid range
        """
        if not 0.1 <= self.speed_multiplier <= 10.0:
            raise ValueError(
                f"speed_multiplier must be 0.1-10.0, got {self.speed_multiplier}"
            )

        if not 0.01 <= self.arpeggio_interval <= 1.0:
            raise ValueError(
                f"arpeggio_interval must be 0.01-1.0, got {self.arpeggio_interval}"
            )

        if not 0.01 <= self.interval_rating <= 5.0:
            raise ValueError(
                f"interval_rating must be 0.01-5.0, got {self.interval_rating}"
            )

        if not 0.0 <= self.line_interval_rating <= 10.0:
            raise ValueError(
                f"line_interval_rating must be 0.0-10.0, got {self.line_interval_rating}"
            )

        if not 0.0 <= self.space_interval_rating <= 10.0:
            raise ValueError(
                f"space_interval_rating must be 0.0-10.0, got {self.space_interval_rating}"
            )

        if not 0.0 <= self.empty_line_interval_rating <= 10.0:
            raise ValueError(
                f"empty_line_interval_rating must be 0.0-10.0, got {self.empty_line_interval_rating}"
            )

        if not 0 <= self.segment_length <= 20:
            raise ValueError(f"segment_length must be 0-20, got {self.segment_length}")

    def copy(self) -> "PlayConfig":
        """Create a copy of this configuration.

        Returns:
            New PlayConfig instance with same values
        """
        return PlayConfig(
            version=self.version,
            speed_multiplier=self.speed_multiplier,
            arpeggio_interval=self.arpeggio_interval,
            interval_rating=self.interval_rating,
            line_interval_rating=self.line_interval_rating,
            space_interval_rating=self.space_interval_rating,
            empty_line_interval_rating=self.empty_line_interval_rating,
            segment_length=self.segment_length,
            segment_strict=self.segment_strict,
        )
