import os
import sys
import time
from threading import Thread

import keyboard

QUOTE_PAIR = {
    '(': ')',
    '[': ']',
    '{': '}'
}

SAFE_KEYS = {'/', ' ', '^'}
SAFE_KEYS.update({f"{chr(i)}" for i in range(65, 91)})
SAFE_KEYS.update(QUOTE_PAIR.keys())
SAFE_KEYS.update(QUOTE_PAIR.values())

replace_map = {
    "（": "(", "）": ")",
    "【": "[", "】": "]",
    "｛": "{", "｝": "}"
}

DEFAULT_ARPEGGIO_INTERVAL = ARPEGGIO_INTERVAL = 0.05
DEFAULT_INTERVAL_RATING = INTERVAL_RATING = 0.15
DEFAULT_SPACE_INTERVAL_RATING = SPACE_INTERVAL_RATING = 0.5
DEFAULT_HORN_MODE_INTERVAL = HORN_MODE_INTERVAL = 0.01
DEFAULT_LINE_INTERVAL_RATING = LINE_INTERVAL_RATING = 1

SPACE_FILLS = True
IGNORE_BLANK_LINE = True
MUSIC_START_LINE = 1
MUSIC_PATH = "music.txt"


class Controller:
    last_key = None

    @staticmethod
    def press(syllable, display=True):
        if display: print(syllable, end="", flush=True)
        if syllable.is_space: return

        last = len(syllable.words) - 1
        for idx, _k in enumerate(syllable.words):
            if isinstance(_k, Syllable):
                Controller.press(_k, display=False)
            else:
                keyboard.press_and_release(_k.lower())

            if syllable.is_arpeggio and idx != last: time.sleep(ARPEGGIO_INTERVAL)

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
        Controller.last_key = ''.join(str(w).lower() for w in syllable.words)


class Connection:
    def __init__(
            self, *,
            running_flag=True,
            stop_flag=True,
            delay_press=False,
            restart=False,
            reset_config=False,
            hot_reload=False,
            progress_adjust_rating=1,
            adjust_interval=0,
            adjust_space_interval=0,
            adjust_progress=0
    ):
        self.running_flag = running_flag
        self.stop_flag = stop_flag
        self.delay_press = delay_press
        self.adjust_interval = adjust_interval
        self.adjust_space_interval = adjust_space_interval
        self.adjust_progress = adjust_progress
        self.pg_ad_rating = progress_adjust_rating
        self.restart = restart
        self.reset_config = reset_config
        self.hot_reload = hot_reload


class Syllable:
    def __init__(self, words, is_arpeggio=False):
        self.is_space = (words == " ")
        self.is_multitone = (len(words) > 1)
        self.is_rest = (words == "^")

        self.words = words
        if isinstance(words, str) and not self.is_space and words != "^":
            self.words = list(words) if words.isalpha() else Syllable.analyse(words)

        self.is_arpeggio = is_arpeggio

    @staticmethod
    def analyse(word):
        pairs = {}
        stack = []
        for idx, item in enumerate(word):
            if item in QUOTE_PAIR.keys():
                stack.append(idx)
            elif item in QUOTE_PAIR.values() and stack:
                pairs[stack.pop()] = idx

        res = []
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
            return Syllable(" ")
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
            f"SI:{SPACE_INTERVAL_RATING:.2f}  "
            f"{self.current_syllable}"
        )

    def sleep(self):
        time.sleep(self.interval_)

    def config_reset(self):
        global ARPEGGIO_INTERVAL, INTERVAL_RATING, SPACE_INTERVAL_RATING, HORN_MODE_INTERVAL
        self.interval_changes = 0
        self.pg_ad_rating = 1
        INTERVAL_RATING = DEFAULT_INTERVAL_RATING
        SPACE_INTERVAL_RATING = DEFAULT_SPACE_INTERVAL_RATING
        ARPEGGIO_INTERVAL = DEFAULT_ARPEGGIO_INTERVAL
        HORN_MODE_INTERVAL = DEFAULT_HORN_MODE_INTERVAL

    def restart(self):
        self.idx = 0
        self.display_music(self.idx)

    def change_args(self):
        global SPACE_INTERVAL_RATING
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

        if self.conn.adjust_space_interval:
            SPACE_INTERVAL_RATING += self.conn.adjust_space_interval
            self.conn.adjust_space_interval = 0

        if self.conn.reset_config:
            self.config_reset()
            self.conn.reset_config = not self.conn.reset_config

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
    def content_analyze(content, lineno):
        syllables = []
        length = len(content)
        idx = 0

        def inner():
            nonlocal idx, syllables
            section = 0
            while idx < length:
                if content[idx] not in SAFE_KEYS:
                    syllables.append(Syllable(" "))
                    idx += 1
                    section += 1
                    continue

                if content[idx] == "/":
                    if SPACE_FILLS and section < 4:
                        for _ in range(4 - section): syllables.append(Syllable(" "))
                    section = 0

                elif (right_quote := QUOTE_PAIR.get(content[idx], None)) is not None:
                    left_quote = idx
                    while idx < length and content[idx] != right_quote: idx += 1

                    syllables.append(Syllable(content[left_quote + 1:idx], is_arpeggio=bool(content[idx] != ")")))

                elif content[idx].isalpha() or content[idx] == " ":
                    syllables.append(Syllable(content[idx]))

                elif content[idx] in QUOTE_PAIR.values():
                    pass

                else:
                    syllables.append(Syllable(content[idx]))

                idx += 1
                section += 1

        try:
            inner()
        except (RecursionError, IndexError) as e:
            print(f"\033[31mErr({e}): cur at ({lineno=})({idx=}), till: {content[idx:]}\033[0m")
            return []

        except Exception as e:
            print(f"\033[31mErr({e}), cur at {idx}, till: {content[idx:]}\033[0m")
            return []

        return syllables

    def analyze(self):
        song_player = PianoPlayer(self.conn)
        song_player.interval = 1 / float(''.join(i for i in self.content[0] if i.isdigit() or i == '.'))

        for lineno, syllable in enumerate(self.content[MUSIC_START_LINE:]):
            song_player.add_syllables(FileAnalyzer.content_analyze(
                replace_all(syllable),
                lineno
            ))

            idx = len(syllable) - 1
            while idx >= 0 and syllable[idx] == ' ' and IGNORE_BLANK_LINE: idx -= 1
            if idx >= 0 and syllable[idx] == '/': continue

            for _ in range(int(LINE_INTERVAL_RATING) if idx >= 0 else 0):
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
        while self.conn.running_flag:
            res_k = user_enter_monitor()
            if res_k == "f1":
                self.conn.stop_flag = not self.conn.stop_flag
            elif res_k == "f2":
                self.conn.running_flag = False
            elif res_k == "f3":
                self.conn.restart = not self.conn.restart
            elif res_k == "f4":
                self.conn.reset_config = not self.conn.reset_config
            elif res_k == "f5":
                self.conn.hot_reload = not self.conn.hot_reload
                self.conn.running_flag = False
                break
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
            elif res_k == "k":
                self.conn.adjust_space_interval -= 0.02
            elif res_k == "l":
                self.conn.adjust_space_interval += 0.02

        self.conn.running_flag = False


def replace_all(text):
    for k, v in replace_map.items():
        text = text.replace(k, v)
    return text


def load_config():
    global ARPEGGIO_INTERVAL, INTERVAL_RATING, SPACE_INTERVAL_RATING, \
        HORN_MODE_INTERVAL, LINE_INTERVAL_RATING
    global DEFAULT_ARPEGGIO_INTERVAL, DEFAULT_INTERVAL_RATING, DEFAULT_SPACE_INTERVAL_RATING, \
        DEFAULT_HORN_MODE_INTERVAL, DEFAULT_LINE_INTERVAL_RATING
    global SPACE_FILLS, MUSIC_START_LINE, IGNORE_BLANK_LINE

    with open(MUSIC_PATH, 'r', encoding='utf8') as file:
        lines = file.read().split('\n')

    for idx, line in enumerate(lines):
        if line.startswith("ARPEGGIO_INTERVAL"):
            DEFAULT_ARPEGGIO_INTERVAL = ARPEGGIO_INTERVAL = float(line.split('=')[-1])
        elif line.startswith("INTERVAL_RATING"):
            DEFAULT_INTERVAL_RATING = INTERVAL_RATING = float(line.split('=')[-1])

        elif line.startswith("SPACE_INTERVAL_RATING"):
            DEFAULT_SPACE_INTERVAL_RATING = SPACE_INTERVAL_RATING = float(line.split('=')[-1])

        elif line.startswith("HORN_MODE_INTERVAL"):
            DEFAULT_HORN_MODE_INTERVAL = HORN_MODE_INTERVAL = float(line.split('=')[-1])

        elif line.startswith("SPACE_FILLS"):
            SPACE_FILLS = (line.split('=')[-1].lower() == "true")

        elif line.startswith("LINE_INTERVAL_RATING"):
            DEFAULT_LINE_INTERVAL_RATING = LINE_INTERVAL_RATING = int(line.split('=')[-1])

        elif line.startswith("IGNORE_BLANK_LINE"):
            IGNORE_BLANK_LINE = (line.split('=')[-1].lower() == "true")

        elif line.startswith("-"):
            MUSIC_START_LINE = idx + 1


def display_default_info():
    print(
        "Press F1 to start/stop, F2 to exit, F3 to restart, F4 to reset config, F5 to hotreload music\n"
        "UP to increase interval, DOWN to decrease interval, "
        "LEFT to go back, RIGHT to go forward, \n"
        "P to double progress, O to halve progress, \n"
        "I to switch mode between piano and horn, \n"
        "K to increase space interval, L to decrease space interval"
    )
    print(f"Play the song of `{MUSIC_PATH}`")
    print(
        f"arpeggio_interval: {ARPEGGIO_INTERVAL}"
        f", interval_rating: {INTERVAL_RATING}"
        f", space_interval_rating: {SPACE_INTERVAL_RATING}"
        f", horn_mode_interval: {HORN_MODE_INTERVAL}"
        f", line_interval_rating: {LINE_INTERVAL_RATING}"
    )


def load_all():
    load_config()
    display_default_info()
    c = Connection()
    (m := Monitor(c)).start()
    music = FileAnalyzer(MUSIC_PATH, c).read_content().analyze()

    return {
        'music': music,
        'connection': c,
        'monitor': m
    }


def play(music, connection):
    while connection.running_flag:
        try:
            music.play()
            connection.stop_flag = True
            music.display_title()
        finally:
            Controller.release_all()

        if connection.restart: music.restart()


def main(argv):
    global MUSIC_PATH
    if len(argv) == 1:
        print("拖动音乐文件到exe上以启动，或者手动键入音乐文件路径")
        while not os.path.exists(MUSIC_PATH := input("请输入音乐文件路径：")): print("请键入合法的路径！")
    else:
        MUSIC_PATH = argv[1]

    hot_reload_flag = True  # for first time running
    packages = load_all()
    while hot_reload_flag:
        play(music=packages['music'], connection=packages['connection'])
        hot_reload_flag = packages['connection'].hot_reload
        if hot_reload_flag:
            os.system("cls")
            cur_idx = packages['music'].idx
            packages = load_all()
            packages['music'].idx = cur_idx
            packages['music'].display_music(cur_idx)
            print(f"\n{'Hot reload success!':-^50}", flush=True)

        else:
            packages['monitor'].join()


if __name__ == '__main__':
    main(sys.argv)
    # main(['', r'D:\a3432\Desktop\谱\Script\temp.txt'])
