"""Default hotkey configuration for GIPianoPlayer.

This module registers all default hotkeys for the player.
"""

from typing import TYPE_CHECKING

from src.hotkey_registry import get_hotkey_registry

if TYPE_CHECKING:
    from src.cli import CLI


def register_default_hotkeys(cli: "CLI") -> None:
    """Register all default hotkeys.

    Args:
        cli: CLI instance with callback methods
    """
    registry = get_hotkey_registry()

    # Playback control
    registry.register(
        "f8",
        cli._toggle_play_pause,
        "Play/Pause playback",
        "playback",
    )
    registry.register(
        "f2",
        cli._quit,
        "Quit application",
        "playback",
    )

    # Speed control
    registry.register(
        "+",
        lambda: cli._adjust_speed(0.01),
        "Increase speed (small)",
        "speed",
    )
    registry.register(
        "-",
        lambda: cli._adjust_speed(-0.01),
        "Decrease speed (small)",
        "speed",
    )
    registry.register(
        "ctrl+=",
        lambda: cli._adjust_speed(0.1),
        "Increase speed (large)",
        "speed",
    )
    registry.register(
        "ctrl+_",
        lambda: cli._adjust_speed(-0.1),
        "Decrease speed (large)",
        "speed",
    )

    # Arpeggio control
    registry.register(
        "[",
        lambda: cli._adjust_arpeggio(-0.01),
        "Faster arpeggio",
        "timing",
    )
    registry.register(
        "]",
        lambda: cli._adjust_arpeggio(0.01),
        "Slower arpeggio",
        "timing",
    )

    # Interval control
    registry.register(
        ",",
        lambda: cli._adjust_interval(-0.01),
        "Decrease note interval",
        "timing",
    )
    registry.register(
        ".",
        lambda: cli._adjust_interval(0.01),
        "Increase note interval",
        "timing",
    )

    # Line interval control
    registry.register(
        "up",
        lambda: cli._adjust_line_interval(1),
        "Increase line interval",
        "timing",
    )
    registry.register(
        "down",
        lambda: cli._adjust_line_interval(-1),
        "Decrease line interval",
        "timing",
    )

    # Space interval control
    registry.register(
        "shift+up",
        lambda: cli._adjust_space_interval(0.1),
        "Increase space interval",
        "timing",
    )
    registry.register(
        "shift+down",
        lambda: cli._adjust_space_interval(-0.1),
        "Decrease space interval",
        "timing",
    )

    # Empty line interval control
    registry.register(
        "ctrl+up",
        lambda: cli._adjust_empty_line_interval(1),
        "Increase empty line interval",
        "timing",
    )
    registry.register(
        "ctrl+down",
        lambda: cli._adjust_empty_line_interval(-1),
        "Decrease empty line interval",
        "timing",
    )

    # Segment length control
    registry.register(
        "page down",
        lambda: cli._adjust_segment_length(-1),
        "Decrease segment length",
        "segment",
    )
    registry.register(
        "page up",
        lambda: cli._adjust_segment_length(1),
        "Increase segment length",
        "segment",
    )

    # Navigation
    registry.register(
        "left",
        cli._skip_backward,
        "Skip backward 1 note",
        "navigation",
    )
    registry.register(
        "right",
        cli._skip_forward,
        "Skip forward 1 note",
        "navigation",
    )
    registry.register(
        "ctrl+left",
        cli._skip_backward_large,
        "Skip backward 1 line",
        "navigation",
    )
    registry.register(
        "ctrl+right",
        cli._skip_forward_large,
        "Skip forward 1 line",
        "navigation",
    )

    # File operations
    registry.register(
        "f5",
        cli._reload,
        "Reload score file",
        "file",
    )
    registry.register(
        "f6",
        cli._reparse,
        "Reparse with current config",
        "file",
    )
    registry.register(
        "f9",
        cli._save_config,
        "Save config to file",
        "file",
    )

    # Mode toggles
    registry.register(
        "f7",
        cli._toggle_sustain,
        "Toggle sustain mode",
        "mode",
    )
    registry.register(
        "f4",
        cli._toggle_segment_strict,
        "Toggle segment strict mode",
        "mode",
    )
