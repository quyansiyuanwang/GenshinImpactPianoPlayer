"""Playback configuration and command hints shown below the score."""

from __future__ import annotations

from typing import Any

from src.application.config.constants import SKIP_LARGE, SKIP_SMALL


def configuration_lines(host: Any) -> list[str]:
    """Build the complete configuration context for the current player."""
    player = host.player
    if not player:
        return []
    hotkeys = host.hotkeys
    range_a, range_b = player.get_range()
    if range_a is not None and range_b is not None and range_a < range_b:
        range_status = "looping"
    elif range_a is not None:
        range_status = "A set"
    elif range_b is not None:
        range_status = "B set"
    else:
        range_status = "off"
    bookmark = player.get_bookmark()
    bookmark_status = f"line {bookmark[0] + 1}" if bookmark else "none"
    segment = (
        f"{player._segment_length} notes" if player._segment_length > 0 else "Disabled"
    )
    strict = (
        " (Strict)"
        if player.get_segment_strict() and player._segment_length > 0
        else ""
    )
    arpeggio = (
        "automatic"
        if player.get_arpeggio_auto()
        else f"manual ({player._arpeggio_interval:.3f}s)"
    )
    keyboard_state = "LOCKED" if host._keyboard_locked else "active"
    return [
        "Configuration:",
        f"  Speed: {player._speed_multiplier:.2f}x  [{hotkeys['speed_down']}/{hotkeys['speed_up']}] Adjust  [{hotkeys['speed_down_large']}/{hotkeys['speed_up_large']}] Large",
        f"  Note Interval: {player._interval_rating:.3f}s  [{hotkeys['interval_shorter']}/{hotkeys['interval_longer']}] Adjust",
        f"  Arpeggio: {arpeggio}  [{hotkeys['arpeggio_shorter']}/{hotkeys['arpeggio_longer']}] Adjust  [{hotkeys['toggle_arpeggio_auto']}] Auto",
        f"  Line Interval: {player._line_interval_rating:.0f} notes  [{hotkeys['line_interval_less']}/{hotkeys['line_interval_more']}] Adjust",
        f"  Space Interval: {player._space_interval_rating:.1f}x  [{hotkeys['space_interval_less']}/{hotkeys['space_interval_more']}] Adjust",
        f"  Empty Line: {player._empty_line_interval_rating:.0f} notes  [{hotkeys['empty_line_interval_less']}/{hotkeys['empty_line_interval_more']}] Adjust",
        f"  Segment Length: {segment}{strict}  [{hotkeys['segment_length_less']}/{hotkeys['segment_length_more']}] Adjust  [{hotkeys['toggle_segment_strict']}] Strict",
        f"  Sustain: {'ON' if player.get_sustain_enabled() else 'OFF'}  [{hotkeys['toggle_sustain']}] Toggle",
        f"  Loop: {'ON' if player.get_loop_enabled() else 'OFF'}  [{hotkeys['toggle_loop']}] Toggle",
        f"  Line Repeat: {'ON' if player.get_line_loop_enabled() else 'OFF'}  [{hotkeys['toggle_line_loop']}] Toggle",
        f"  Range: {range_status}  [{hotkeys['set_range_a']}/{hotkeys['set_range_b']}] Set  [{hotkeys['clear_range']}] Clear",
        f"  Bookmark: {bookmark_status}  [{hotkeys['set_bookmark']}] Set  [{hotkeys['jump_to_bookmark']}] Jump",
        f"  Keyboard Input: {keyboard_state}  [{hotkeys['toggle_output_lock']}] Toggle",
        f"  Key Mapping: {len(player.get_key_mapping())} key(s)  Playlist: {len(host.playlist.entries)} track(s)",
    ]


def visible_configuration(lines: list[str], height: int) -> list[str]:
    """Keep important context visible when vertical space is constrained."""
    if height >= len(lines):
        return lines
    priorities = [0, 1, 2, 3, 9, 13, 8, 10, 11, 12, 4, 5, 6, 7, 14]
    return [lines[index] for index in priorities[:height] if index < len(lines)]


def control_hints(host: Any) -> list[str]:
    """Return the complete command legend for the dedicated footer."""
    hotkeys = host.hotkeys
    return [
        f"Controls: [{hotkeys['play_pause']}] Play/Pause  [{hotkeys['quit']}] Quit  [{hotkeys['save']}] Save  [{hotkeys['open_settings']}] Settings  [{hotkeys['toggle_output_lock']}] Lock",
        f"Navigate: [{hotkeys['skip_backward']}/{hotkeys['skip_forward']}] {SKIP_SMALL} note  [{hotkeys['skip_backward_large']}/{hotkeys['skip_forward_large']}] {SKIP_LARGE} line  [{hotkeys['jump_to_start']}/{hotkeys['jump_to_end']}] Start/End",
        f"Files: [{hotkeys['reload']}] Reload  [{hotkeys['reparse']}] Reparse  [Tab] Playlist  [Enter] Load  [A] Add  [/] Search  [N/P] Next/Previous  [D] Remove",
    ]
