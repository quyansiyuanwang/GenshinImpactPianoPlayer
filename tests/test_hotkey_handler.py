"""Hotkey registry and dispatch tests without a global keyboard hook."""

from types import SimpleNamespace
from typing import cast

import keyboard
import pytest

from src.ui.cli.input.hotkey_handler import HotkeyHandler
from src.ui.cli.input.hotkey_registry import HotkeyRegistry


def _event(
    name: str, scan_code: int, event_type: str = "down"
) -> keyboard.KeyboardEvent:
    return cast(
        keyboard.KeyboardEvent,
        SimpleNamespace(name=name, scan_code=scan_code, event_type=event_type),
    )


def test_handler_dispatches_scan_codes_and_combinations() -> None:
    calls: list[str] = []
    handler = HotkeyHandler()
    handler.register("=", lambda: calls.append("speed"))
    handler.register("ctrl+left", lambda: calls.append("line-back"))

    handler._on_key_event(_event("=", 13))
    handler._on_key_event(_event("ctrl", 29))
    handler._on_key_event(_event("left", 75))
    handler._on_key_event(_event("ctrl", 29, "up"))

    assert calls == ["speed", "line-back"]


def test_handler_normalizes_ctrl_plus_to_ctrl_equals() -> None:
    calls: list[str] = []
    handler = HotkeyHandler()
    handler.register("ctrl+=", lambda: calls.append("speed-up-large"))

    handler._on_key_event(_event("ctrl", 29))
    handler._on_key_event(_event("+", 13))
    handler._on_key_event(_event("ctrl", 29, "up"))

    assert calls == ["speed-up-large"]


def test_handler_unhooks_only_its_own_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    hooks: list[object] = []
    unhooks: list[object] = []
    monkeypatch.setattr(keyboard, "hook", hooks.append)
    monkeypatch.setattr(keyboard, "unhook", unhooks.append)
    handler = HotkeyHandler()

    handler.start()
    handler.stop()

    assert hooks == [handler._on_key_event]
    assert unhooks == [handler._on_key_event]


def test_registry_preserves_plugin_bindings() -> None:
    registry = HotkeyRegistry()

    def callback() -> None:
        pass

    registry.register("f9", callback, "Save configuration", "plugin")

    assert registry.get_callback("f9") is callback
    assert registry.get_by_category("plugin") == [("f9", "Save configuration")]


def test_handler_swallows_callback_errors() -> None:
    calls: list[str] = []
    handler = HotkeyHandler()

    def broken() -> None:
        raise RuntimeError("callback failed")

    handler.register("f8", broken)
    handler.register("f2", lambda: calls.append("quit"))

    handler._on_key_event(_event("f8", 66))
    handler._on_key_event(_event("f2", 60))

    assert calls == ["quit"]


def test_shifted_symbol_falls_back_to_scan_code_binding() -> None:
    calls: list[str] = []
    handler = HotkeyHandler()
    handler.register("=", lambda: calls.append("speed-up"))

    # Shift+= produces the "+" key name but the same physical scan code
    handler._on_key_event(_event("shift", 42))
    handler._on_key_event(_event("+", 13))
    handler._on_key_event(_event("shift", 42, "up"))

    assert calls == ["speed-up"]


def test_ctrl_combinations_do_not_fall_back_to_scan_codes() -> None:
    calls: list[str] = []
    handler = HotkeyHandler()
    handler.register("=", lambda: calls.append("speed-up"))

    handler._on_key_event(_event("ctrl", 29))
    handler._on_key_event(_event("=", 13))
    handler._on_key_event(_event("ctrl", 29, "up"))

    assert calls == []


def test_default_hotkeys_register_documented_bindings() -> None:
    from src.cli import CLI
    from src.ui.cli.input.default_hotkeys import register_default_hotkeys
    from src.ui.cli.input.hotkey_registry import (
        _reset_for_testing,
        get_hotkey_registry,
    )

    _reset_for_testing()
    try:
        cli = CLI("score.txt")
        register_default_hotkeys(cli, get_hotkey_registry())

        registry = get_hotkey_registry()
        for key in (
            "shift+up",
            "shift+down",
            "ctrl+up",
            "ctrl+down",
            "up",
            "down",
            "page up",
            "page down",
            "home",
            "end",
            "insert",
            "delete",
            "ctrl+home",
            "ctrl+end",
            "ctrl+backspace",
            "ctrl+k",
            "ctrl+l",
            "f12",
        ):
            assert registry.get_callback(key) is not None, key
    finally:
        _reset_for_testing()
