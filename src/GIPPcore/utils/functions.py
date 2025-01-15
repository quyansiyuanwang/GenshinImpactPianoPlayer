from typing import Any
from ..Consts import utils


def replace_all(text: str) -> str:
    for k, v in utils.REPLACE_MAP.items():
        text = text.replace(k, v)
    return text


def reverse(tar: object, prop: str) -> bool:
    if not hasattr(tar, prop): return False
    setattr(
        tar, prop,
        not getattr(tar, prop)
    )
    return True


def set_value(tar: object, prop: str, value: Any) -> None:
    setattr(tar, prop, value)


def increase_value(tar: object, prop: str, value: Any) -> bool:
    if not hasattr(tar, prop): return False
    setattr(
        tar, prop,
        getattr(tar, prop) + value
    )
    return True
