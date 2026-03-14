"""Constants and configuration for GIPianoPlayer."""

# Valid keys that the game supports
VALID_KEYS = set("QWERTYUASDFGHJZXCVBNM")

# Default hotkey bindings
DEFAULT_HOTKEYS = {
    # Playback control
    "play_pause": "f8",
    "quit": "f2",
    # Speed adjustment
    "speed_up": "+",
    "speed_down": "-",
    "speed_up_large": "ctrl+=",
    "speed_down_large": "ctrl+_",
    # Arpeggio interval adjustment
    "arpeggio_faster": "[",
    "arpeggio_slower": "]",
    # Note interval adjustment
    "interval_shorter": ",",  # < key
    "interval_longer": ".",  # > key
    # Line interval adjustment
    "line_interval_less": "down",
    "line_interval_more": "up",
    # Space interval adjustment
    "space_interval_less": "shift+down",
    "space_interval_more": "shift+up",
    # Empty line interval adjustment
    "empty_line_interval_less": "ctrl+down",
    "empty_line_interval_more": "ctrl+up",
    # Segment length adjustment
    "segment_length_less": "page down",
    "segment_length_more": "page up",
    # Navigation
    "skip_backward": "left",
    "skip_forward": "right",
    "skip_backward_large": "ctrl+left",
    "skip_forward_large": "ctrl+right",
    # Reload and reparse
    "reload": "f5",
    "reparse": "f6",
    # Sustain toggle
    "toggle_sustain": "f7",
}

# Skip amounts
SKIP_SMALL = 1  # notes (single note)
SKIP_LARGE = 1  # lines (will be handled differently)

# Adjustment steps
SPEED_STEP = 0.01
SPEED_STEP_LARGE = 0.1
ARPEGGIO_STEP = 0.01  # seconds
INTERVAL_STEP = 0.01  # seconds

# Display settings
DISPLAY_REFRESH_RATE = 0.042  # seconds (~24 FPS)
DISPLAY_LINES_BEFORE = 3
DISPLAY_LINES_AFTER = 6

# Default PlayConfig values
DEFAULT_VERSION = 1.0
DEFAULT_SPEED_MULTIPLIER = 1.0
DEFAULT_ARPEGGIO_INTERVAL = 0.05  # seconds
DEFAULT_INTERVAL_RATING = 0.2  # seconds
DEFAULT_LINE_INTERVAL_RATING = 1.0  # N empty notes between lines
DEFAULT_SPACE_INTERVAL_RATING = 1.0  # multiplier for space (rest) notes
DEFAULT_EMPTY_LINE_INTERVAL_RATING = 2.0  # N empty notes for empty lines
DEFAULT_SEGMENT_LENGTH = 0  # 0 = disabled, >0 = force N notes per segment

# Playback limits
MIN_SPEED = 0.1
MAX_SPEED = 5.0
MIN_ARPEGGIO_INTERVAL = 0.01
MAX_ARPEGGIO_INTERVAL = 1.0
MIN_INTERVAL = 0.01
MAX_INTERVAL = 5.0
