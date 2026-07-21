#!/usr/bin/env python
"""Linting and formatting script for GIPianoPlayer."""

import subprocess
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Change to project root
PROJECT_ROOT = Path(__file__).parent.parent
print(f"Working directory: {PROJECT_ROOT}\n")


def run_command(name: str, command: list[str], check_only: bool = False) -> bool:
    """Run a command and return success status."""
    print(f"{'=' * 70}")
    print(f"Running {name}...")
    print(f"{'=' * 70}")

    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=False,
            text=True,
        )

        if result.returncode == 0:
            print(f"✅ {name} passed\n")
            return True
        else:
            print(f"❌ {name} failed with exit code {result.returncode}\n")
            return False
    except Exception as e:
        print(f"❌ {name} error: {e}\n")
        return False


def main() -> None:
    """Main linting process."""
    check_only = "--check" in sys.argv

    print("GIPianoPlayer - Code Quality Tools")
    print("=" * 70)
    print(f"Mode: {'Check only' if check_only else 'Fix and format'}\n")

    results = {}

    # 1. Unit tests
    results["Pytest"] = run_command("Pytest", ["uv", "run", "pytest"])

    # 2. Ruff check (linting)
    if check_only:
        results["Ruff Lint"] = run_command(
            "Ruff Lint", ["uv", "run", "ruff", "check", "src/", "tests/", "scripts/"]
        )
    else:
        results["Ruff Lint"] = run_command(
            "Ruff Lint (with fixes)",
            ["uv", "run", "ruff", "check", "--fix", "src/", "tests/", "scripts/"],
        )

    # 3. Ruff format (formatting)
    if check_only:
        results["Ruff Format"] = run_command(
            "Ruff Format",
            ["uv", "run", "ruff", "format", "--check", "src/", "tests/", "scripts/"],
        )
    else:
        results["Ruff Format"] = run_command(
            "Ruff Format", ["uv", "run", "ruff", "format", "src/", "tests/", "scripts/"]
        )

    # 4. MyPy (type checking) - always check only
    results["MyPy"] = run_command("MyPy", ["uv", "run", "mypy", ".", "--strict"])

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_passed = True
    for tool, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{tool:20s} {status}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n🎉 All checks passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
