"""Responsive geometry for the playback screen."""

from __future__ import annotations

from dataclasses import dataclass

from src.ui.cli.components import Rect


@dataclass(frozen=True)
class MainLayout:
    bounds: Rect
    header: Rect
    score: Rect
    playlist: Rect
    status: Rect
    details: Rect
    footer: Rect
    stacked: bool
    tiny: bool

    @classmethod
    def from_size(cls, height: int, width: int, *, has_playlist: bool) -> "MainLayout":
        height = max(0, height)
        width = max(0, width)
        bounds = Rect(0, 0, height, width)
        tiny = width < 36 or height < 10
        header_height = min(height, 3 if not tiny else 2)
        footer_height = 0 if height < 8 else (2 if height >= 16 else 1)
        details_height = 4 if height >= 25 else (2 if height >= 18 else 0)
        status_height = 2 if height >= 7 else 1
        body_height = max(
            0,
            height - header_height - footer_height - details_height - status_height,
        )
        body_top = header_height
        status_top = body_top + body_height
        details_top = status_top + status_height
        footer_top = details_top + details_height

        stacked = has_playlist and (width < 96 or height < 16)
        if not has_playlist:
            score = Rect(body_top, 0, body_height, width)
            playlist = Rect(body_top, width, 0, 0)
        elif tiny:
            score_height = max(1, body_height // 2)
            score = Rect(body_top, 0, score_height, width)
            playlist = Rect(
                body_top + score_height, 0, body_height - score_height, width
            )
        elif stacked:
            playlist_height = min(8, max(4, body_height // 3))
            score = Rect(body_top, 0, max(0, body_height - playlist_height - 1), width)
            playlist = Rect(score.top + score.height + 1, 0, playlist_height, width)
        else:
            playlist_width = min(38, max(28, width // 3))
            score_width = max(0, width - playlist_width - 2)
            score = Rect(body_top, 0, body_height, score_width)
            playlist = Rect(body_top, score_width + 2, body_height, playlist_width)

        return cls(
            bounds,
            Rect(0, 0, header_height, width),
            score,
            playlist,
            Rect(status_top, 0, status_height, width),
            Rect(details_top, 0, details_height, width),
            Rect(footer_top, 0, footer_height, width),
            stacked,
            tiny,
        )
