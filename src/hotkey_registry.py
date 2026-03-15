"""Hotkey registry system for GIPianoPlayer.

Provides a centralized system for registering and managing hotkeys.
"""

from typing import Callable


class HotkeyRegistry:
    """Registry for managing hotkeys and their callbacks."""

    def __init__(self) -> None:
        """Initialize hotkey registry."""
        self._hotkeys: dict[str, Callable[[], None]] = {}
        self._descriptions: dict[str, str] = {}
        self._categories: dict[str, list[str]] = {}

    def register(
        self,
        key: str,
        callback: Callable[[], None],
        description: str = "",
        category: str = "general",
    ) -> None:
        """Register a hotkey.

        Args:
            key: Hotkey string (e.g., "f8", "ctrl+p")
            callback: Function to call when hotkey is pressed
            description: Human-readable description of the action
            category: Category for grouping (e.g., "playback", "navigation")
        """
        if key in self._hotkeys:
            raise ValueError(f"Hotkey '{key}' is already registered")

        self._hotkeys[key] = callback
        self._descriptions[key] = description

        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(key)

    def unregister(self, key: str) -> None:
        """Unregister a hotkey.

        Args:
            key: Hotkey string to unregister
        """
        if key in self._hotkeys:
            del self._hotkeys[key]
            del self._descriptions[key]

            # Remove from category
            for category_keys in self._categories.values():
                if key in category_keys:
                    category_keys.remove(key)

    def get_callback(self, key: str) -> Callable[[], None] | None:
        """Get callback for a hotkey.

        Args:
            key: Hotkey string

        Returns:
            Callback function or None if not registered
        """
        return self._hotkeys.get(key)

    def get_all_hotkeys(self) -> dict[str, Callable[[], None]]:
        """Get all registered hotkeys.

        Returns:
            Dictionary of hotkey -> callback
        """
        return self._hotkeys.copy()

    def get_description(self, key: str) -> str:
        """Get description for a hotkey.

        Args:
            key: Hotkey string

        Returns:
            Description or empty string if not found
        """
        return self._descriptions.get(key, "")

    def get_by_category(self, category: str) -> list[tuple[str, str]]:
        """Get hotkeys in a category.

        Args:
            category: Category name

        Returns:
            List of (key, description) tuples
        """
        keys = self._categories.get(category, [])
        return [(key, self._descriptions.get(key, "")) for key in keys]

    def get_all_categories(self) -> list[str]:
        """Get all category names.

        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def clear(self) -> None:
        """Clear all registered hotkeys."""
        self._hotkeys.clear()
        self._descriptions.clear()
        self._categories.clear()


# Global hotkey registry instance
_hotkey_registry = HotkeyRegistry()


def get_hotkey_registry() -> HotkeyRegistry:
    """Get the global hotkey registry instance.

    Returns:
        Global hotkey registry
    """
    return _hotkey_registry
