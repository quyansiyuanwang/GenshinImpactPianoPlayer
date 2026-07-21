"""Application layer.

Import from specific modules instead of from this __init__.py to avoid circular imports.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.application.config.manager import ConfigManager
    from src.application.services.file_service import FileService
    from src.application.services.playback_service import PlaybackService
    from src.application.state.app_state import ApplicationState

__all__ = [
    "ConfigManager",
    "FileService",
    "PlaybackService",
    "ApplicationState",
]


def __getattr__(name: str) -> Any:
    """Lazy import to avoid circular dependencies."""
    if name == "ConfigManager":
        from src.application.config.manager import ConfigManager

        return ConfigManager
    elif name == "FileService":
        from src.application.services.file_service import FileService

        return FileService
    elif name == "PlaybackService":
        from src.application.services.playback_service import PlaybackService

        return PlaybackService
    elif name == "ApplicationState":
        from src.application.state.app_state import ApplicationState

        return ApplicationState
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
