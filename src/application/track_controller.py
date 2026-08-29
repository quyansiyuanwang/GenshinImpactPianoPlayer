"""Load playlist entries into the existing Player runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.keyboard.controller import KeyboardController
from src.core.parser.score_parser import ScoreParser
from src.core.player.player import Player


class TrackController:
    def __init__(self, host: Any) -> None:
        self.host = host

    def load(self, path: Path) -> tuple[bool, str]:
        host = self.host
        old_player = host.player
        try:
            if old_player:
                old_player.stop()
            with path.open("r", encoding="utf-8-sig") as stream:
                host.original_content = stream.read()
            score = ScoreParser(str(path)).parse()
            player = Player(score, KeyboardController(), host.key_mapping)
            player.set_progress_callback(host._on_progress)
            host.score = score
            host.player = player
            host.file_path = str(path)
            host._reinitialize_plugins()
            return True, f"Loaded {path.name}"
        except Exception as error:
            if old_player:
                host.player = old_player
            return False, f"Load failed: {error}"
