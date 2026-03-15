@echo off
REM Linting and formatting shortcuts for GIPianoPlayer

if "%1"=="check" (
    echo Running all checks (no fixes)...
    python scripts\lint.py --check
    goto :eof
)

if "%1"=="fix" (
    echo Running all checks with auto-fix...
    python scripts\lint.py --fix
    goto :eof
)

if "%1"=="ruff" (
    echo Running Ruff linter...
    uv run ruff check --fix src/ tests/ scripts/
    goto :eof
)

if "%1"=="format" (
    echo Running formatters...
    uv run ruff format src/ tests/ scripts/
    uv run black src/ tests/ scripts/
    goto :eof
)

if "%1"=="mypy" (
    echo Running MyPy type checker...
    uv run mypy . --strict
    goto :eof
)

echo Usage: %0 {check^|fix^|ruff^|format^|mypy}
echo.
echo Commands:
echo   check   - Run all checks without fixing
echo   fix     - Run all checks and auto-fix issues
echo   ruff    - Run Ruff linter only
echo   format  - Run formatters only
echo   mypy    - Run MyPy type checker only
exit /b 1
