from ..Consts import consts


class Config:
    player_keys = (
        "player_interval",
        "arpeggio_interval",
        "interval_rating",
        "space_interval_rating",
        "horn_mode_interval",
        "line_interval_rating",
        "strict_limited",
    )
    player_interval: float = consts.DEFAULT_PLAYER_INTERVAL
    arpeggio_interval: float = consts.DEFAULT_ARPEGGIO_INTERVAL
    interval_rating: float = consts.DEFAULT_INTERVAL_RATING
    space_interval_rating: float = consts.DEFAULT_SPACE_INTERVAL_RATING
    horn_mode_interval: float = consts.DEFAULT_HORN_MODE_INTERVAL
    line_interval_rating: int = consts.DEFAULT_LINE_INTERVAL_RATING

    space_fills: bool = consts.SPACE_FILLS
    strict_limited: bool = consts.STRICT_LIMITED
    music_start_line: int = consts.MUSIC_START_LINE
    music_path: str = consts.MUSIC_PATH

    @staticmethod
    def reset():
        Config.player_interval = consts.DEFAULT_PLAYER_INTERVAL
        Config.arpeggio_interval = consts.DEFAULT_ARPEGGIO_INTERVAL
        Config.interval_rating = consts.DEFAULT_INTERVAL_RATING
        Config.space_interval_rating = consts.DEFAULT_SPACE_INTERVAL_RATING
        Config.horn_mode_interval = consts.DEFAULT_HORN_MODE_INTERVAL
        Config.line_interval_rating = consts.DEFAULT_LINE_INTERVAL_RATING

        Config.space_fills = consts.SPACE_FILLS
        Config.strict_limited = consts.STRICT_LIMITED
        Config.music_start_line = consts.MUSIC_START_LINE
        Config.music_path = consts.MUSIC_PATH
