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
    hint: Rect
    footer: Rect

    @classmethod
    def from_size(cls, height: int, width: int, profile_count: int = 0) -> "SettingsLayout":
        bounds = Rect(0, 0, max(0, height), max(0, width))
        footer_height = 2 if height >= 5 else 1
        hint_height = 2 if height >= 7 else 1
        header_height = 2 if height >= 3 else 1
        available_height = max(0, height - header_height - hint_height - footer_height)
        if width < 64:
            sidebar_width = width
            sidebar_height = min(
                available_height,
                max(2, min(profile_count + 2, max(2, available_height // 2))),
            )
            sidebar = Rect(header_height, 0, sidebar_height, sidebar_width)
            content_top = header_height + sidebar_height
            content_height = max(0, available_height - sidebar_height)
            content_left = 0
            content_width = width
        else:
            sidebar_width = min(28, max(22, width // 3))
            sidebar = Rect(header_height, 0, available_height, sidebar_width)
            content_top = header_height
            content_height = available_height
            content_left = sidebar_width + 1
            content_width = max(0, width - content_left)
        content = Rect(
            content_top,
            content_left,
            content_height,
            content_width,
        )
        footer_top = max(0, height - footer_height)
        hint = Rect(max(header_height, footer_top - hint_height), 0, hint_height, width)
        return cls(
            bounds,
            sidebar,
            content,
            Rect(0, 0, header_height, width),
            hint,
            Rect(footer_top, 0, footer_height, width),
        )

    @property
    def compact(self) -> bool:
        return self.bounds.width < 60 or self.bounds.height < 16

    @property
    def stacked(self) -> bool:
        return self.bounds.width < 64


def clip(text: object, width: int) -> str:
    """Clip a cell to its available width."""
    return str(text)[: max(0, width - 1)]
