# Build

Use Python 3.10+ and synchronize development dependencies first:

```powershell
uv sync --group dev
uv run python scripts/build.py
```

The build script creates a one-file Windows executable with `plugins.toml`, the sample score, README, and the current documentation. Output is written to `release/GIPianoPlayer.exe`.

Run the executable from an elevated terminal when keyboard output or global hotkeys require it.
