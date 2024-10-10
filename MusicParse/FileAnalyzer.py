from Consts import consts, utils
from Config import Config as GlobalConfig
from MusicParse import Syllable
from utils import replace_all


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
    def content_analyze(content, max_idx, lineno):
        syllables = []
        length = len(content)
        idx = 0

        def inner():
            nonlocal idx, syllables
            section = 0
            while idx < min(max_idx, length):
                if content[idx] not in utils.SAFE_KEYS:
                    syllables.append(Syllable(" "))
                    idx += 1
                    section += 1
                    continue

                if content[idx] == "/":
                    if consts.SPACE_FILLS and section < 4:
                        for _ in range(4 - section): syllables.append(Syllable(" "))
                    section = 0

                elif (right_quote := utils.QUOTE_PAIR.get(content[idx], None)) is not None:
                    left_quote = idx
                    while idx < length and content[idx] != right_quote: idx += 1

                    syllables.append(Syllable(content[left_quote + 1:idx], is_arpeggio=bool(content[idx] != ")")))
                    section += 1

                elif content[idx].isalpha() or content[idx] == " ":
                    syllables.append(Syllable(content[idx]))
                    section += 1

                elif content[idx] in utils.QUOTE_PAIR.values():
                    pass

                else:
                    syllables.append(Syllable(content[idx]))
                    section += 1

                idx += 1


        try:
            inner()
        except (RecursionError, IndexError) as e:
            print(f"Err({e}): cur at ({lineno=})({idx=}), till: {content[idx:]}")
            return []

        except Exception as e:
            print(f"Err({e}), cur at ({lineno=})({idx=}), till: {content[idx:]}")
            return []

        return syllables

    def analyze(self):
        syllables = []

        interval = 1 / float(''.join(i for i in self.content[0] if i.isdigit() or i == '.'))

        for lineno, syllable in enumerate(self.content[GlobalConfig.MUSIC_START_LINE:]):
            replace_content = replace_all(syllable)
            idx = len(syllable) - 1
            while idx >= 0 and syllable[idx] == ' ': idx -= 1

            for s in FileAnalyzer.content_analyze(
                    replace_content,
                    idx if idx >= 0 and syllable[idx] == '/' else len(syllable),
                    lineno
            ):
                syllables.append(s)

            if consts.IGNORE_BLANK_LINE and idx == -1: continue  # blank line

            for _ in range(int(consts.DEFAULT_LINE_INTERVAL_RATING) if idx != -1 else 1):
                syllables.append(Syllable(" "))

        return {'syllables': syllables, 'interval': interval}

    def __str__(self):
        return f"{self.syllables}"
