"""Persistent hotkey and score-mapping profiles."""

from __future__ import annotations

import json
import os
import keyboard
import tempfile
from pathlib import Path
from typing import Mapping, cast

from src.application.config.constants import DEFAULT_HOTKEYS, VALID_KEYS
from src.ui.cli.input.key_binding import KeyBinding


class ProfileStore:
    """Manage independent hotkey and key-mapping profiles."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else Path.cwd() / "gipianoplayer_profiles.json"
        self.data: dict[str, object] = {}
        self.load()

    @staticmethod
    def _defaults() -> dict[str, object]:
        return {
            "version": 2,
            "active_hotkey_profile": "default",
            "active_mapping_profile": "default",
            "hotkey_profiles": {"default": DEFAULT_HOTKEYS.copy()},
            "mapping_profiles": {"default": {}},
            "mapping_scan_profiles": {"default": {}},
        }

    def load(self) -> None:
        defaults = self._defaults()
        needs_rebuild = False
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("profile root must be an object")
            self.data = self._sanitize(raw, defaults)
            needs_rebuild = self.data != raw
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            self.data = defaults
            needs_rebuild = True
        if needs_rebuild:
            try:
                self.save()
            except OSError:
                # A read-only working directory should still permit the
                # application to run with in-memory defaults.
                pass

    @staticmethod
    def _sanitize(
        raw: dict[str, object], defaults: dict[str, object]
    ) -> dict[str, object]:
        result = defaults
        hotkeys = raw.get("hotkey_profiles")
        if isinstance(hotkeys, dict):
            clean_hotkeys: dict[str, dict[str, str]] = {}
            for name, values in hotkeys.items():
                if isinstance(name, str) and name and isinstance(values, dict):
                    candidate: dict[str, str] = {}
                    for action, binding in values.items():
                        if (
                            not isinstance(action, str)
                            or action not in DEFAULT_HOTKEYS
                            or not isinstance(binding, str)
                        ):
                            continue
                        try:
                            normalized = str(KeyBinding.parse(binding))
                        except ValueError:
                            continue
                        candidate[action] = normalized
                    # Duplicate bindings make dispatch ambiguous; discard the
                    # conflicting entries and let defaults fill them below.
                    seen: set[str] = set()
                    unique: dict[str, str] = {}
                    for action, binding in candidate.items():
                        if binding not in seen:
                            unique[action] = binding
                            seen.add(binding)
                    clean_hotkeys[name] = unique
            if clean_hotkeys:
                default_hotkeys = clean_hotkeys.setdefault(
                    "default", DEFAULT_HOTKEYS.copy()
                )
                for action, binding in DEFAULT_HOTKEYS.items():
                    default_hotkeys.setdefault(action, binding)
                for profile in clean_hotkeys.values():
                    for action, binding in DEFAULT_HOTKEYS.items():
                        profile.setdefault(action, binding)
                result["hotkey_profiles"] = clean_hotkeys

        mappings = raw.get("mapping_profiles")
        if isinstance(mappings, dict):
            clean_mappings: dict[str, dict[str, str]] = {}
            for name, values in mappings.items():
                if isinstance(name, str) and name and isinstance(values, dict):
                    clean_mappings[name] = ProfileStore.validate_mapping(values)
            if clean_mappings:
                clean_mappings.setdefault("default", {})
                result["mapping_profiles"] = clean_mappings

        scan_profiles = raw.get("mapping_scan_profiles")
        if isinstance(scan_profiles, dict):
            clean_scans: dict[str, dict[str, dict[str, int]]] = {}
            for name, values in scan_profiles.items():
                if (
                    not isinstance(name, str)
                    or not name
                    or not isinstance(values, dict)
                ):
                    continue
                entries: dict[str, dict[str, int]] = {}
                for source, entry in values.items():
                    if not isinstance(source, str) or source.upper() not in VALID_KEYS:
                        continue
                    if isinstance(entry, dict):
                        source_code = entry.get("source_scan_code")
                        target_code = entry.get("target_scan_code")
                        if isinstance(source_code, int) and isinstance(
                            target_code, int
                        ):
                            entries[source.upper()] = {
                                "source_scan_code": source_code,
                                "target_scan_code": target_code,
                            }
                clean_scans[name] = entries
            if clean_scans:
                clean_scans.setdefault("default", {})
                result["mapping_scan_profiles"] = clean_scans
        scan_profiles = result["mapping_scan_profiles"]
        mappings = result["mapping_profiles"]
        if isinstance(scan_profiles, dict) and isinstance(mappings, dict):
            for profile, values in mappings.items():
                if not isinstance(values, dict):
                    continue
                scans = scan_profiles.setdefault(profile, {})
                if not isinstance(scans, dict):
                    scans = {}
                    scan_profiles[profile] = scans
                for source, target in values.items():
                    if source in scans or not isinstance(target, str):
                        continue
                    try:
                        source_codes = keyboard.key_to_scan_codes(source.lower())
                        target_codes = keyboard.key_to_scan_codes(target.lower())
                    except (ValueError, KeyError):
                        continue
                    if source_codes and target_codes:
                        scans[source] = {
                            "source_scan_code": int(source_codes[0]),
                            "target_scan_code": int(target_codes[0]),
                        }

        active_hotkeys = raw.get("active_hotkey_profile")
        hotkey_profiles = result["hotkey_profiles"]
        if (
            isinstance(active_hotkeys, str)
            and isinstance(hotkey_profiles, dict)
            and active_hotkeys in hotkey_profiles
        ):
            result["active_hotkey_profile"] = active_hotkeys
        active_mapping = raw.get("active_mapping_profile")
        mapping_profiles = result["mapping_profiles"]
        if (
            isinstance(active_mapping, str)
            and isinstance(mapping_profiles, dict)
            and active_mapping in mapping_profiles
        ):
            result["active_mapping_profile"] = active_mapping
        return result

    @staticmethod
    def validate_mapping(mapping: Mapping[object, object]) -> dict[str, str]:
        clean: dict[str, str] = {}
        for source, target in mapping.items():
            if not isinstance(source, str) or not isinstance(target, str):
                continue
            source = source.upper()
            target = target.strip().lower()
            if len(source) != 1 or source not in VALID_KEYS or not target:
                continue
            try:
                scan_codes = keyboard.key_to_scan_codes(target)
            except (KeyError, ValueError):
                continue
            if scan_codes:
                clean[source] = target.upper() if target.isalpha() else target
        return clean

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=self.path.name, suffix=".tmp", dir=self.path.parent
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(self.data, stream, indent=2, ensure_ascii=True)
                stream.write("\n")
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def hotkey_profiles(self) -> dict[str, dict[str, str]]:
        return self.data["hotkey_profiles"]  # type: ignore[return-value]

    def mapping_profiles(self) -> dict[str, dict[str, str]]:
        return self.data["mapping_profiles"]  # type: ignore[return-value]

    def active_hotkeys(self) -> dict[str, str]:
        name = self.data["active_hotkey_profile"]
        return self.hotkey_profiles()[str(name)].copy()

    def active_mapping(self) -> dict[str, str]:
        name = self.data["active_mapping_profile"]
        return self.mapping_profiles()[str(name)].copy()

    def mapping_scans(self, name: str | None = None) -> dict[str, dict[str, int]]:
        profile = name or str(self.data["active_mapping_profile"])
        profiles = self.data.get("mapping_scan_profiles", {})
        values = profiles.get(profile, {}) if isinstance(profiles, dict) else {}
        return cast(dict[str, dict[str, int]], values).copy()

    def select_hotkeys(self, name: str) -> None:
        if name not in self.hotkey_profiles():
            raise KeyError(name)
        self.data["active_hotkey_profile"] = name

    def select_mapping(self, name: str) -> None:
        if name not in self.mapping_profiles():
            raise KeyError(name)
        self.data["active_mapping_profile"] = name

    def add_hotkey_profile(
        self, name: str, values: Mapping[str, str] | None = None
    ) -> None:
        self._add(self.hotkey_profiles(), name, dict(values or self.active_hotkeys()))

    def add_mapping_profile(
        self, name: str, values: Mapping[str, str] | None = None
    ) -> None:
        candidate = cast(Mapping[object, object], values or self.active_mapping())
        self._add(self.mapping_profiles(), name, self.validate_mapping(candidate))
        scans = self.data.setdefault("mapping_scan_profiles", {})
        if isinstance(scans, dict):
            scans[name.strip()] = {}

    @staticmethod
    def _add(
        profiles: dict[str, dict[str, str]], name: str, values: dict[str, str]
    ) -> None:
        name = name.strip()
        if not name or name in profiles:
            raise ValueError("profile name is empty or already exists")
        profiles[name] = values

    def rename_hotkey_profile(self, old: str, new: str) -> None:
        self._rename(self.hotkey_profiles(), old, new)
        if self.data["active_hotkey_profile"] == old:
            self.data["active_hotkey_profile"] = new

    def rename_mapping_profile(self, old: str, new: str) -> None:
        self._rename(self.mapping_profiles(), old, new)
        scans = self.data.setdefault("mapping_scan_profiles", {})
        if isinstance(scans, dict) and old in scans:
            scans[new] = scans.pop(old)
        if self.data["active_mapping_profile"] == old:
            self.data["active_mapping_profile"] = new

    @staticmethod
    def _rename(profiles: dict[str, dict[str, str]], old: str, new: str) -> None:
        new = new.strip()
        if old not in profiles or not new or (new != old and new in profiles):
            raise ValueError("invalid profile rename")
        profiles[new] = profiles.pop(old)

    def delete_hotkey_profile(self, name: str) -> None:
        self._delete(self.hotkey_profiles(), name)
        if self.data["active_hotkey_profile"] == name:
            self.data["active_hotkey_profile"] = "default"

    def delete_mapping_profile(self, name: str) -> None:
        self._delete(self.mapping_profiles(), name)
        scans = self.data.get("mapping_scan_profiles", {})
        if isinstance(scans, dict):
            scans.pop(name, None)
        if self.data["active_mapping_profile"] == name:
            self.data["active_mapping_profile"] = "default"

    @staticmethod
    def _delete(profiles: dict[str, dict[str, str]], name: str) -> None:
        if name == "default" or name not in profiles or len(profiles) <= 1:
            raise ValueError("default profile cannot be deleted")
        del profiles[name]
