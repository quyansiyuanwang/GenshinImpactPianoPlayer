import os
import sys
import time
from threading import Thread
from typing import List, Union

import keyboard

QUOTE_PAIR = {
    '(': ')',
    '[': ']',
    '{': '}'
}

ARPEGGIO_INTERVAL = 0.05
INTERVAL_RATING = 0.15
SPACE_INTERVAL_RATING = 0.5
MUSIC_START_LINE = 1
HORN_MODE_INTERVAL = 0.01
MUSIC_PATH = "music.txt"


class Controller:
    last_key = None

    @staticmethod
    def press(syllable, display=True):
        if display: print(syllable, end="", flush=True)
        if syllable.is_space: return

        for _k in syllable.words:
            if syllable.is_arpeggio: time.sleep(ARPEGGIO_INTERVAL)
            if isinstance(_k, Syllable): Controller.press(_k, display=False)
            else: keyboard.press_and_release(_k.lower())

    @staticmethod
    def release_all():
        if Controller.last_key is not None:
            for _k in Controller.last_key:
                keyboard.release(_k)
        Controller.last_key = None

    @staticmethod
    def delay_press(syllable):
        print(syllable, end="", flush=True)
        if syllable.is_space: return
        if Controller.last_key is not None:
            for _k in Controller.last_key:
                keyboard.release(_k)

        time.sleep(HORN_MODE_INTERVAL)

        for _k in syllable.words:
            if syllable.is_arpeggio: time.sleep(ARPEGGIO_INTERVAL)
            keyboard.press(_k.lower())
        Controller.last_key = syllable.words.lower()


class Connection:
    def __init__(
            self, *,
            running_flag=True,
            stop_flag=True,
            delay_press=False,
            restart=False,
            progress_adjust_rating=1,
            adjust_interval=0,
            adjust_progress=0
    ):
        self.running_flag = running_flag
        self.stop_flag = stop_flag
        self.delay_press = delay_press
        self.adjust_interval = adjust_interval
        self.adjust_progress = adjust_progress
        self.pg_ad_rating = progress_adjust_rating
        self.restart = restart


class Syllable:
    def __init__(self, words, is_arpeggio=False):
        self.is_space = (words == " ")
        self.is_multitone = (len(words) > 1)
        self.is_rest = (words == "^")

        self.words = words
        if isinstance(words, str) and not self.is_space:
            self.words = list(words) if words.isalpha() else Syllable.analyse(words)

        self.is_arpeggio = is_arpeggio

    @staticmethod
    def analyse(word):
        pairs = {}
        stack = []
        for idx, item in enumerate(word):
            if item in QUOTE_PAIR.keys():
                stack.append(idx)
            elif item in QUOTE_PAIR.values():
                pairs[stack.pop()] = idx

        res: List[Syllable] = []
        idx = 0
        length = len(word)
        while idx < length:

            if (right := pairs.get(idx, None)) is not None:
                res.append(Syllable(word[idx + 1: right]))
                idx = right + 1
                continue
            res.append(Syllable(word[idx]))
            idx += 1
        return res

    def __str__(self):
        if self.is_space: return "_"

        word_str = ''.join(map(str, self.words))
        if self.is_arpeggio:
            return f"[{word_str}]"
        elif self.is_multitone:
            return f"({word_str})"
        else:
            return f"{word_str}"

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
        if self.current_syllable.words == " ":
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
        return self.idx / self.length

    @property
    def current_syllable(self):
        if self.idx >= self.length:
            return Syllable("!")
        return self.syllables[self.idx]

    def display_title(self):
        percent = self.percentage
        interval = self.r_interval
        os.system(
            f"title "
            f"{percent * 100:.2f}%  "
            f"{'Running' if not self.conn.stop_flag else 'Stopped'}  "
            f"[{interval:.4f}s - {1 / (interval / INTERVAL_RATING):.3f}Hz]  "
            f"APR:{self.pg_ad_rating}  "
            f"Mode:{'horn' if self.conn.delay_press else 'piano'}  "
            f"{self.current_syllable}"
        )

    def sleep(self):
        time.sleep(self.interval_)

    def restart(self):
        self.idx = 0
        self.display_music(self.idx)

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

        if self.conn.restart:
            self.restart()
            self.conn.restart = False

    def display_music(self, end):
        os.system("cls")
        display_default_info()
        print("".join(map(str, self.syllables[:end])), end="", flush=True)

    def check_stop(self):
        if not self.conn.running_flag: return True
        while self.conn.stop_flag:
            Controller.release_all()
            if not self.conn.running_flag: return True

            self.change_args()
            self.display_title()
        return False

    def play(self):
        while self.idx < self.length:

            self.change_args()
            self.display_title()
            self.sleep()

            if self.current_syllable.is_rest: Controller.release_all()
            if self.check_stop(): return

            if self.conn.delay_press:
                Controller.delay_press(self.current_syllable)
            else:
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

            elif (right_quote := QUOTE_PAIR.get(content[idx], None)) is not None:
                left_quote = idx
                while idx < length and content[idx] != right_quote: idx += 1

                syllables.append(Syllable(content[left_quote + 1:idx], is_arpeggio=bool(content[idx] != ")")))

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
            elif res_k == "i":
                self.conn.delay_press = not self.conn.delay_press
            elif res_k == "f3":
                self.conn.restart = not self.conn.restart

        self.conn.running_flag = False


def load_config():
    global ARPEGGIO_INTERVAL, INTERVAL_RATING, SPACE_INTERVAL_RATING, MUSIC_START_LINE, HORN_MODE_INTERVAL
    with open(MUSIC_PATH, 'r') as file:
        lines = file.read().split('\n')

    for idx, line in enumerate(lines):
        if line.startswith("ARPEGGIO_INTERVAL"):
            ARPEGGIO_INTERVAL = float(line.split('=')[-1])
        elif line.startswith("INTERVAL_RATING"):
            INTERVAL_RATING = float(line.split('=')[-1])

        elif line.startswith("SPACE_INTERVAL_RATING"):
            SPACE_INTERVAL_RATING = float(line.split('=')[-1])

        elif line.startswith("HORN_MODE_INTERVAL"):
            HORN_MODE_INTERVAL = float(line.split('=')[-1])

        elif line.startswith("-"):
            MUSIC_START_LINE = idx + 1


def display_default_info():
    print(
        "Press F1 to start/stop, F2 to exit, F3 to restart, \n"
        "UP to increase interval, DOWN to decrease interval, "
        "LEFT to go back, RIGHT to go forward, \n"
        "P to double progress, O to halve progress\n"
        "I to switch mode between piano and horn, "
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
    (m := Monitor(c)).start()
    music = FileAnalyzer(MUSIC_PATH, c).read_content().analyze()
    while c.running_flag:

        try:
            music.play()
            c.stop_flag = True
            music.display_title()
        finally:
            Controller.release_all()

        if c.restart: music.restart()

    m.join()


if __name__ == '__main__':
    main(sys.argv)
    # main(['', r'D:\a3432\Desktop\谱\Script\背对背拥抱 by小6.txt'])