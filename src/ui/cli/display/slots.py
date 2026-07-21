"""Display slot system for GIPianoPlayer.

Provides a slot-based system for customizing the CLI display.
Different components can register themselves to be rendered in specific slots.
"""

from typing import Any, Callable, Protocol


class DisplaySlot(Protocol):
    """Protocol for display slot renderers."""

    def render(self, context: "DisplayContext") -> list[str]:
        """Render content for this slot.

        Args:
            context: Display context with current state

        Returns:
            List of strings to display (one per line)
        """
        ...


class DisplayContext:
    """Context provided to display slot renderers."""

    def __init__(
        self,
        player: Any = None,
        score: Any = None,
        current_line: int = 0,
        current_note: int = 0,
        total_lines: int = 0,
        width: int = 80,
        height: int = 24,
        file_path: str = "",
    ) -> None:
        """Initialize display context.

        Args:
            player: Player instance
            score: Parsed score
            current_line: Current line number
            current_note: Current note number
            total_lines: Total number of lines
            width: Terminal width
            height: Terminal height
            file_path: Score file path
        """
        self.player = player
        self.score = score
        self.current_line = current_line
        self.current_note = current_note
        self.total_lines = total_lines
        self.width = width
        self.height = height
        self.file_path = file_path


class DisplaySlotRegistry:
    """Registry for display slots."""

    def __init__(self) -> None:
        """Initialize display slot registry."""
        self._slots: dict[
            str, list[tuple[int, Callable[[DisplayContext], list[str]]]]
        ] = {
            "header": [],
            "score": [],
            "footer": [],
            "status": [],
            "config": [],
            "controls": [],
        }

    def register(
        self,
        slot: str,
        renderer: Callable[[DisplayContext], list[str]],
        priority: int = 100,
    ) -> None:
        """Register a renderer for a display slot.

        Args:
            slot: Slot name (header, score, footer, status, config, controls)
            renderer: Function that renders content
            priority: Priority (lower = rendered first)
        """
        if slot not in self._slots:
            raise ValueError(f"Unknown slot: {slot}")

        self._slots[slot].append((priority, renderer))
        # Sort by priority
        self._slots[slot].sort(key=lambda x: x[0])

    def unregister(
        self, slot: str, renderer: Callable[[DisplayContext], list[str]]
    ) -> None:
        """Unregister a renderer from a slot.

        Args:
            slot: Slot name
            renderer: Renderer function to remove
        """
        if slot in self._slots:
            self._slots[slot] = [(p, r) for p, r in self._slots[slot] if r != renderer]

    def render_slot(self, slot: str, context: DisplayContext) -> list[str]:
        """Render all content for a slot.

        Args:
            slot: Slot name
            context: Display context

        Returns:
            List of lines to display
        """
        if slot not in self._slots:
            return []

        lines: list[str] = []
        for _priority, renderer in self._slots[slot]:
            try:
                rendered = renderer(context)
                lines.extend(rendered)
            except Exception as e:
                lines.append(f"[Error rendering {slot}: {e}]")

        return lines

    def get_slot_names(self) -> list[str]:
        """Get all slot names.

        Returns:
            List of slot names
        """
        return list(self._slots.keys())

    def clear_slot(self, slot: str) -> None:
        """Clear all renderers from a slot.

        Args:
            slot: Slot name
        """
        if slot in self._slots:
            self._slots[slot] = []

    def clear_all(self) -> None:
        """Clear all renderers from all slots."""
        for slot in self._slots:
            self._slots[slot] = []


# Global display slot registry instance
_display_slot_registry = DisplaySlotRegistry()


def get_display_slot_registry() -> DisplaySlotRegistry:
    """Get the global display slot registry instance.

    Returns:
        Global display slot registry
    """
    return _display_slot_registry
