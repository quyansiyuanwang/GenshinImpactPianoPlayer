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
    def press(key, is_arpeggio=False):

        if key == " ":
            print("_", end="", flush=True)
            return

        if len(key) > 1:
            key_str = f'({key})' if not is_arpeggio else f'[{key}]'
        else:
            key_str = key

        print(key_str, end="", flush=True)
        for _k in key:
            if is_arpeggio: time.sleep(ARPEGGIO_INTERVAL)
            keyboard.press_and_release(_k.lower())


class Flag:
    def __init__(self):
        self.running_flag = True
        self.stop_flag = False
        self.adjust_interval = 0


class Syllable:
    def __init__(self, word, is_arpeggio=False):
        self.word = word
        self.is_arpeggio = is_arpeggio

    def __str__(self):
        return f"'{self.word}'"

    def __repr__(self):
        return f"'{self.word}'"


class PianoPlayer:
    def __init__(self):
        self.syllables = []
        self.interval = 0.5

    def add_syllables(self, syllables):
        for syllable in syllables:
            self.syllables.append(syllable)
        return self

    def play(self, flag):
        interval = self.interval * INTERVAL_RATING
        total_time = len(self.syllables) * interval
        length = len(self.syllables)

        for idx, syllable in enumerate(self.syllables):
            if syllable.word == " ":
                time.sleep(interval * SPACE_INTERVAL_RATING)
            else:
                time.sleep(interval)
            if flag.adjust_interval:
                interval += flag.adjust_interval
                flag.adjust_interval = 0

            if not flag.running_flag: return

            while flag.stop_flag:
                if not flag.running_flag: return
                os.system("title stopping")

            Controller.press(syllable.word, is_arpeggio=syllable.is_arpeggio)

            percent = (idx + 1) / length
            os.system(
                f"title "
                f"{percent * 100:.2f}%"
                f"({total_time * percent:.2f}/ {total_time:.2f}s)"
                f"ITV[{interval:.4f}s - {1 / (interval / INTERVAL_RATING):.3f}Hz]"
            )

    def __str__(self):
        syllables = ".".join([str(syllable) for syllable in self.syllables])
        return f"U{self.interval}\n{syllables}"


class FileAnalyzer:
    def __init__(self, filename):
        self.filename = filename
        self.syllables = []
        self.content = None

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
                idx += 1
                continue

            elif content[idx] in ["(", "[", "{"]:
                left_quote = idx
                while idx < length and content[idx] not in [")", "]", "}"]: idx += 1
                syllables.append(Syllable(
                    content[left_quote + 1:idx],
                    is_arpeggio=bool(content[idx] != ")")
                ))

            else:
                syllables.append(Syllable(content[idx].replace(u"\xa0", " ")))

            idx += 1

        return syllables

    def analyze(self):
        song_player = PianoPlayer()
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
    def __init__(self, flag):
        super().__init__()
        self.flag = flag

    def run(self):
        while (res_k := user_enter_monitor()) != "f2":
            if res_k == "f1": self.flag.stop_flag = not self.flag.stop_flag
            if res_k == "up": self.flag.adjust_interval += 0.005
            if res_k == "down": self.flag.adjust_interval -= 0.005
        self.flag.running_flag = False


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


def main(argv):
    global MUSIC_PATH
    MUSIC_PATH = argv[1]
    load_config()

    print("Press F1 to start/stop, F2 to exit, UP to increase interval, DOWN to decrease interval")
    print(f"Play the song of `{MUSIC_PATH}`")
    print(
        f"arpeggio_interval: {ARPEGGIO_INTERVAL}"
        f", interval_rating: {INTERVAL_RATING}"
        f", space_interval_rating: {SPACE_INTERVAL_RATING}"
    )

    f = Flag()
    while f.running_flag:
        if user_enter_monitor() == "f1":
            m = Monitor(f)
            m.start()
            FileAnalyzer(MUSIC_PATH).read_content().analyze().play(f)
            m.join()


if __name__ == '__main__':
    main(sys.argv)
