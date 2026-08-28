"""Constants and configuration for GIPianoPlayer."""

# Valid keys that the game supports
VALID_KEYS = set("QWERTYUASDFGHJZXCVBNM")

# Default hotkey bindings
DEFAULT_HOTKEYS = {
    # Playback control
    "play_pause": "f8",
    "quit": "f2",
    # Speed adjustment (use physical keys for better compatibility)
    "speed_up": "=",  # = key (not +)
    "speed_down": "-",
    "speed_up_large": "ctrl+=",
    "speed_down_large": "ctrl+-",
    # Note interval adjustment
    "interval_shorter": ",",  # < key
    "interval_longer": ".",  # > key
    # Arpeggio adjustment switches to manual timing mode
    "arpeggio_shorter": "[",
    "arpeggio_longer": "]",
    "toggle_arpeggio_auto": "f3",
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
    "jump_to_start": "home",
    "jump_to_end": "end",
    # Loop playback
    "toggle_loop": "insert",
    "toggle_line_loop": "delete",
    # A-B range playback
    "set_range_a": "ctrl+home",
    "set_range_b": "ctrl+end",
    "clear_range": "ctrl+backspace",
    # Bookmark
    "set_bookmark": "ctrl+k",
    "jump_to_bookmark": "ctrl+l",
    # Reload and reparse
    "reload": "f5",
    "reparse": "f6",
    # Sustain toggle
    "toggle_sustain": "f7",
    # Segment strict mode toggle
    "toggle_segment_strict": "f4",
}

# Skip amounts
SKIP_SMALL = 1  # notes (single note)
SKIP_LARGE = 1  # lines (will be handled differently)

# Adjustment steps
SPEED_STEP = 0.01
SPEED_STEP_LARGE = 0.1
ARPEGGIO_STEP = 0.01  # seconds
INTERVAL_STEP = 0.01  # seconds
SPACE_INTERVAL_STEP = 0.1  # multiplier for rest notes

# Display settings
DISPLAY_REFRESH_RATE = 0.042  # seconds (~24 FPS)
DISPLAY_LINES_BEFORE = 3
DISPLAY_LINES_AFTER = 6

# Default PlayConfig values
DEFAULT_VERSION = 1.0
DEFAULT_SPEED_MULTIPLIER = 1.0
DEFAULT_ARPEGGIO_INTERVAL = 0.05  # seconds
DEFAULT_ARPEGGIO_AUTO = True
DEFAULT_INTERVAL_RATING = 0.2  # seconds
DEFAULT_LINE_INTERVAL_RATING = 1.0  # N empty notes between lines
DEFAULT_SPACE_INTERVAL_RATING = 1.0  # multiplier for space (rest) notes
DEFAULT_EMPTY_LINE_INTERVAL_RATING = 0.0  # N empty notes for empty lines
DEFAULT_SEGMENT_LENGTH = 0  # 0 = disabled, >0 = force N notes per segment
DEFAULT_SEGMENT_STRICT = (
    False  # True = truncate segments exceeding length, False = pad only
)
DEFAULT_LOOP = False  # True = restart from the beginning after the last note

# Playback limits
MIN_SPEED = 0.1
MAX_SPEED = 10.0
MIN_ARPEGGIO_INTERVAL = 0.01
MAX_ARPEGGIO_INTERVAL = 1.0
MIN_INTERVAL = 0.01
MAX_INTERVAL = 5.0
