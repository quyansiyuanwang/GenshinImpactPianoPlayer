import os
import time
from typing import List, Self, Union

from ..Connection import Connection
from ..Consts import consts
from ..Controller import Controller
from ..MusicParse import Syllable
from ..Config import Config as GlobalConfig
from ..MusicParse import Action

Syllables = List[Union[Syllable, Action]]


class PianoPlayer:

    def __init__(
        self,
        syllables: Syllables,
        *,
        connection: Connection,
    ) -> None:
        self.syllables: Syllables = syllables
        self.conn: Connection = connection

        self.idx = 0
        self.interval_changes = 0
        self.progress_adjust_rating = 1

    @property
    def length(self) -> int:
        return len(self.syllables)

    def add_syllables(self, syllables: Syllables) -> Self:
        for syllable in syllables:
            self.syllables.append(syllable)
        return self

    @property
    def interval_(self) -> float:
        if isinstance(self.current_syllable, Action):
            return 0
        if self.current_syllable.words == " ":
            return self.r_interval * GlobalConfig.space_interval_rating
        return self.r_interval

    @property
    def r_interval(self) -> float:
        return (
            GlobalConfig.player_interval * GlobalConfig.interval_rating
            + self.interval_changes
        )

    @interval_.setter
    def interval_(self, value: float) -> None:
        GlobalConfig.player_interval = value

    @property
    def percentage(self) -> float:
        return self.idx / self.length

    @property
    def current_syllable(self) -> Union[Syllable, Action]:
        if self.idx >= self.length:
            return Syllable(words=" ")
        return self.syllables[self.idx]

    def display_title(self) -> None:
        percent = self.percentage
        interval = self.r_interval
        os.system(
            f"title "
            f"{percent * 100:.2f}%  "
            f"{'Running' if not self.conn.stop_flag else 'Stopped'}  "
            f"[{interval:.4f}s - {1 / (interval / GlobalConfig.interval_rating):.3f}Hz]  "
            f"APR:{self.progress_adjust_rating}  "
            f"Mode:{'horn' if self.conn.delay_press else 'piano'}  "
            f"SI:{GlobalConfig.space_interval_rating:.2f}  "
            f"{self.current_syllable}"
        )

    def sleep(self) -> None:
        time.sleep(self.interval_)

    def config_reset(self) -> None:
        self.interval_changes = 0
        self.progress_adjust_rating = 1
        GlobalConfig.interval_rating = consts.DEFAULT_INTERVAL_RATING
        GlobalConfig.space_interval_rating = consts.DEFAULT_SPACE_INTERVAL_RATING
        GlobalConfig.arpeggio_interval = consts.DEFAULT_ARPEGGIO_INTERVAL
        GlobalConfig.horn_mode_interval = consts.DEFAULT_HORN_MODE_INTERVAL

    def restart(self) -> None:
        self.idx = 0
        clear_and_DDI()
        self.display_music(end=self.idx)

    def change_args(self) -> None:
        if self.conn.progress_adjust_rating:
            self.progress_adjust_rating *= self.conn.progress_adjust_rating
            self.conn.progress_adjust_rating = 0

        if self.conn.adjust_interval:
            self.interval_changes += self.conn.adjust_interval
            self.conn.adjust_interval = 0

        if self.conn.adjust_progress:
            self.idx += int(self.conn.adjust_progress * self.progress_adjust_rating)
            clear_and_DDI()
            self.display_music(self.idx)
            self.conn.adjust_progress = 0

        if self.conn.restart:
            self.restart()
            self.conn.restart = False

        if self.conn.adjust_space_interval:
            GlobalConfig.space_interval_rating += self.conn.adjust_space_interval
            self.conn.adjust_space_interval = 0

        if self.conn.reset_config:
            self.config_reset()
            self.conn.reset_config = not self.conn.reset_config

    @staticmethod
    def clear() -> None:
        os.system("cls")

    def display_music(self, end: int) -> None:
        print("".join(map(str, self.syllables[:end])), end="", flush=True)

    def check_stop(self) -> bool:
        if not self.conn.running_flag:
            return True
        if self.conn.stop_flag:
            Controller.release_all()

        while self.conn.stop_flag:
            if not self.conn.running_flag:
                return True

            self.change_args()
            self.display_title()
        return False

    def play(self) -> None:
        while self.idx < self.length:

            self.change_args()
            self.display_title()
            self.sleep()

            if isinstance(self.current_syllable, Action):
                self.current_syllable()
                self.idx += 1
                continue

            if self.current_syllable.is_rest:
                Controller.release_all()
            if self.check_stop():
                return

            if self.conn.delay_press:
                Controller.delay_press(self.current_syllable)
            else:
                Controller.press(self.current_syllable)

            self.idx += 1

    def __str__(self) -> str:
        syllables = ".".join([str(syllable) for syllable in self.syllables])
        return f"U{GlobalConfig.player_interval}\n{syllables}"


def clear_and_DDI() -> None:
    PianoPlayer.clear()
    display_default_info()


def display_default_info() -> None:
    print(f"Play the song of `{GlobalConfig.music_path}`")
    print(
        f"The following are the default data: \n"
        f"arpeggio_interval: {consts.DEFAULT_ARPEGGIO_INTERVAL}"
        f", interval_rating: {consts.DEFAULT_INTERVAL_RATING}"
        f", space_interval_rating: {consts.DEFAULT_SPACE_INTERVAL_RATING}"
        f", horn_mode_interval: {consts.DEFAULT_HORN_MODE_INTERVAL}"
        f", line_interval_rating: {consts.DEFAULT_LINE_INTERVAL_RATING}"
    )
    print(
        f"SPACE_FILLS: {GlobalConfig.space_fills}, "
        f"IGNORE_BLANK_LINE: {consts.IGNORE_BLANK_LINE}, "
        f"STRICT_LIMITED: {consts.STRICT_LIMITED}"
    )
