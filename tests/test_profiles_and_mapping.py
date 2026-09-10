"""Tests for persistent profiles, input locking, and score mappings."""

from types import SimpleNamespace
from pathlib import Path
from typing import cast

import keyboard

from src.application.config.profiles import ProfileStore
from src.core.player.player import Player
from src.ui.cli.input.hotkey_handler import HotkeyHandler
from tests.conftest import FakeKeyboard, make_score


def test_profile_store_round_trips_independent_profiles(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profiles.json")
    store.add_hotkey_profile("compact", {"play_pause": "f6"})
    store.add_mapping_profile("practice", {"a": "j"})
    store.select_hotkeys("compact")
    store.select_mapping("practice")
    store.save()

    loaded = ProfileStore(tmp_path / "profiles.json")
    assert loaded.active_hotkeys()["play_pause"] == "f6"
    assert loaded.active_mapping() == {"A": "J"}
    loaded.rename_hotkey_profile("compact", "renamed")
    loaded.rename_mapping_profile("practice", "renamed-map")
    loaded.delete_hotkey_profile("renamed")
    loaded.delete_mapping_profile("renamed-map")
    assert list(loaded.hotkey_profiles()) == ["default"]
    assert list(loaded.mapping_profiles()) == ["default"]


def test_player_maps_single_and_deduplicates_chord_output() -> None:
    keyboard_controller = FakeKeyboard()
    player = Player(make_score([["A"]]), keyboard_controller, {"a": "j"})
    player._playback_loop()
    assert keyboard_controller.operations == [("tap", ("J",))]


def test_symbol_mapping_round_trips_with_scan_metadata(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profiles.json")
    store.data["mapping_profiles"] = {"default": {"A": ","}}
    store.data["mapping_scan_profiles"] = {
        "default": {"A": {"source_scan_code": 30, "target_scan_code": 51}}
    }
    store.save()
    loaded = ProfileStore(tmp_path / "profiles.json")
    assert loaded.active_mapping() == {"A": ","}
    assert loaded.mapping_scans()["A"]["target_scan_code"] == 51


def test_player_prefers_target_scan_code_when_available() -> None:
    class ScanKeyboard(FakeKeyboard):
        def tap_scan_code(self, scan_code: int) -> None:
            self._record("tap_scan", [str(scan_code)])

    scan_keyboard = ScanKeyboard()
    player = Player(
        make_score([["A"]]),
        scan_keyboard,
        {"A": ","},
        {"A": {"target_scan_code": 51}},
    )
    player._playback_loop()
    assert scan_keyboard.operations == [("tap_scan", ("51",))]

    keyboard_controller = FakeKeyboard()
    player = Player(make_score([["A", "Q"]]), keyboard_controller, {"a": "j", "q": "j"})
    player._play_keys(["A", "Q"], 0)
    assert keyboard_controller.operations == [("tap", ("J",))]


def test_locked_handler_allows_only_unlock_binding() -> None:
    calls: list[str] = []
    handler = HotkeyHandler()
    handler.register("f8", lambda: calls.append("play"))
    handler.register("f12", lambda: calls.append("unlock"))
    handler.set_locked(True, "f12")

    def event(name: str, scan_code: int) -> keyboard.KeyboardEvent:
        return cast(
            keyboard.KeyboardEvent,
            SimpleNamespace(name=name, scan_code=scan_code, event_type="down"),
        )

    handler._on_key_event(event("f8", 66))
    handler._on_key_event(event("f12", 88))
    assert calls == ["unlock"]
