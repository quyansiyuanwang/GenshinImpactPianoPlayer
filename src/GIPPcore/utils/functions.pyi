from typing import Any, Union

Digit = Union[int, float]


def replace_all(text: str) -> str: ...


def reverse(tar: Any, prop: str) -> bool: ...


def set_value(tar: Any, prop: str, value: Any) -> None: ...


def increase_value(tar: Any, prop: str, value: Digit) -> bool: ...
