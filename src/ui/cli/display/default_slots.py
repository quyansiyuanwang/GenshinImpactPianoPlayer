"""Default display renderers for GIPianoPlayer.

This module registers all default display components.
"""

import os
from typing import TYPE_CHECKING

from src.ui.cli.display.slots import DisplayContext, get_display_slot_registry

if TYPE_CHECKING:
    from src.cli import CLI


def register_default_display_slots(cli: "CLI") -> None:
    """Register all default display slots.

    Args:
        cli: CLI instance
    """
    registry = get_display_slot_registry()

    # Header slot
    registry.register("header", lambda ctx: render_header(ctx, cli), priority=10)

    # Score slot
    registry.register("score", lambda ctx: render_score(ctx, cli), priority=10)

    # Status slot
    registry.register("status", lambda ctx: render_status(ctx, cli), priority=10)

    # Config slot
    registry.register("config", lambda ctx: render_config(ctx, cli), priority=10)

    # Controls slot
    registry.register("controls", lambda ctx: render_controls(ctx, cli), priority=10)


def render_header(context: DisplayContext, cli: "CLI") -> list[str]:
    """Render header section.

    Args:
        context: Display context
        cli: CLI instance

    Returns:
        List of header lines
    """
    separator_width = min(context.width - 1, 100)
    return [
        "GIPianoPlayer - Command Line Interface"[: context.width - 1],
        "=" * separator_width,
        f"File: {os.path.basename(context.file_path)}"[: context.width - 1],
        f"Lines: {len(context.score.lines) if context.score else 0}"[
            : context.width - 1
        ],
        "",
    ]


def render_score(context: DisplayContext, cli: "CLI") -> list[str]:
    """Render score section.

    Args:
        context: Display context
        cli: CLI instance

    Returns:
        List of score lines
    """
    if not context.score:
        return ["No score loaded"]

    lines: list[str] = []

    # Calculate visible range
    # This is simplified - the actual implementation would be more complex
    start_line = max(0, context.current_line - 3)
    end_line = min(len(context.score.lines), context.current_line + 7)

    # Show indicator if there are lines before
    if start_line > 0:
        lines.append(f"    ... ({start_line} lines above) ..."[: context.width - 1])
        lines.append("")

    # Display visible lines
    for line_idx in range(start_line, end_line):
        line = context.score.lines[line_idx]
        line_num = f"{line_idx + 1:4d}. "

        # Format the line (simplified)
        line_text = (
            cli._format_score_line(line) if hasattr(cli, "_format_score_line") else ""
        )

        # Add color/highlighting based on position
        if line_idx < context.current_line:
            # Already played
            lines.append(f"{line_num}{line_text}"[: context.width - 1])
        elif line_idx == context.current_line:
            # Current line
            lines.append(f"{line_num}{line_text}"[: context.width - 1])
        else:
            # Not yet played
            lines.append(f"{line_num}{line_text}"[: context.width - 1])

    # Show indicator if there are lines after
    if end_line < len(context.score.lines):
        lines.append("")
        lines.append(
            f"    ... ({len(context.score.lines) - end_line} lines below) ..."[
                : context.width - 1
            ]
        )

    return lines


def render_status(context: DisplayContext, cli: "CLI") -> list[str]:
    """Render status section.

    Args:
        context: Display context
        cli: CLI instance

    Returns:
        List of status lines
    """
    separator_width = min(context.width - 1, 100)
    lines = ["", "=" * separator_width]

    # Status line
    state = context.player.get_state().value.upper() if context.player else "STOPPED"

    # Calculate progress
    if context.player and context.total_lines > 0 and context.score:
        total_notes = sum(len(line) for line in context.score.lines)
        played_notes = sum(
            len(context.score.lines[i]) for i in range(context.current_line)
        )
        played_notes += context.current_note
        progress = (played_notes / total_notes * 100) if total_notes > 0 else 0
        status_text = f"Status: {state} | Line {context.current_line + 1}/{context.total_lines} | Note {played_notes}/{total_notes} | Progress: {progress:.1f}%"
    else:
        status_text = f"Status: {state} | Line {context.current_line + 1}/{context.total_lines} | Progress: 0.0%"

    lines.append(status_text[: context.width - 1])
    lines.append("")

    return lines


def render_config(context: DisplayContext, cli: "CLI") -> list[str]:
    """Render configuration section.

    Args:
        context: Display context
        cli: CLI instance

    Returns:
        List of config lines
    """
    if not context.player:
        return []

    separator_width = min(context.width - 1, 100)
    lines = [
        "Configuration",
        "-" * separator_width,
    ]

    # Get config values
    speed = context.player._speed_multiplier
    arp_interval = context.player._arpeggio_interval
    arpeggio_auto = context.player.get_arpeggio_auto()
    interval = context.player._interval_rating
    line_interval = context.player._line_interval_rating
    space_interval = context.player._space_interval_rating
    empty_line_interval = context.player._empty_line_interval_rating
    segment_length = context.player._segment_length
    segment_strict = context.player.get_segment_strict()
    sustain_enabled = context.player.get_sustain_enabled()

    # Format config lines
    lines.append(f"  Speed: {speed:.2f}x              [+/-] Adjust speed")
    arpeggio_timing = "automatic" if arpeggio_auto else f"manual {arp_interval:.3f}s"
    lines.append(f"  Arpeggio: {arpeggio_timing}  [[/]] Manual | [F3] Auto")
    lines.append(f"  Note Interval: {interval:.3f}s    [,/.] Adjust interval")
    lines.append(f"  Line Interval: {line_interval:.0f} notes  [Up/Down] Adjust line")
    lines.append(
        f"  Space Interval: {space_interval:.1f}x     [Shift+Up/Down] Adjust space"
    )
    lines.append(
        f"  Empty Line: {empty_line_interval:.0f} notes     [Ctrl+Up/Down] Adjust empty line"
    )

    segment_status = f"{segment_length} notes" if segment_length > 0 else "Disabled"
    strict_indicator = " (Strict)" if segment_strict and segment_length > 0 else ""
    lines.append(
        f"  Segment Length: {segment_status}{strict_indicator}  [PgUp/PgDn] Adjust | [F4] Toggle Strict"
    )

    sustain_status = "ON" if sustain_enabled else "OFF"
    lines.append(f"  Sustain Mode: {sustain_status}        [F7] Toggle")

    lines.append("")

    return lines


def render_controls(context: DisplayContext, cli: "CLI") -> list[str]:
    """Render controls section.

    Args:
        context: Display context
        cli: CLI instance

    Returns:
        List of control lines
    """
    # Only show if keyboard is available
    try:
        import keyboard  # noqa: F401

        return [
            "Controls: [F8] Play/Pause | [F2] Quit | [F5] Reload | [F9] Save Config",
            "          [←/→] Skip Note | [Ctrl+←/→] Skip Line",
            "",
        ]
    except ImportError:
        return []
