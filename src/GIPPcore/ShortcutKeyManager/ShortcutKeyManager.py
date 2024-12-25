import os

from ..Consts import FIXED_RELATIVE_PATH, EXE_PATH, DEFAULT_DESCRIPTION_KEY_MAP
from ..Consts import DEFAULT_DESCRIPTION_LAMBDA_MAP


class ShortcutKey:
    def __init__(self, key, description, func):
        self.key = key
        self.description = description
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class ShortcutKeyManager:
    def __init__(self):
        self.keys_list = list()

    def get_by_key(self, key):
        for shortcut_key in self.keys_list:
            if shortcut_key.key == key:
                return shortcut_key

    def get_by_description(self, description):
        for shortcut_key in self.keys_list:
            if shortcut_key.description == description:
                return shortcut_key

    def set_func(self, key, description, func):
        search_res = self.get_by_key(key)
        if search_res is None:
            self.keys_list.append(ShortcutKey(key, description, func))
        else:
            search_res.func = func

    def set_default_shortcut_keys(self):
        for description, key in DEFAULT_DESCRIPTION_KEY_MAP.items():
            self.set_key_by_description(description, key)

    def set_key_by_description(self, description, key):
        shortcut_key = self.get_by_description(description)
        if shortcut_key is not None:
            shortcut_key.key = key
        else:
            rep = DEFAULT_DESCRIPTION_LAMBDA_MAP.get(description)
            if rep is not None:
                self.set_func(key, description, rep)
            else:
                print(f'No such key description: {description}, Please Check your keyMap.ini')
                os.system('pause')
                assert False, 'No such key description'

    def generate_ini(self):
        if not os.path.exists(EXE_PATH + FIXED_RELATIVE_PATH):
            os.makedirs(os.path.dirname(EXE_PATH + FIXED_RELATIVE_PATH), exist_ok=True)
        with open(EXE_PATH + FIXED_RELATIVE_PATH, 'w', encoding='utf8') as file:
            for shortcut_key in self.keys_list:
                file.write(f'{shortcut_key.description}={shortcut_key.key}\n')

    def load_ini(self):
        with open(EXE_PATH + FIXED_RELATIVE_PATH, 'r', encoding='utf8') as file:
            lines = file.read().split('\n')
        for line in lines:
            if not line: continue
            description, key = line.split('=')
            self.set_key_by_description(description, key)

    def display(self):
        print('Shortcuts:')
        for shortcut_key in self.keys_list:
            print(f'{shortcut_key.description} : {shortcut_key.key}')
        print("-" * 50)

    def modify_shortcut_key(self):
        print()
        for idx, shortcut_key in enumerate(self.keys_list):
            print(f'{idx + 1}. {shortcut_key.description} : {shortcut_key.key}')
        print("-" * 50)
        idx = int(input('Please enter the index of the shortcut you want to modify: ')) - 1
        new_key = input('Please enter the new key: ')
        self.keys_list[idx].key = new_key
