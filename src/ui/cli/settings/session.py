"""Transactional settings editing model.

The UI edits this object only.  A successful save commits the complete
snapshot to ``ProfileStore``; cancelling simply discards the snapshot.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping

from src.application.config.profiles import ProfileStore
from src.ui.cli.input.key_binding import KeyBinding


class SettingsSession:
    """Own a temporary, validated copy of hotkey and mapping profiles."""

    def __init__(self, store: ProfileStore, reserved_bindings: set[str] | None = None) -> None:
        self.store = store
        self.data: dict[str, object] = copy.deepcopy(store.data)
        self.reserved_bindings = {value.lower() for value in (reserved_bindings or set())}
        self.dirty = False
        self.error = ""

    @property
    def hotkeys(self) -> dict[str, dict[str, str]]:
        return self.data["hotkey_profiles"]  # type: ignore[return-value]

    @property
    def mappings(self) -> dict[str, dict[str, str]]:
        return self.data["mapping_profiles"]  # type: ignore[return-value]

    @property
    def active_hotkey_profile(self) -> str:
        return str(self.data["active_hotkey_profile"])

    @property
    def active_mapping_profile(self) -> str:
        return str(self.data["active_mapping_profile"])

    @property
    def active_hotkeys(self) -> dict[str, str]:
        return self.hotkeys[self.active_hotkey_profile]

    @property
    def active_mapping(self) -> dict[str, str]:
        return self.mappings[self.active_mapping_profile]

    @property
    def hotkey_actions(self) -> list[str]:
        return list(self.active_hotkeys)

    @property
    def mapping_items(self) -> list[tuple[str, str]]:
        return list(self.active_mapping.items())

    def _changed(self) -> None:
        self.dirty = True
        self.error = ""

    def select_hotkey_profile(self, name: str) -> None:
        if name not in self.hotkeys:
            raise KeyError(name)
        self.data["active_hotkey_profile"] = name
        self._changed()

    def select_mapping_profile(self, name: str) -> None:
        if name not in self.mappings:
            raise KeyError(name)
        self.data["active_mapping_profile"] = name
        self._changed()

    def add_hotkey_profile(self, name: str) -> None:
        name = name.strip()
        if not name or name in self.hotkeys:
            raise ValueError("profile name is empty or already exists")
        self.hotkeys[name] = self.active_hotkeys.copy()
        self.data["active_hotkey_profile"] = name
        self._changed()

    def add_mapping_profile(self, name: str) -> None:
        name = name.strip()
        if not name or name in self.mappings:
            raise ValueError("profile name is empty or already exists")
        self.mappings[name] = self.active_mapping.copy()
        self.data["active_mapping_profile"] = name
        self._changed()

    def rename_hotkey_profile(self, name: str) -> None:
        self._rename(self.hotkeys, self.active_hotkey_profile, name)
        self.data["active_hotkey_profile"] = name.strip()
        self._changed()

    def rename_mapping_profile(self, name: str) -> None:
        self._rename(self.mappings, self.active_mapping_profile, name)
        self.data["active_mapping_profile"] = name.strip()
        self._changed()

    @staticmethod
    def _rename(profiles: dict[str, dict[str, str]], old: str, new: str) -> None:
        new = new.strip()
        if not new or (new != old and new in profiles):
            raise ValueError("invalid profile rename")
        profiles[new] = profiles.pop(old)

    def delete_hotkey_profile(self) -> None:
        self._delete(self.hotkeys, self.active_hotkey_profile)
        self.data["active_hotkey_profile"] = "default"
        self._changed()

    def delete_mapping_profile(self) -> None:
        self._delete(self.mappings, self.active_mapping_profile)
        self.data["active_mapping_profile"] = "default"
        self._changed()

    @staticmethod
    def _delete(profiles: dict[str, dict[str, str]], name: str) -> None:
        if name == "default" or name not in profiles or len(profiles) <= 1:
            raise ValueError("default profile cannot be deleted")
        del profiles[name]

    def set_hotkey(self, action: str, binding: str) -> None:
        if action not in self.active_hotkeys:
            raise KeyError(action)
        normalized = str(KeyBinding.parse(binding))
        if normalized.lower() in self.reserved_bindings:
            raise ValueError("Binding is reserved by a plugin")
        for other, existing in self.active_hotkeys.items():
            if other != action and str(KeyBinding.parse(existing)) == normalized:
                raise ValueError(f"Binding already used by {other}")
        self.active_hotkeys[action] = normalized
        self._changed()

    def set_mapping(self, source: str, target: str) -> None:
        source = source.strip().upper()
        target = target.strip().upper()
        validated = ProfileStore.validate_mapping({source: target})
        if not validated:
            raise ValueError("source and target must be valid piano keys")
        for existing_source, existing_target in self.active_mapping.items():
            if existing_source != source and existing_target == target:
                raise ValueError(f"Output key {target} already used by {existing_source}")
        self.active_mapping[source] = target
        self._changed()

    def delete_mapping(self, source: str) -> None:
        self.active_mapping.pop(source.strip().upper(), None)
        self._changed()

    def save(self) -> None:
        previous = self.store.data
        self.store.data = copy.deepcopy(self.data)
        try:
            self.store.save()
        except Exception:
            self.store.data = previous
            raise
        self.dirty = False
        self.error = ""

    def cancel(self) -> None:
        self.data = copy.deepcopy(self.store.data)
        self.dirty = False
        self.error = ""

    def replace_hotkeys(self, values: Mapping[str, str]) -> None:
        for action, binding in values.items():
            self.set_hotkey(action, binding)
