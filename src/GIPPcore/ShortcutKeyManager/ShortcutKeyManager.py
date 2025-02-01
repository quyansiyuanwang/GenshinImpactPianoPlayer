import os
import time
from typing import Callable, Optional, TypeVar, Generic, List

from ..Consts import FIXED_RELATIVE_PATH, EXE_PATH, DEFAULT_DESCRIPTION_KEY_MAP
from ..Consts import DEFAULT_DESCRIPTION_LAMBDA_MAP

T = TypeVar("T")
RT = TypeVar("RT")


class ShortcutKey(Generic[T, RT]):
    def __init__(self, key: str, description: str, func: Callable[[T], RT]) -> None:
        self.key: str = key
        self.description: str = description.split("*")[-1]
        self.func: Callable[[T], RT] = func
        self.is_always_active: bool = True if description.startswith("*") else False

    def __call__(self, *args: T, **kwargs: T) -> RT:
        return self.func(*args, **kwargs)


class ShortcutKeyManager(Generic[T, RT]):
    def __init__(self):
        self.keys_list: List[ShortcutKey[T, RT]] = list()

    def get_by_key(self, key: str) -> Optional[ShortcutKey[T, RT]]:
        for shortcut_key in self.keys_list:
            if shortcut_key.key == key:
                return shortcut_key

    def get_by_description(self, description: str) -> Optional[ShortcutKey[T, RT]]:
        description = description.split("*")[-1]
        for shortcut_key in self.keys_list:
            if shortcut_key.description == description:
                return shortcut_key

    def set_func(self, key: str, description: str, func: Callable[[T], RT]):
        search_res = self.get_by_key(key)
        if search_res is None:
            self.keys_list.append(ShortcutKey(key, description, func))
        else:
            search_res.func = func

    def set_default_shortcut_keys(self):
        for description, key in DEFAULT_DESCRIPTION_KEY_MAP.items():
            self.set_key_by_description(description, key)

    def set_key_by_description(self, description: str, key: str) -> None:
        shortcut_key = self.get_by_description(description)
        if shortcut_key is not None:
            shortcut_key.key = key
            shortcut_key.is_always_active = True if description.startswith("*") else False
            return None
        rep: Optional[Callable[[T], RT]] = DEFAULT_DESCRIPTION_LAMBDA_MAP.get(description)  # type: ignore[dict-item]
        if rep is not None:
            self.set_func(key, description, rep)
        else:
            print(
                f"No such key description: {description}, Please Check your keyMap.ini"
            )
            os.system("pause")
            assert False, "No such key description"

    def generate_ini(self) -> None:
        if not os.path.exists(EXE_PATH + FIXED_RELATIVE_PATH):
            os.makedirs(os.path.dirname(EXE_PATH + FIXED_RELATIVE_PATH), exist_ok=True)
        with open(EXE_PATH + FIXED_RELATIVE_PATH, "w", encoding="utf8") as file:
            for shortcut_key in self.keys_list:
                file.write(
                    f"{'*' if shortcut_key.is_always_active else ''}{shortcut_key.description}={shortcut_key.key}\n"
                )

    def load_ini(self) -> None:
        with open(EXE_PATH + FIXED_RELATIVE_PATH, "r", encoding="utf8") as file:
            lines = file.read().split("\n")
        for line in lines:
            if not line:
                continue
            description, key = line.split("=")
            self.set_key_by_description(description, key)

    def display(self) -> None:
        print("Shortcuts:")
        string = ""
        for i, shortcut_key in enumerate(self.keys_list, 1):
            new = f"{shortcut_key.description} : {shortcut_key.key}"
            string += new
            if i % 2 == 0:
                string += "\n"
            else:
                string += " " * (30 - len(new))
        print(string)
        print("-" * 50)

    def modify_shortcut_key(self) -> None:
        for idx, shortcut_key in enumerate(self.keys_list):
            print(f"{idx + 1}. {shortcut_key.description} : {shortcut_key.key}")
        print("-" * 50)
        time.sleep(0.3)
        try:
            idx = (
                    int(input(
                        "Please enter the index of the shortcut you want to modify(empty for exit): "
                    )) - 1
            )
            new_key = input("Please enter the new key: ")
        except ValueError:
            print("Exited editing")
            return None
        self.keys_list[idx].key = new_key
