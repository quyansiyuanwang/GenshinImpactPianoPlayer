from typing import List, TypedDict, Self, Union, Optional

from ..Consts import utils, consts
from ..Config import Config as GlobalConfig
from ..utils import replace_all
from .Syllable import Syllable
from .Action import Action

Syllables = List[Union[Syllable, Action]]


class MusicPackage(TypedDict):
    syllables: Syllables
    interval: float


class FileAnalyzer:
    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.syllables: Syllables = []
        self.content: Optional[List[str]] = None

    def read_content(self) -> Self:
        with open(self.filename, "r", encoding="utf-8-sig") as file:
            self.content = file.read().split("\n")
        return self

    @staticmethod
    def content_analyze(content: str, max_idx: int, lineno: int) -> Syllables:
        syllables: Syllables = []
        length = len(content)
        idx = 0

        def inner():
            nonlocal idx, syllables
            section = 0
            while idx < min(max_idx, length):
                if section == 4 and GlobalConfig.strict_limited:
                    while idx < min(max_idx, length) and content[idx] != "/":
                        idx += 1

                if content[idx] not in utils.SAFE_KEYS:
                    syllables.append(Syllable(" "))
                    idx += 1
                    section += 1
                    continue

                if content[idx] == "/":
                    if GlobalConfig.space_fills and section < 4:
                        for _ in range(4 - section):
                            syllables.append(Syllable(" "))
                    section = 0

                elif (
                        right_quote := utils.QUOTE_PAIR.get(content[idx], None)
                ) is not None:
                    left_quote = content[idx]
                    left_quote_idx = idx
                    quote_depth = 1
                    while (
                            idx < length
                            and content[idx] != right_quote
                            and quote_depth != 0
                    ):
                        if content[idx] == right_quote:
                            quote_depth -= 1
                        elif content[idx] == left_quote:
                            quote_depth += 1
                        idx += 1

                    syllables.append(
                        Syllable(
                            content[left_quote_idx + 1: idx],
                            is_arpeggio=bool(content[idx] != ")"),
                        )
                    )
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
            print(
                f"RI:Err({e}): cur at "
                f"(lineno={lineno + GlobalConfig.music_start_line + 1})({idx=}), "
                f"till: {content[idx:]}"
            )
            return []

        except Exception as e:
            print(
                f"OE:Err({e}), cur at "
                f"(lineno={lineno + GlobalConfig.music_start_line + 1})({idx=}), "
                f"till: {content[idx:]}"
            )
            return []

        return syllables

    @staticmethod
    def dispose_action(content: str) -> Optional[Action]:
        action = Action(cfg_str=content)
        if action.is_valid:
            return action
        return None

    def analyze(
            self,
    ) -> MusicPackage:
        if self.content is None:
            raise ValueError("Content is None, please read content first")
        syllables: Syllables = []
        config_flag = False

        interval = 1 / float(self.content[0].strip())

        for lineno, syllable in enumerate(
                self.content[GlobalConfig.music_start_line:]
        ):
            replace_content = replace_all(syllable)
            idx = len(syllable) - 1
            while idx >= 0 and syllable[idx] == " ":
                idx -= 1

            if idx >= 0 and syllable[idx].startswith("#"):
                config_flag = not config_flag
                continue

            if config_flag:
                action = FileAnalyzer.dispose_action(syllable)
                if action is not None:
                    syllables.append(action)
                    continue

            for s in FileAnalyzer.content_analyze(
                    replace_content,
                    idx if idx >= 0 and syllable[idx] == "/" else len(syllable),
                    lineno,
            ):
                syllables.append(s)

            if consts.IGNORE_BLANK_LINE and idx == -1:
                continue  # blank line

            for _ in range(
                    int(consts.DEFAULT_LINE_INTERVAL_RATING) if idx != -1 else 1
            ):
                syllables.append(Syllable(" "))

        return {"syllables": syllables, "interval": interval}

    def __str__(self) -> str:
        return f"{self.syllables}"
