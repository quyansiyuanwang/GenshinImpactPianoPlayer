# Build Scripts

This directory contains scripts for building GIPianoPlayer into a standalone executable.

## Files

- **build.py** - Main Python build script using PyInstaller
- **build.bat** - Windows batch script wrapper
- **build.ps1** - PowerShell script wrapper

## Usage

See [../docs/BUILD.md](../docs/BUILD.md) for detailed instructions.

### Quick Start

**Windows (CMD):**
```cmd
scripts\build.bat
```

**PowerShell:**
```powershell
.\scripts\build.ps1
```

**Direct Python:**
```bash
python scripts/build.py
```

## Requirements

- PyInstaller (installed as dev dependency)
- Virtual environment activated
- Administrator privileges (recommended)

## Output

The build process creates:
- `build/` - Temporary build files (auto-cleaned)
- `dist/` - PyInstaller output directory
- `release/` - Final release package with documentation
- `version_info.txt` - Windows version information file
- `GIPianoPlayer.spec` - PyInstaller spec file

All build artifacts are git-ignored.
