#!/bin/bash
# Linting and formatting shortcuts for GIPianoPlayer

case "$1" in
    "check")
        echo "Running all checks (no fixes)..."
        python scripts/lint.py --check
        ;;
    "fix")
        echo "Running all checks with auto-fix..."
        python scripts/lint.py --fix
        ;;
    "ruff")
        echo "Running Ruff linter..."
        uv run ruff check --fix src/ tests/ scripts/
        ;;
    "format")
        echo "Running Ruff formatter..."
        uv run ruff format src/ tests/ scripts/
        ;;
    "mypy")
        echo "Running MyPy type checker..."
        uv run mypy . --strict
        ;;
    *)
        echo "Usage: $0 {check|fix|ruff|format|mypy}"
        echo ""
        echo "Commands:"
        echo "  check   - Run all checks without fixing"
        echo "  fix     - Run all checks and auto-fix issues"
        echo "  ruff    - Run Ruff linter only"
        echo "  format  - Run formatters only"
        echo "  mypy    - Run MyPy type checker only"
        exit 1
        ;;
esac
