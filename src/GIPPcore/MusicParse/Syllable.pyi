from typing import Union, List


class Syllable:
    words: Union[str, List[Syllable]]
    is_arpeggio: bool
    is_space: bool
    is_multitone: bool
    is_rest: bool

    def __init__(self, word: Union[str, List[Syllable]], is_arpeggio: bool = False) -> None: ...

    @staticmethod
    def analyse(word: str) -> List[Syllable]: ...

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...
