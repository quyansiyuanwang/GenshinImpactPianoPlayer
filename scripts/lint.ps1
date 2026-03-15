# Linting and formatting shortcuts for GIPianoPlayer
# PowerShell version

param(
    [Parameter(Position=0)]
    [ValidateSet("check", "fix", "ruff", "format", "mypy")]
    [string]$Command
)

if (-not $Command) {
    Write-Host "Usage: .\scripts\lint.ps1 {check|fix|ruff|format|mypy}"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  check   - Run all checks without fixing"
    Write-Host "  fix     - Run all checks and auto-fix issues"
    Write-Host "  ruff    - Run Ruff linter only"
    Write-Host "  format  - Run formatters only"
    Write-Host "  mypy    - Run MyPy type checker only"
    exit 1
}

switch ($Command) {
    "check" {
        Write-Host "Running all checks (no fixes)..."
        python scripts\lint.py --check
    }
    "fix" {
        Write-Host "Running all checks with auto-fix..."
        python scripts\lint.py --fix
    }
    "ruff" {
        Write-Host "Running Ruff linter..."
        uv run ruff check --fix src/ tests/ scripts/
    }
    "format" {
        Write-Host "Running formatters..."
        uv run ruff format src/ tests/ scripts/
        uv run black src/ tests/ scripts/
    }
    "mypy" {
        Write-Host "Running MyPy type checker..."
        uv run mypy . --strict
    }
}
