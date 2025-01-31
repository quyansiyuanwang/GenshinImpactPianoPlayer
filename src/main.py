import os
import sys
from typing import List, Union, TypedDict

from GIPPcore.Config import Config as GlobalConfig
from GIPPcore.Consts import consts, FIXED_RELATIVE_PATH, EXE_PATH
from GIPPcore.utils import Monitor
from GIPPcore.Controller import Controller
from GIPPcore.Connection import Connection
from GIPPcore.MusicParse import Action, FileAnalyzer, MusicPackage, Syllable
from GIPPcore.GenshinImpactPianoPlayer import PianoPlayer, display_default_info
from GIPPcore.ShortcutKeyManager import ShortcutKeyManager

Syllables = List[Union[Syllable, Action]]


class AllObjects(TypedDict):
    music: PianoPlayer
    connection: Connection
    monitor: Monitor


def load_config() -> None:
    with open(GlobalConfig.music_path, "r", encoding="utf8") as file:
        lines = file.read().split("\n")

    for idx, line in enumerate(lines):
        if line.upper().startswith("ARPEGGIO_INTERVAL"):
            consts.DEFAULT_ARPEGGIO_INTERVAL = GlobalConfig.arpeggio_interval = float(
                line.split("=")[-1]
            )

        elif line.upper().startswith("INTERVAL_RATING"):
            consts.DEFAULT_INTERVAL_RATING = GlobalConfig.interval_rating = float(
                line.split("=")[-1]
            )

        elif line.upper().startswith("SPACE_INTERVAL_RATING"):
            consts.DEFAULT_SPACE_INTERVAL_RATING = (
                GlobalConfig.space_interval_rating
            ) = float(line.split("=")[-1])

        elif line.upper().startswith("HORN_MODE_INTERVAL"):
            consts.DEFAULT_HORN_MODE_INTERVAL = GlobalConfig.horn_mode_interval = float(
                line.split("=")[-1]
            )

        elif line.upper().startswith("LINE_INTERVAL_RATING"):
            consts.DEFAULT_LINE_INTERVAL_RATING = GlobalConfig.line_interval_rating = (
                int(line.split("=")[-1])
            )

        elif line.upper().startswith("SPACE_FILLS"):
            GlobalConfig.space_fills = consts.SPACE_FILLS = line.split("=")[-1].lower() == "true"

        elif line.upper().startswith("IGNORE_BLANK_LINE"):
            consts.IGNORE_BLANK_LINE = line.split("=")[-1].lower() == "true"

        elif line.upper().startswith("STRICT_LIMITED"):
            GlobalConfig.strict_limited = consts.STRICT_LIMITED = (
                line.split("=")[-1].lower() == "true"
            )

        elif line.startswith("-"):
            GlobalConfig.music_start_line = idx + 1
            return None


def load_shortcut_keys() -> ShortcutKeyManager[Connection, Union[None, bool]]:
    skm: ShortcutKeyManager[Connection, Union[None, bool]] = ShortcutKeyManager()
    skm.set_default_shortcut_keys()

    print(f"Loading keyMap.ini from {EXE_PATH + FIXED_RELATIVE_PATH}")
    if not os.path.exists(EXE_PATH + FIXED_RELATIVE_PATH):
        print("keyMap.ini not found, generating...")
        skm.generate_ini()
        return skm

    skm.load_ini()
    return skm


def load_all() -> AllObjects:
    load_config()
    c = Connection()
    skm: ShortcutKeyManager[Connection, Union[None, bool]] = load_shortcut_keys()
    m = Monitor(conn=c, shortcut_key_manager=skm)
    m.start()
    skm.display()
    package: MusicPackage = (
        FileAnalyzer(filename=GlobalConfig.music_path).read_content().analyze()
    )
    music = PianoPlayer(syllables=package["syllables"], connection=c)
    GlobalConfig.player_interval = package["interval"]

    return {"music": music, "connection": c, "monitor": m}


def play(music: PianoPlayer, connection: Connection) -> None:
    while connection.running_flag:
        try:
            music.play()
            connection.stop_flag = True
            music.display_title()
        finally:
            Controller.release_all()

        if connection.restart:
            music.restart()


def main(argv: List[str]):
    if len(argv) == 1:
        print(
            "Drag the music file onto the exe to launch, or manually type the music file path"
        )
        GlobalConfig.music_path = input("Please enter the music file path: ")
        while not os.path.exists(GlobalConfig.music_path):
            GlobalConfig.music_path = input(
                "Please enter the correct music file path: "
            )
    else:
        GlobalConfig.music_path = argv[1]

    hot_reload_flag = True  # for first time running
    packages: AllObjects = load_all()
    display_default_info()
    while hot_reload_flag:
        play(music=packages["music"], connection=packages["connection"])
        hot_reload_flag = packages["connection"].hot_reload
        if hot_reload_flag:
            # configure the vars
            cur_idx = packages["music"].idx
            packages = load_all()
            packages["music"].idx = cur_idx

            # display info
            PianoPlayer.clear()
            print(f"\n{'Hot reload!':-^50}", flush=True)
            display_default_info()
            packages["music"].display_music(cur_idx)

        else:
            packages["monitor"].join()


if __name__ == "__main__":
    main(sys.argv)
