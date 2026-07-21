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
