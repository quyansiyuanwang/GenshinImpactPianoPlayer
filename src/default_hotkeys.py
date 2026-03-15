"""Default hotkey configuration for GIPianoPlayer.

This module registers all default hotkeys for the player.
"""

from typing import TYPE_CHECKING

from src.hotkey_registry import get_hotkey_registry
from src.plugin_system import get_plugin_manager

if TYPE_CHECKING:
    from src.cli import CLI


def register_default_hotkeys(cli: "CLI") -> None:
    """Register all default hotkeys.

    Args:
        cli: CLI instance with callback methods
    """
    registry = get_hotkey_registry()
    plugin_manager = get_plugin_manager()

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

    # Get plugin instances for config operations
    speed_plugin = plugin_manager.get_plugin("speed_adjustment")
    interval_plugin = plugin_manager.get_plugin("interval_adjustment")
    segment_plugin = plugin_manager.get_plugin("segment_adjustment")
    mode_plugin = plugin_manager.get_plugin("mode_toggle")

    # Speed control (via plugin)
    if speed_plugin:
        registry.register(
            "+",
            lambda: speed_plugin.adjust_speed(0.01),  # type: ignore[attr-defined]
            "Increase speed (small)",
            "speed",
        )
        registry.register(
            "-",
            lambda: speed_plugin.adjust_speed(-0.01),  # type: ignore[attr-defined]
            "Decrease speed (small)",
            "speed",
        )
        registry.register(
            "ctrl+=",
            lambda: speed_plugin.adjust_speed(0.1),  # type: ignore[attr-defined]
            "Increase speed (large)",
            "speed",
        )
        registry.register(
            "ctrl+_",
            lambda: speed_plugin.adjust_speed(-0.1),  # type: ignore[attr-defined]
            "Decrease speed (large)",
            "speed",
        )

    # Interval control (via plugin)
    if interval_plugin:
        # Arpeggio
        registry.register(
            "[",
            lambda: interval_plugin.adjust_arpeggio(-0.01),  # type: ignore[attr-defined]
            "Faster arpeggio",
            "timing",
        )
        registry.register(
            "]",
            lambda: interval_plugin.adjust_arpeggio(0.01),  # type: ignore[attr-defined]
            "Slower arpeggio",
            "timing",
        )

        # Note interval
        registry.register(
            ",",
            lambda: interval_plugin.adjust_interval(-0.01),  # type: ignore[attr-defined]
            "Decrease note interval",
            "timing",
        )
        registry.register(
            ".",
            lambda: interval_plugin.adjust_interval(0.01),  # type: ignore[attr-defined]
            "Increase note interval",
            "timing",
        )

        # Line interval
        registry.register(
            "up",
            lambda: interval_plugin.adjust_line_interval(1),  # type: ignore[attr-defined]
            "Increase line interval",
            "timing",
        )
        registry.register(
            "down",
            lambda: interval_plugin.adjust_line_interval(-1),  # type: ignore[attr-defined]
            "Decrease line interval",
            "timing",
        )

        # Space interval
        registry.register(
            "shift+up",
            lambda: interval_plugin.adjust_space_interval(0.1),  # type: ignore[attr-defined]
            "Increase space interval",
            "timing",
        )
        registry.register(
            "shift+down",
            lambda: interval_plugin.adjust_space_interval(-0.1),  # type: ignore[attr-defined]
            "Decrease space interval",
            "timing",
        )

        # Empty line interval
        registry.register(
            "ctrl+up",
            lambda: interval_plugin.adjust_empty_line_interval(1),  # type: ignore[attr-defined]
            "Increase empty line interval",
            "timing",
        )
        registry.register(
            "ctrl+down",
            lambda: interval_plugin.adjust_empty_line_interval(-1),  # type: ignore[attr-defined]
            "Decrease empty line interval",
            "timing",
        )

    # Segment control (via plugin)
    if segment_plugin:
        registry.register(
            "page down",
            lambda: segment_plugin.adjust_segment_length(-1),  # type: ignore[attr-defined]
            "Decrease segment length",
            "segment",
        )
        registry.register(
            "page up",
            lambda: segment_plugin.adjust_segment_length(1),  # type: ignore[attr-defined]
            "Increase segment length",
            "segment",
        )
        registry.register(
            "f4",
            lambda: segment_plugin.toggle_segment_strict(),  # type: ignore[attr-defined]
            "Toggle segment strict mode",
            "segment",
        )

    # Mode toggles (via plugin)
    if mode_plugin:
        registry.register(
            "f7",
            lambda: mode_plugin.toggle_sustain(),  # type: ignore[attr-defined]
            "Toggle sustain mode",
            "mode",
        )

    # Navigation (still via CLI)
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

    # File operations (still via CLI)
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

    # Config save is now handled by ConfigManagerPlugin (F9)
    # It registers itself in its initialize() method

