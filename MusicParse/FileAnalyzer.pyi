from typing import List, Union, Self, Mapping, Literal
from .Syllable import Syllable

Syllables = List[Syllable]


class FileAnalyzer:
    filename: str
    syllables: List[Syllable]
    content: Union[List[str], None]

    def __init__(self, filename: str) -> None: ...

    def read_content(self) -> Self: ...

    @staticmethod
    def content_analyze(content: str, max_idx: int ,lineno: int) -> Syllables: ...

    def analyze(self) -> Mapping[
        Literal['syllables', 'interval'],
        'Syllables', 'float'
    ]: ...

    def __str__(self) -> str: ...
