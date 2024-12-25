from typing import Dict, Final, Set

QUOTE_PAIR: Final[
    Dict[str, str]
] = {
    '(': ')',
    '[': ']',
    '{': '}'
}

SAFE_KEYS: Final[
    Set[str]
] = {'/', ' ', '^'}
SAFE_KEYS.update({f"{chr(i)}" for i in range(65, 91)})
SAFE_KEYS.update(QUOTE_PAIR.keys())
SAFE_KEYS.update(QUOTE_PAIR.values())

REPLACE_MAP: Final[
    Dict[str, str]
] = {
    "（": "(", "）": ")",
    "【": "[", "】": "]",
    "｛": "{", "｝": "}"
}
