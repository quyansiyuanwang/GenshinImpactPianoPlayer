import time
import keyboard

from MusicParse import Syllable
from Config import Config as GlobalConfig


class Controller:
    last_key = None

    @staticmethod
    def press(syllable, display=True):
        if display: print(syllable, end="", flush=True)
        if syllable.is_space: return

        last = len(syllable.words) - 1
        for idx, _k in enumerate(syllable.words):
            if isinstance(_k, Syllable):
                Controller.press(_k, display=False)
            else:
                keyboard.press_and_release(_k.lower())

            if syllable.is_arpeggio and idx != last: time.sleep(GlobalConfig.ARPEGGIO_INTERVAL)

    @staticmethod
    def release_all():
        if Controller.last_key is not None:
            for _k in Controller.last_key:
                keyboard.release(_k)
        Controller.last_key = None

    @staticmethod
    def delay_press(syllable):
        print(syllable, end="", flush=True)
        if syllable.is_space: return
        if Controller.last_key is not None:
            for _k in Controller.last_key:
                keyboard.release(_k)

        time.sleep(GlobalConfig.HORN_MODE_INTERVAL)

        for _k in syllable.words:
            if syllable.is_arpeggio: time.sleep(GlobalConfig.ARPEGGIO_INTERVAL)
            keyboard.press(_k.lower())
        Controller.last_key = ''.join(str(w).lower() for w in syllable.words)
