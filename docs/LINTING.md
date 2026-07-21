# Testing And Quality

Install the development group with `uv sync --group dev`, then run:

```powershell
uv run python scripts/lint.py --check
```

The check runs pytest, Ruff linting, Ruff format verification, and strict MyPy. To apply Ruff fixes and formatting before checking types, run:

```powershell
uv run python scripts/lint.py --fix
```

The test suite uses fake keyboard controllers and does not send system keyboard input.
