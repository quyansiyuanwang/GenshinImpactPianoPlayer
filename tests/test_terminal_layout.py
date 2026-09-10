"""Unicode width and responsive playback layout tests."""

from src.ui.cli.main_layout import MainLayout
from src.ui.cli.main_renderer import MainRenderer
from src.ui.cli.terminal_text import cell_width, clip_cells, fit_cells


def test_chinese_text_uses_two_terminal_columns() -> None:
    assert cell_width("A琴B") == 4
    assert clip_cells("曲目名称", 5) == "曲目"
    assert cell_width(fit_cells("琴", 5)) == 5


def test_main_layout_regions_do_not_overlap_at_common_sizes() -> None:
    for height, width in [(40, 140), (28, 90), (16, 60), (9, 30)]:
        layout = MainLayout.from_size(height, width, has_playlist=True)
        regions = [
            layout.header,
            layout.score,
            layout.playlist,
            layout.status,
            layout.details,
            layout.footer,
        ]
        for region in regions:
            assert region.top >= 0
            assert region.left >= 0
            assert region.top + region.height <= height
            assert region.left + region.width <= width

        if layout.playlist.left > layout.score.left:
            assert layout.score.left + layout.score.width < layout.playlist.left
        else:
            assert layout.score.top + layout.score.height <= layout.playlist.top


def test_resize_recalculates_wide_and_stacked_geometry() -> None:
    wide = MainLayout.from_size(30, 120, has_playlist=True)
    narrow = MainLayout.from_size(20, 70, has_playlist=True)
    assert not wide.stacked
    assert wide.playlist.left > wide.score.left
    assert narrow.stacked
    assert narrow.playlist.top > narrow.score.top


def test_score_viewport_grows_with_height_but_remains_bounded() -> None:
    renderer = MainRenderer()
    small_start, small_end, _before, _after = renderer._score_window(100, 50, 7)
    large_start, large_end, _before, _after = renderer._score_window(100, 50, 30)
    assert small_end - small_start < large_end - large_start
    assert large_end - large_start <= 18


def test_compact_layout_preserves_score_rows() -> None:
    medium = MainLayout.from_size(20, 70, has_playlist=True)
    compact = MainLayout.from_size(12, 45, has_playlist=True)
    assert medium.score.height >= 6
    assert compact.score.height >= 3
