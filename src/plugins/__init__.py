"""Built-in plugins for GIPianoPlayer."""

from typing import Callable

from src.plugin_system import Plugin, PluginContext

# Import config plugins
from src.plugins.config_plugins import (
    ConfigManagerPlugin,
    SpeedAdjustmentPlugin,
    IntervalAdjustmentPlugin,
    SegmentAdjustmentPlugin,
    ModeTogglePlugin,
)

__all__ = [
    "SpeedControlPlugin",
    "LoopPlugin",
    "MetronomePlugin",
    "BookmarkPlugin",
    "ConfigManagerPlugin",
    "SpeedAdjustmentPlugin",
    "IntervalAdjustmentPlugin",
    "SegmentAdjustmentPlugin",
    "ModeTogglePlugin",
]


class SpeedControlPlugin(Plugin):
    """Plugin for advanced speed control features."""

    def __init__(self) -> None:
        """Initialize speed control plugin."""
        super().__init__("speed_control", "1.0.0")
        self._speed_presets = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        self._current_preset_index = 2  # Default to 1.0x

    def initialize(self, context: PluginContext) -> None:
        """Initialize plugin with context."""
        # Register custom hotkeys
        context.register_hotkey("ctrl+shift+up", self._next_speed_preset)
        context.register_hotkey("ctrl+shift+down", self._prev_speed_preset)
        context.register_hotkey("ctrl+0", self._reset_speed)

    def _next_speed_preset(self) -> None:
        """Switch to next speed preset."""
        if not self.enabled:
            return
        self._current_preset_index = min(
            self._current_preset_index + 1, len(self._speed_presets) - 1
        )
        # Would set speed on player here

    def _prev_speed_preset(self) -> None:
        """Switch to previous speed preset."""
        if not self.enabled:
            return
        self._current_preset_index = max(self._current_preset_index - 1, 0)
        # Would set speed on player here

    def _reset_speed(self) -> None:
        """Reset speed to 1.0x."""
        if not self.enabled:
            return
        self._current_preset_index = 2  # 1.0x
        # Would set speed on player here


class LoopPlugin(Plugin):
    """Plugin for looping sections of the score."""

    def __init__(self) -> None:
        """Initialize loop plugin."""
        super().__init__("loop", "1.0.0")
        self._loop_start: int | None = None
        self._loop_end: int | None = None
        self._loop_enabled = False

    def initialize(self, context: PluginContext) -> None:
        """Initialize plugin with context."""
        # Register loop control hotkeys
        context.register_hotkey("ctrl+[", self._set_loop_start)
        context.register_hotkey("ctrl+]", self._set_loop_end)
        context.register_hotkey("ctrl+l", self._toggle_loop)
        context.register_hotkey("ctrl+shift+l", self._clear_loop)

    def _set_loop_start(self) -> None:
        """Set loop start point at current position."""
        if not self.enabled:
            return
        # Would get current position from player
        self._loop_start = 0  # Placeholder

    def _set_loop_end(self) -> None:
        """Set loop end point at current position."""
        if not self.enabled:
            return
        # Would get current position from player
        self._loop_end = 0  # Placeholder

    def _toggle_loop(self) -> None:
        """Toggle loop on/off."""
        if not self.enabled:
            return
        self._loop_enabled = not self._loop_enabled

    def _clear_loop(self) -> None:
        """Clear loop points."""
        if not self.enabled:
            return
        self._loop_start = None
        self._loop_end = None
        self._loop_enabled = False


class MetronomePlugin(Plugin):
    """Plugin for metronome functionality."""

    def __init__(self) -> None:
        """Initialize metronome plugin."""
        super().__init__("metronome", "1.0.0")
        self._metronome_enabled = False
        self._bpm = 120

    def initialize(self, context: PluginContext) -> None:
        """Initialize plugin with context."""
        # Register metronome hotkeys
        context.register_hotkey("ctrl+m", self._toggle_metronome)
        context.register_hotkey("ctrl+shift+,", self._decrease_bpm)
        context.register_hotkey("ctrl+shift+.", self._increase_bpm)

    def _toggle_metronome(self) -> None:
        """Toggle metronome on/off."""
        if not self.enabled:
            return
        self._metronome_enabled = not self._metronome_enabled

    def _decrease_bpm(self) -> None:
        """Decrease BPM by 5."""
        if not self.enabled:
            return
        self._bpm = max(40, self._bpm - 5)

    def _increase_bpm(self) -> None:
        """Increase BPM by 5."""
        if not self.enabled:
            return
        self._bpm = min(240, self._bpm + 5)


class BookmarkPlugin(Plugin):
    """Plugin for bookmarking positions in the score."""

    def __init__(self) -> None:
        """Initialize bookmark plugin."""
        super().__init__("bookmark", "1.0.0")
        self._bookmarks: dict[int, int] = {}  # slot -> line number

    def initialize(self, context: PluginContext) -> None:
        """Initialize plugin with context."""
        # Register bookmark hotkeys (Ctrl+1-9 to set, Alt+1-9 to jump)
        for i in range(1, 10):

            def make_set_callback(slot: int) -> Callable[[], None]:
                return lambda: self._set_bookmark(slot)

            def make_jump_callback(slot: int) -> Callable[[], None]:
                return lambda: self._jump_to_bookmark(slot)

            context.register_hotkey(f"ctrl+{i}", make_set_callback(i))
            context.register_hotkey(f"alt+{i}", make_jump_callback(i))

    def _set_bookmark(self, slot: int) -> None:
        """Set bookmark at current position.

        Args:
            slot: Bookmark slot (1-9)
        """
        if not self.enabled:
            return
        # Would get current line from player
        self._bookmarks[slot] = 0  # Placeholder

    def _jump_to_bookmark(self, slot: int) -> None:
        """Jump to bookmarked position.

        Args:
            slot: Bookmark slot (1-9)
        """
        if not self.enabled or slot not in self._bookmarks:
            return
        # Would jump to line on player
