# GIPianoPlayer

GIPianoPlayer reads a text score and sends its notes as keyboard input. It is a Windows-focused CLI application for game piano layouts.

Requires Python 3.10 or newer. The `keyboard` library normally requires an elevated terminal on Windows.

```powershell
uv sync --group dev
uv run python main.py tests/sample_score.txt
```

The target application must have focus before playback begins.

## Documentation

- [Usage, score format, and hotkeys](docs/USAGE.md)
- [Build a Windows executable](docs/BUILD.md)
- [Plugin development](docs/PLUGIN_DEVELOPMENT.md)
- [Tests and code quality](docs/LINTING.md)

## Development

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy .
```
