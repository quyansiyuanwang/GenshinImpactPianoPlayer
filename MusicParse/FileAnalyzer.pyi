from typing import List, Union, Self, Mapping, Literal, Optional

from .Action import Action
from .Syllable import Syllable

Syllables = List[Union[Action, Syllable]]


class FileAnalyzer:
    filename: str
    syllables: Syllables
    content: Union[List[str], None]

    def __init__(self, filename: str) -> None: ...

    def read_content(self) -> Self: ...

    @staticmethod
    def content_analyze(content: str, max_idx: int, lineno: int) -> Syllables: ...

    @staticmethod
    def dispose_action(content: str) -> Optional[Action]: ...

    def analyze(self) -> Mapping[
        Literal['syllables', 'interval'],
        'Syllables', 'float'
    ]: ...

    def __str__(self) -> str: ...
