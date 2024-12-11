from Consts import consts


class Config:
    PLAYER_KEYS = (
        "PLAYER_INTERVAL",
        "ARPEGGIO_INTERVAL",
        "INTERVAL_RATING",
        "SPACE_INTERVAL_RATING",
        "HORN_MODE_INTERVAL",
        "LINE_INTERVAL_RATING",
        "STRICT_LIMITED",
    )
    PLAYER_INTERVAL = consts.DEFAULT_PLAYER_INTERVAL
    ARPEGGIO_INTERVAL = consts.DEFAULT_ARPEGGIO_INTERVAL
    INTERVAL_RATING = consts.DEFAULT_INTERVAL_RATING
    SPACE_INTERVAL_RATING = consts.DEFAULT_SPACE_INTERVAL_RATING
    HORN_MODE_INTERVAL = consts.DEFAULT_HORN_MODE_INTERVAL
    LINE_INTERVAL_RATING = consts.DEFAULT_LINE_INTERVAL_RATING

    SPACE_FILLS = consts.SPACE_FILLS
    STRICT_LIMITED = consts.STRICT_LIMITED
    MUSIC_START_LINE = consts.MUSIC_START_LINE
    MUSIC_PATH = consts.MUSIC_PATH

    @staticmethod
    def reset():
        Config.PLAYER_INTERVAL = consts.DEFAULT_PLAYER_INTERVAL
        Config.ARPEGGIO_INTERVAL = consts.DEFAULT_ARPEGGIO_INTERVAL
        Config.INTERVAL_RATING = consts.DEFAULT_INTERVAL_RATING
        Config.SPACE_INTERVAL_RATING = consts.DEFAULT_SPACE_INTERVAL_RATING
        Config.HORN_MODE_INTERVAL = consts.DEFAULT_HORN_MODE_INTERVAL
        Config.LINE_INTERVAL_RATING = consts.DEFAULT_LINE_INTERVAL_RATING

        Config.SPACE_FILLS = consts.SPACE_FILLS
        Config.STRICT_LIMITED = consts.STRICT_LIMITED
        Config.MUSIC_START_LINE = consts.MUSIC_START_LINE
        Config.MUSIC_PATH = consts.MUSIC_PATH
