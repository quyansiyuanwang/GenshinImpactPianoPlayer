from typing import Union

from MusicParse import Syllable


class Controller:
    last_key: Union[str, None]

    @staticmethod
    def press(syllable: Syllable, display: bool = True) -> None: ...

    @staticmethod
    def release_all() -> None: ...

    @staticmethod
    def delay_press(syllable: Syllable) -> None: ...
