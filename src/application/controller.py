"""Application command controller shared by all input and UI frontends."""

from typing import Any, Callable

from src.application.command_bus import CommandBus, CommandResult
from src.application.events import InputEvent
from src.ui.cli.input.key_binding import KeyBinding


class ApplicationController:
    """Translate normalized bindings into named application commands."""

    def __init__(self, command_bus: CommandBus | None = None) -> None:
        self.bus = command_bus or CommandBus()
        self._bindings: dict[KeyBinding, str] = {}
        self._locked = False

    def register_command(
        self,
        name: str,
        handler: Callable[[InputEvent], CommandResult],
        *,
        enabled_when: Callable[[], bool] | None = None,
        replace: bool = False,
    ) -> None:
        self.bus.register(name, handler, enabled_when=enabled_when, replace=replace)

    def bind_key(self, binding: str, command: str) -> None:
        parsed = KeyBinding.parse(binding)
        if parsed in self._bindings:
            raise ValueError(f"Binding '{binding}' is already assigned")
        self._bindings[parsed] = command

    def binding_command(self, binding: str) -> str | None:
        """Return the command currently assigned to a binding, if any."""
        try:
            return self._bindings.get(KeyBinding.parse(binding))
        except ValueError:
            return None

    def clear_bindings(self, *, preserve_prefixes: tuple[str, ...] = ()) -> None:
        """Remove key bindings, optionally retaining plugin-owned commands."""
        if not preserve_prefixes:
            self._bindings.clear()
            return
        self._bindings = {
            binding: command
            for binding, command in self._bindings.items()
            if command.startswith(preserve_prefixes)
        }

    def dispatch(self, command: str, event: InputEvent | None = None) -> CommandResult:
        if self._locked and command != "input.toggle_lock":
            return CommandResult.error("Command input is locked")
        return self.bus.dispatch(command, event)

    def dispatch_event(self, event: InputEvent) -> CommandResult | None:
        for binding, command in self._bindings.items():
            if binding.matches(event):
                return self.dispatch(command, event)
        return None

    def set_locked(self, locked: bool) -> None:
        self._locked = bool(locked)

    def is_locked(self) -> bool:
        return self._locked

    def command_names(self) -> tuple[str, ...]:
        return self.bus.names()

    def register_host_method(self, command: str, host: Any, method: str) -> None:
        """Register a legacy CLI method as a command during migration."""

        def invoke(_event: InputEvent) -> CommandResult:
            result = getattr(host, method)()
            return result if isinstance(result, CommandResult) else CommandResult.ok()

        self.register_command(command, invoke)
