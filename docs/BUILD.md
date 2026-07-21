# Build

Use Python 3.10+ and synchronize development dependencies first:

```powershell
uv sync --group dev
uv run python scripts/build.py
```

The build script creates a one-file Windows executable with `plugins.toml`, the sample score, README, and the current documentation. Output is written to `release/GIPianoPlayer.exe`.

Run the executable from an elevated terminal when keyboard output or global hotkeys require it.

## GitHub Actions

The `CI` workflow runs tests, quality checks, and a Windows build on pushes and pull requests. Its ZIP package is available as a workflow artifact.

Push a version tag such as `v1.0.0` to run the `Release` workflow. It repeats validation, builds `GIPianoPlayer-v1.0.0-windows-x64.zip`, and creates or updates the matching GitHub Release. The release workflow can also be run manually for an existing tag.

## Branch Policy

Develop features and fixes on `dev` or a feature branch targeting `dev`. Pull requests into `dev` run CI and provide the integration point for ongoing work. Promote a tested `dev` commit to `main` through a pull request, then create a `v*` tag from that `main` commit to publish a release. The release workflow rejects tags that are not reachable from `main`.
