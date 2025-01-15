from typing import Dict, List, Union
from ..Consts import utils


class Syllable:
    def __init__(self, words: str, is_arpeggio: bool = False):
        self.is_space: bool = words == " "
        self.is_multitone: bool = len(words) > 1
        self.is_rest: bool = words == "^"

        self.words: Union[str, List[str], List[Syllable]] = words
        if not self.is_space and words != "^":
            self.words = (
                list(words) if words.isalpha() else Syllable.analyse(words)
            )

        self.is_arpeggio: bool = is_arpeggio

    @staticmethod
    def analyse(word: str) -> List['Syllable']:
        pairs: Dict[int, int] = {}
        stack: List[int] = []
        for idx, item in enumerate(word):
            if item in utils.QUOTE_PAIR.keys():
                stack.append(idx)
            elif item in utils.QUOTE_PAIR.values() and stack:
                pairs[stack.pop()] = idx

        res: List[Syllable] = []
        idx = 0
        length = len(word)
        while idx < length:

            if (right := pairs.get(idx, None)) is not None:
                res.append(Syllable(word[idx + 1 : right]))
                idx = right + 1
                continue
            res.append(Syllable(word[idx]))
            idx += 1
        return res

    def __str__(self) -> str:
        if self.is_space:
            return "_"

        word_str = "".join(map(str, self.words))
        if self.is_arpeggio:
            return f"[{word_str}]"
        elif self.is_multitone:
            return f"({word_str})"
        else:
            return f"{word_str}"

    def __repr__(self):
        return self.__str__()
