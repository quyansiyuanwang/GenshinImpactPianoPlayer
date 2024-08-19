from Consts import consts


class Config:
    ARPEGGIO_INTERVAL = consts.DEFAULT_ARPEGGIO_INTERVAL
    INTERVAL_RATING = consts.DEFAULT_INTERVAL_RATING
    SPACE_INTERVAL_RATING = consts.DEFAULT_SPACE_INTERVAL_RATING
    HORN_MODE_INTERVAL = consts.DEFAULT_HORN_MODE_INTERVAL
    LINE_INTERVAL_RATING = consts.DEFAULT_LINE_INTERVAL_RATING

    SPACE_FILLS = consts.SPACE_FILLS
    MUSIC_START_LINE = consts.MUSIC_START_LINE
    MUSIC_PATH = consts.MUSIC_PATH

    @staticmethod
    def reset():
        Config.ARPEGGIO_INTERVAL = consts.DEFAULT_ARPEGGIO_INTERVAL
        Config.INTERVAL_RATING = consts.DEFAULT_INTERVAL_RATING
        Config.SPACE_INTERVAL_RATING = consts.DEFAULT_SPACE_INTERVAL_RATING
        Config.HORN_MODE_INTERVAL = consts.DEFAULT_HORN_MODE_INTERVAL
        Config.LINE_INTERVAL_RATING = consts.DEFAULT_LINE_INTERVAL_RATING

        Config.SPACE_FILLS = consts.SPACE_FILLS
        Config.MUSIC_START_LINE = consts.MUSIC_START_LINE
        Config.MUSIC_PATH = consts.MUSIC_PATH