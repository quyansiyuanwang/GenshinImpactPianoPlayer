"""Default hotkey declarations for the CLI."""

from typing import TYPE_CHECKING, Callable

from src.application.config.constants import (
    ARPEGGIO_STEP,
    INTERVAL_STEP,
    SPACE_INTERVAL_STEP,
    SPEED_STEP,
    SPEED_STEP_LARGE,
)
from src.ui.cli.input.hotkey_registry import HotkeyRegistry

if TYPE_CHECKING:
    from src.application.host_protocol import ApplicationHost


def register_default_hotkeys(cli: "ApplicationHost", registry: HotkeyRegistry) -> None:
    """Register the built-in CLI actions into a hotkey registry."""
    bindings: dict[str, tuple[Callable[[], None], str, str]] = {
        "play_pause": (cli.toggle_play_pause, "Play or pause playback", "playback"),
        "quit": (cli.quit, "Quit application", "playback"),
        "open_settings": (cli.request_settings, "Open configuration", "general"),
        "save": (cli.save_config, "Save score configuration", "file"),
        "toggle_loop": (cli.toggle_loop, "Toggle looping playback", "playback"),
        "toggle_line_loop": (
            cli.toggle_line_loop,
            "Toggle repeating the current line",
            "playback",
        ),
        "set_range_a": (cli.set_range_a, "Set A-B range start", "playback"),
        "set_range_b": (cli.set_range_b, "Set A-B range end", "playback"),
        "clear_range": (cli.clear_range, "Clear the A-B range", "playback"),
        "set_bookmark": (
            cli.set_bookmark,
            "Bookmark the current position",
            "navigation",
        ),
        "jump_to_bookmark": (
            cli.jump_to_bookmark,
            "Jump back to the bookmark",
            "navigation",
        ),
        "jump_to_start": (
            cli.jump_to_start,
            "Jump to the start of the score",
            "navigation",
        ),
        "jump_to_end": (
            cli.jump_to_end,
            "Jump to the end of the score",
            "navigation",
        ),
        "speed_up": (
            lambda: cli.adjust_speed(SPEED_STEP),
            "Increase speed",
            "speed",
        ),
        "speed_down": (
            lambda: cli.adjust_speed(-SPEED_STEP),
            "Decrease speed",
            "speed",
        ),
        "speed_up_large": (
            lambda: cli.adjust_speed(SPEED_STEP_LARGE),
            "Increase speed by 0.1",
            "speed",
        ),
        "speed_down_large": (
            lambda: cli.adjust_speed(-SPEED_STEP_LARGE),
            "Decrease speed by 0.1",
            "speed",
        ),
        "interval_shorter": (
            lambda: cli.adjust_interval(-INTERVAL_STEP),
            "Decrease note interval",
            "timing",
        ),
        "interval_longer": (
            lambda: cli.adjust_interval(INTERVAL_STEP),
            "Increase note interval",
            "timing",
        ),
        "arpeggio_shorter": (
            lambda: cli.adjust_arpeggio(-ARPEGGIO_STEP),
            "Decrease manual arpeggio interval",
            "timing",
        ),
        "arpeggio_longer": (
            lambda: cli.adjust_arpeggio(ARPEGGIO_STEP),
            "Increase manual arpeggio interval",
            "timing",
        ),
        "toggle_arpeggio_auto": (
            cli.toggle_arpeggio_auto,
            "Toggle automatic arpeggio timing",
            "timing",
        ),
        "line_interval_less": (
            lambda: cli.adjust_line_interval(-1),
            "Decrease line interval",
            "timing",
        ),
        "line_interval_more": (
            lambda: cli.adjust_line_interval(1),
            "Increase line interval",
            "timing",
        ),
        "space_interval_less": (
            lambda: cli.adjust_space_interval(-SPACE_INTERVAL_STEP),
            "Decrease space interval",
            "timing",
        ),
        "space_interval_more": (
            lambda: cli.adjust_space_interval(SPACE_INTERVAL_STEP),
            "Increase space interval",
            "timing",
        ),
        "empty_line_interval_less": (
            lambda: cli.adjust_empty_line_interval(-1),
            "Decrease empty line interval",
            "timing",
        ),
        "empty_line_interval_more": (
            lambda: cli.adjust_empty_line_interval(1),
            "Increase empty line interval",
            "timing",
        ),
        "segment_length_less": (
            lambda: cli.adjust_segment_length(-1),
            "Decrease segment length",
            "segment",
        ),
        "segment_length_more": (
            lambda: cli.adjust_segment_length(1),
            "Increase segment length",
            "segment",
        ),
        "skip_backward": (cli.skip_backward, "Skip backward one note", "navigation"),
        "skip_forward": (cli.skip_forward, "Skip forward one note", "navigation"),
        "skip_backward_large": (
            cli.skip_backward_large,
            "Skip backward one line",
            "navigation",
        ),
        "skip_forward_large": (
            cli.skip_forward_large,
            "Skip forward one line",
            "navigation",
        ),
        "reload": (cli.reload, "Reload score file", "file"),
        "reparse": (cli.reparse, "Reparse score file", "file"),
        "toggle_sustain": (cli.toggle_sustain, "Toggle sustain", "mode"),
        "toggle_segment_strict": (
            cli.toggle_segment_strict,
            "Toggle strict segment mode",
            "segment",
        ),
        "toggle_output_lock": (
            cli.toggle_keyboard_lock,
            "Lock or unlock user controls",
            "playback",
        ),
    }

    for action, (callback, description, category) in bindings.items():
        registry.register(cli.hotkeys[action], callback, description, category)
