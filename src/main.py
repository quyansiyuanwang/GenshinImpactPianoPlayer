import os
import sys

from GIPPcore.Config import Config as GlobalConfig
from GIPPcore.Consts import consts, FIXED_RELATIVE_PATH, EXE_PATH
from GIPPcore.utils import Monitor
from GIPPcore.Controller import Controller
from GIPPcore.Connection import Connection
from GIPPcore.MusicParse import FileAnalyzer
from GIPPcore.GenshinImpactPianoPlayer import PianoPlayer, display_default_info
from GIPPcore.ShortcutKeyManager import ShortcutKeyManager


def load_config():
    with open(GlobalConfig.MUSIC_PATH, 'r', encoding='utf8') as file:
        lines = file.read().split('\n')

    for idx, line in enumerate(lines):
        if line.startswith("ARPEGGIO_INTERVAL"):
            consts.DEFAULT_ARPEGGIO_INTERVAL = GlobalConfig.ARPEGGIO_INTERVAL = float(line.split('=')[-1])

        elif line.startswith("INTERVAL_RATING"):
            consts.DEFAULT_INTERVAL_RATING = GlobalConfig.INTERVAL_RATING = float(line.split('=')[-1])

        elif line.startswith("SPACE_INTERVAL_RATING"):
            consts.DEFAULT_SPACE_INTERVAL_RATING = GlobalConfig.SPACE_INTERVAL_RATING = float(line.split('=')[-1])

        elif line.startswith("HORN_MODE_INTERVAL"):
            consts.DEFAULT_HORN_MODE_INTERVAL = GlobalConfig.HORN_MODE_INTERVAL = float(line.split('=')[-1])

        elif line.startswith("LINE_INTERVAL_RATING"):
            consts.DEFAULT_LINE_INTERVAL_RATING = GlobalConfig.LINE_INTERVAL_RATING = int(line.split('=')[-1])

        elif line.startswith("SPACE_FILLS"):
            consts.SPACE_FILLS = (line.split('=')[-1].lower() == "true")

        elif line.startswith("IGNORE_BLANK_LINE"):
            consts.IGNORE_BLANK_LINE = (line.split('=')[-1].lower() == "true")

        elif line.startswith("STRICT_LIMITED"):
            GlobalConfig.STRICT_LIMITED = consts.STRICT_LIMITED = (line.split('=')[-1].lower() == "true")

        elif line.startswith("-"):
            GlobalConfig.MUSIC_START_LINE = idx + 1
            return None


def load_shortcut_keys():
    skm = ShortcutKeyManager()
    skm.set_default_shortcut_keys()

    print(f"Loading keyMap.ini from {EXE_PATH + FIXED_RELATIVE_PATH}")
    if not os.path.exists(EXE_PATH + FIXED_RELATIVE_PATH):
        print("keyMap.ini not found, generating...")
        skm.generate_ini()
        return skm

    skm.load_ini()
    return skm


def load_all():
    load_config()
    c = Connection()
    skm = load_shortcut_keys()
    m = Monitor(c, skm)
    m.start()
    skm.display()
    package = FileAnalyzer(GlobalConfig.MUSIC_PATH).read_content().analyze()
    music = PianoPlayer(package['syllables'], connection=c)
    GlobalConfig.PLAYER_INTERVAL = package['interval']

    return {
        'music': music,
        'connection': c,
        'monitor': m
    }


def play(music, connection):
    while connection.running_flag:
        try:
            music.play()
            connection.stop_flag = True
            music.display_title()
        finally:
            Controller.release_all()

        if connection.restart: music.restart()


def main(argv):
    os.system("mode con cols=128 lines=30")
    if len(argv) == 1:
        print("Drag the music file onto the exe to launch, or manually type the music file path")
        GlobalConfig.MUSIC_PATH = input("Please enter the music file path: ")
        while not os.path.exists(GlobalConfig.MUSIC_PATH):
            GlobalConfig.MUSIC_PATH = input("Please enter the correct music file path：")
    else:
        GlobalConfig.MUSIC_PATH = argv[1]

    hot_reload_flag = True  # for first time running
    packages = load_all()
    display_default_info()
    while hot_reload_flag:
        play(music=packages['music'], connection=packages['connection'])
        hot_reload_flag = packages['connection'].hot_reload
        if hot_reload_flag:
            # configure the vars
            cur_idx = packages['music'].idx
            packages = load_all()
            packages['music'].idx = cur_idx

            # display info
            PianoPlayer.clear()
            print(f"\n{'Hot reload!':-^50}", flush=True)
            display_default_info()
            packages['music'].display_music(cur_idx)

        else:
            packages['monitor'].join()


if __name__ == '__main__':
    main(sys.argv)
    # main(['', r'D:\a3432\Desktop\谱\Script\color-x by呵呵哒6.txt'])
