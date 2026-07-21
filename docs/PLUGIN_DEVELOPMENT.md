# Plugin Development

Plugins are listed in `plugins.toml`. Built-in plugins live under `src/plugins/builtin`; external plugin paths can be added through `[plugins.custom_paths]`.

A plugin subclasses `src.plugins.core.plugin.Plugin` and receives a `PluginContext` during initialization. Register a hotkey through the context; the CLI collects it with the built-in bindings and installs it through the same handler.

```python
from src.plugins.core.context import PluginContext
from src.plugins.core.plugin import Plugin


class ExamplePlugin(Plugin):
    def __init__(self) -> None:
        super().__init__("example")

    def initialize(self, context: PluginContext) -> None:
        context.register_hotkey("f10", self.toggle)

    def toggle(self) -> None:
        pass
```

Plugin callbacks should return promptly because they run on the keyboard hook thread. Use the supplied player and CLI context rather than importing UI globals.
