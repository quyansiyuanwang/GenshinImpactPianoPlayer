"""Configuration data classes for GIPianoPlayer."""

from dataclasses import dataclass


@dataclass
class PlayConfig:
    """Configuration for playback parameters."""

    version: float
    speed_multiplier: float  # Playback speed multiplier
    arpeggio_interval: float  # Interval between arpeggio notes (seconds)
    interval_rating: float  # Base interval between notes (seconds)
    line_interval_rating: float  # Line break interval multiplier (N empty notes between lines)
    segment_length: int  # Number of notes between each / separator (0 = disabled)
