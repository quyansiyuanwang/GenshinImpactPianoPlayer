"""Alternative hotkey configuration using scan codes.

This file provides scan code mappings for keys that may have different
names on different keyboard layouts.

Scan codes are hardware-level key identifiers that are consistent across
all keyboard layouts.
"""

# Common scan codes for symbol keys (Windows)
SCAN_CODES = {
    # Speed control
    "equals": 13,  # = key (same physical key as +)
    "minus": 12,  # - key
    # Brackets
    "left_bracket": 26,  # [ key
    "right_bracket": 27,  # ] key
    # Comma and period
    "comma": 51,  # , key
    "period": 52,  # . key
}


def get_scan_code_hotkey(key_name: str) -> str:
    """Get hotkey string using scan code.

    Args:
        key_name: Logical key name (e.g., "equals", "minus")

    Returns:
        Hotkey string for keyboard library (e.g., "13" for scan code)
    """
    scan_code = SCAN_CODES.get(key_name)
    if scan_code is None:
        raise ValueError(f"Unknown key name: {key_name}")
    return str(scan_code)


# Alternative: Use these key names that work better across layouts
ALTERNATIVE_KEY_NAMES = {
    "speed_increase": ["=", "plus", "+", "13"],  # Last one is scan code
    "speed_decrease": ["-", "minus", "12"],
    "bracket_left": ["[", "26"],
    "bracket_right": ["]", "27"],
    "comma": [",", "51"],
    "period": [".", "52"],
}
