import os
import sys
import time
from threading import Thread

import keyboard

ARPEGGIO_INTERVAL = 0.05
INTERVAL_RATING = 0.15
SPACE_INTERVAL_RATING = 0.5
MUSIC_START_LINE = 1
MUSIC_PATH = "music.txt"


class Controller:
    @staticmethod
    def press(syllable):
        is_arpeggio = syllable.is_arpeggio

        print(syllable, end="", flush=True)
        if syllable.is_space: return

        for _k in syllable.word:
            if is_arpeggio: time.sleep(ARPEGGIO_INTERVAL)
            keyboard.press_and_release(_k.lower())


class Connection:
    def __init__(
            self, *,
            running_flag=True,
            stop_flag=True,
            progress_adjust_rating=1,
            adjust_interval=0,
            adjust_progress=0
    ):
        self.running_flag = running_flag
        self.stop_flag = stop_flag
        self.adjust_interval = adjust_interval
        self.adjust_progress = adjust_progress
        self.pg_ad_rating = progress_adjust_rating


class Syllable:
    def __init__(self, word, is_arpeggio=False):
        self.word = word
        self.is_arpeggio = is_arpeggio
        self.is_space = (word == " ")
        self.is_multitone = (len(word) > 1)

    def __str__(self):
        if self.is_space: return "_"

        if self.is_arpeggio:
            return f"[{self.word}]"
        elif self.is_multitone:
            return f"({self.word})"
        else:
            return f"{self.word}"

    def __repr__(self):
        return self.__str__()


class PianoPlayer:
    def __init__(self, connection):
        self.conn = connection
        self.syllables = []
        self.interval = 0.5
        self.idx = 0
        self.interval_changes = 0
        self.pg_ad_rating = 1

    @property
    def length(self):
        return len(self.syllables)

    def add_syllables(self, syllables):
        for syllable in syllables:
            self.syllables.append(syllable)
        return self

    @property
    def interval_(self):
        if self.current_syllable.word == " ":
            return self.r_interval * SPACE_INTERVAL_RATING
        return self.r_interval

    @property
    def r_interval(self):
        return self.interval * INTERVAL_RATING + self.interval_changes

    @interval_.setter
    def interval_(self, value):
        self.interval = value

    @property
    def percentage(self):
        return (self.idx + 1) / self.length

    @property
    def current_syllable(self):
        return self.syllables[self.idx]

    def display_title(self):
        percent = self.percentage
        interval = self.r_interval
        os.system(
            f"title "
            f"{percent * 100:.2f}%  "
            f"{'Running' if not self.conn.stop_flag else 'Stopped'}  "
            f"[{self.interval:.4f}s - {1 / (interval / INTERVAL_RATING):.3f}Hz]  "
            f"APR:{self.pg_ad_rating}  "
            f"{self.current_syllable}"
        )

    def sleep(self):
        time.sleep(self.interval_)

    def change_args(self):
        if self.conn.pg_ad_rating:
            self.pg_ad_rating *= self.conn.pg_ad_rating
            self.conn.pg_ad_rating = 0

        if self.conn.adjust_interval:
            self.interval_changes += self.conn.adjust_interval
            self.conn.adjust_interval = 0

        if self.conn.adjust_progress:
            self.idx += int(self.conn.adjust_progress * self.pg_ad_rating)
            self.display_music(self.idx)
            self.conn.adjust_progress = 0

    def display_music(self, end):
        os.system("cls")
        display_default_info()
        print("".join(map(str, self.syllables[:end])), end="", flush=True)

    def check_stop(self):
        if not self.conn.running_flag: return True
        while self.conn.stop_flag:
            if not self.conn.running_flag: return True
            self.change_args()
            self.display_title()
        return False

    def play(self):
        while self.idx < self.length:

            self.change_args()
            self.display_title()
            self.sleep()

            if self.check_stop(): return

            Controller.press(self.current_syllable)

            self.idx += 1

    def __str__(self):
        syllables = ".".join([str(syllable) for syllable in self.syllables])
        return f"U{self.interval}\n{syllables}"


class FileAnalyzer:
    def __init__(self, filename, connection):
        self.filename = filename
        self.syllables = []
        self.content = None
        self.conn = connection

    def read_content(self):
        with open(self.filename, "r", encoding='utf8') as file:
            self.content = file.read().split('\n')
        return self

    @staticmethod
    def content_analyze(content):
        syllables = []
        length = len(content)
        idx = 0
        while idx < length:
            if content[idx] == "/":
                pass

            elif content[idx] in ("(", "[", "{"):
                left_quote = idx
                while idx < length and content[idx] not in (")", "]", "}"): idx += 1

                syllables.append(Syllable(
                    content[left_quote + 1:idx],
                    is_arpeggio=bool(content[idx] != ")")
                ))

            else:
                syllables.append(Syllable(content[idx].replace(u"\xa0", " ")))

            idx += 1

        return syllables

    def analyze(self):
        song_player = PianoPlayer(self.conn)
        song_player.interval = 1 / float(self.content[0])

        for syllable in self.content[MUSIC_START_LINE:]:
            song_player.add_syllables(FileAnalyzer.content_analyze(syllable))
            song_player.add_syllables([Syllable(" ")])

        return song_player

    def __str__(self):
        return f"{self.syllables}"


def user_enter_monitor():
    try:
        if (key_event := keyboard.read_event()).event_type == keyboard.KEY_DOWN:
            return key_event.name
    except KeyboardInterrupt:
        pass


class Monitor(Thread):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn

    def run(self):
        while (res_k := user_enter_monitor()) != "f2":
            if res_k == "f1":
                self.conn.stop_flag = not self.conn.stop_flag
            elif res_k == "up":
                self.conn.adjust_interval += 0.005
            elif res_k == "down":
                self.conn.adjust_interval -= 0.005
            elif res_k == "left":
                self.conn.adjust_progress -= 1
            elif res_k == "right":
                self.conn.adjust_progress += 1
            elif res_k == "p":
                self.conn.pg_ad_rating = 2
            elif res_k == "o":
                self.conn.pg_ad_rating = 0.5

        self.conn.running_flag = False


def load_config():
    global ARPEGGIO_INTERVAL, INTERVAL_RATING, SPACE_INTERVAL_RATING, MUSIC_START_LINE
    with open(MUSIC_PATH, 'r') as file:
        lines = file.read().split('\n')

    for idx, line in enumerate(lines):
        if line.startswith("ARPEGGIO_INTERVAL"):
            ARPEGGIO_INTERVAL = float(line.split('=')[-1])
        elif line.startswith("INTERVAL_RATING"):
            INTERVAL_RATING = float(line.split('=')[-1])

        elif line.startswith("SPACE_INTERVAL_RATING"):
            SPACE_INTERVAL_RATING = float(line.split('=')[-1])

        elif line.startswith("-"):
            MUSIC_START_LINE = idx + 1


def display_default_info():
    print(
        "Press F1 to start/stop, F2 to exit, UP to increase interval, DOWN to decrease interval\n"
        "LEFT to go back, RIGHT to go forward, P to double progress, O to halve progress"
    )
    print(f"Play the song of `{MUSIC_PATH}`")
    print(
        f"arpeggio_interval: {ARPEGGIO_INTERVAL}"
        f", interval_rating: {INTERVAL_RATING}"
        f", space_interval_rating: {SPACE_INTERVAL_RATING}"
    )


def main(argv):
    global MUSIC_PATH
    MUSIC_PATH = argv[1]
    load_config()
    display_default_info()

    c = Connection()
    while c.running_flag:
        m = Monitor(c)
        m.start()
        FileAnalyzer(MUSIC_PATH, c).read_content().analyze().play()
        m.join()


if __name__ == '__main__':
    main(sys.argv)
    # main(["", r"D:\Developments\GenshinImpactPianoPlayer\music\aLiEz.txt"])
