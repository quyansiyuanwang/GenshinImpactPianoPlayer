import os
import sys

from utils import reverse, set_value, increase_value

DEFAULT_PLAYER_INTERVAL: float = 1.0
DEFAULT_ARPEGGIO_INTERVAL: float = 0.05
DEFAULT_INTERVAL_RATING: float = 0.15
DEFAULT_SPACE_INTERVAL_RATING: float = 0.5
DEFAULT_HORN_MODE_INTERVAL: float = 0.01
DEFAULT_LINE_INTERVAL_RATING: int = 0

SPACE_FILLS: bool = True
STRICT_LIMITED: bool = False
IGNORE_BLANK_LINE: bool = True
MUSIC_START_LINE: int = 1

MUSIC_PATH: str = "music.txt"
FIXED_RELATIVE_PATH = r'\keysConfig\keyMap.ini'
EXE_PATH = os.path.dirname(sys.executable)

DEFAULT_DESCRIPTION_LAMBDA_MAP = {
    'start/stop': lambda connection: reverse(connection, 'stop_flag'),
    'exit': lambda connection: set_value(connection, 'running_flag', False),
    'restart': lambda connection: reverse(connection, 'restart'),
    'reset config': lambda connection: reverse(connection, 'reset_config'),
    'hotreload music':
        lambda connection: bool(set_value(connection, 'running_flag', False)) | reverse(connection, 'hot_reload'),
    'increase interval': lambda connection: increase_value(connection, 'adjust_interval', 0.005),
    'decrease interval': lambda connection: increase_value(connection, 'adjust_interval', -0.005),
    'go back': lambda connection: increase_value(connection, 'adjust_progress', -1),
    'go forward': lambda connection: increase_value(connection, 'adjust_progress', 1),
    'double progress': lambda connection: set_value(connection, 'progress_adjust_rating', 2),
    'halve progress': lambda connection: set_value(connection, 'progress_adjust_rating', 0.5),
    'switch mode': lambda connection: reverse(connection, 'delay_press'),
    'increase space interval': lambda connection: increase_value(connection, 'adjust_space_interval', -0.01),
    'decrease space interval': lambda connection: increase_value(connection, 'adjust_space_interval', 0.01),
    'modify shortcut': lambda connection: reverse(connection, 'modify_shortcut'),
    'save shortcut': lambda connection: reverse(connection, 'save_shortcut')
}

DEFAULT_DESCRIPTION_KEY_MAP = {
    'start/stop': 'f1',
    'exit': 'f2',
    'restart': 'f3',
    'reset config': 'f4',
    'hotreload music': 'f5',
    'increase interval': 'up',
    'decrease interval': 'down',
    'go back': 'left',
    'go forward': 'right',
    'double progress': 'p',
    'halve progress': 'o',
    'switch mode': 'i',
    'increase space interval': 'k',
    'decrease space interval': 'l',
    'modify shortcut': 'f6',
    'save shortcut': 'f7'
}
