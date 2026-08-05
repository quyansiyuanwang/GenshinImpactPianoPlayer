"""Default hotkey declarations for the CLI."""

from typing import TYPE_CHECKING, Callable

from src.ui.cli.input.hotkey_registry import HotkeyRegistry

if TYPE_CHECKING:
    from src.cli import CLI


def register_default_hotkeys(cli: "CLI", registry: HotkeyRegistry) -> None:
    """Register the built-in CLI actions into a hotkey registry."""
    bindings: dict[str, tuple[Callable[[], None], str, str]] = {
        "play_pause": (cli.toggle_play_pause, "Play or pause playback", "playback"),
        "quit": (cli.quit, "Quit application", "playback"),
        "speed_up": (lambda: cli.adjust_speed(0.01), "Increase speed", "speed"),
        "speed_down": (lambda: cli.adjust_speed(-0.01), "Decrease speed", "speed"),
        "speed_up_large": (
            lambda: cli.adjust_speed(0.1),
            "Increase speed by 0.1",
            "speed",
        ),
        "speed_down_large": (
            lambda: cli.adjust_speed(-0.1),
            "Decrease speed by 0.1",
            "speed",
        ),
        "interval_shorter": (
            lambda: cli.adjust_interval(-0.01),
            "Decrease note interval",
            "timing",
        ),
        "interval_longer": (
            lambda: cli.adjust_interval(0.01),
            "Increase note interval",
            "timing",
        ),
        "arpeggio_shorter": (
            lambda: cli.adjust_arpeggio(-0.01),
            "Decrease manual arpeggio interval",
            "timing",
        ),
        "arpeggio_longer": (
            lambda: cli.adjust_arpeggio(0.01),
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
    }

    for action, (callback, description, category) in bindings.items():
        registry.register(cli.hotkeys[action], callback, description, category)
