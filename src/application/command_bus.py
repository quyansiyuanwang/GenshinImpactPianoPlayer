"""Command dispatch and application event subscriptions."""

from dataclasses import dataclass
from typing import Callable, TypeVar

from src.application.events import InputEvent, InputKind

CommandHandler = Callable[[InputEvent], "CommandResult"]
EventType = TypeVar("EventType")


@dataclass(frozen=True)
class CommandResult:
    """Outcome of a command invocation."""

    success: bool = True
    message: str = ""

    @classmethod
    def ok(cls, message: str = "") -> "CommandResult":
        return cls(True, message)

    @classmethod
    def error(cls, message: str) -> "CommandResult":
        return cls(False, message)


class CommandBus:
    """Central registry for named synchronous application commands."""

    def __init__(self) -> None:
        self._handlers: dict[str, tuple[CommandHandler, Callable[[], bool] | None]] = {}
        self._subscribers: dict[type[object], list[Callable[[object], None]]] = {}

    def register(
        self,
        name: str,
        handler: CommandHandler,
        *,
        enabled_when: Callable[[], bool] | None = None,
        replace: bool = False,
    ) -> None:
        if name in self._handlers and not replace:
            raise ValueError(f"Command '{name}' is already registered")
        self._handlers[name] = (handler, enabled_when)

    def dispatch(self, name: str, event: InputEvent | None = None) -> CommandResult:
        entry = self._handlers.get(name)
        if entry is None:
            return CommandResult.error(f"Unknown command: {name}")
        handler, enabled_when = entry
        if enabled_when is not None and not enabled_when():
            return CommandResult.error("Command is locked")
        try:
            result = handler(event or InputEvent(InputKind.KEY))
            return result if isinstance(result, CommandResult) else CommandResult.ok()
        except Exception as error:
            return CommandResult.error(str(error))

    def subscribe(self, event_type: type[EventType], callback: Callable[[EventType], None]) -> None:
        self._subscribers.setdefault(event_type, []).append(callback)  # type: ignore[arg-type]

    def publish(self, event: object) -> None:
        for callback in self._subscribers.get(type(event), []):
            callback(event)

    def names(self) -> tuple[str, ...]:
        return tuple(self._handlers)
