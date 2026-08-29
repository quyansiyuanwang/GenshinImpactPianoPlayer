"""Responsive rectangles for the settings surface."""

from __future__ import annotations

from dataclasses import dataclass

from src.ui.cli.components import Rect


@dataclass(frozen=True)
class SettingsLayout:
    """Layout calculated from the current terminal dimensions."""

    bounds: Rect
    sidebar: Rect
    content: Rect
    header: Rect
    footer: Rect

    @classmethod
    def from_size(cls, height: int, width: int) -> "SettingsLayout":
        bounds = Rect(0, 0, max(0, height), max(0, width))
        footer_height = 2 if height >= 4 else 1
        header_height = 2 if height >= 3 else 1
        sidebar_width = min(26, max(18, width // 3)) if width >= 42 else max(0, width // 3)
        sidebar = Rect(header_height, 0, max(0, height - header_height - footer_height), sidebar_width)
        content = Rect(
            header_height,
            sidebar_width + (1 if sidebar_width else 0),
            max(0, height - header_height - footer_height),
            max(0, width - sidebar_width - (1 if sidebar_width else 0)),
        )
        return cls(
            bounds,
            sidebar,
            content,
            Rect(0, 0, header_height, width),
            Rect(max(0, height - footer_height), 0, footer_height, width),
        )

    @property
    def compact(self) -> bool:
        return self.bounds.width < 60 or self.bounds.height < 16


def clip(text: object, width: int) -> str:
    """Clip a cell to its available width."""
    return str(text)[: max(0, width - 1)]
