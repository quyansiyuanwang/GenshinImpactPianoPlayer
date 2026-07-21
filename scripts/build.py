"""Build script for creating GIPianoPlayer executable."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Change to project root directory
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)
print(f"Working directory: {PROJECT_ROOT}\n")


def clean_build_dirs() -> None:
    """Clean previous build directories."""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}/...")
            shutil.rmtree(dir_name)

    # Clean .spec file
    spec_file = "GIPianoPlayer.spec"
    if os.path.exists(spec_file):
        print(f"Removing {spec_file}...")
        os.remove(spec_file)


def create_version_file() -> None:
    """Create version info file for Windows executable."""
    version_info = """# UTF-8
#
# For more details about fixed file info:
# See https://msdn.microsoft.com/en-us/library/ms646997.aspx

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'GIPianoPlayer'),
        StringStruct(u'FileDescription', u'Automated Piano Playing Script'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'GIPianoPlayer'),
        StringStruct(u'LegalCopyright', u'MIT License'),
        StringStruct(u'OriginalFilename', u'GIPianoPlayer.exe'),
        StringStruct(u'ProductName', u'GIPianoPlayer'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""

    with open("version_info.txt", "w", encoding="utf-8") as f:
        f.write(version_info)
    print("Created version_info.txt")


def build_executable() -> None:
    """Build the executable using PyInstaller."""
    print("\n" + "=" * 60)
    print("Building GIPianoPlayer executable...")
    print("=" * 60 + "\n")

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=GIPianoPlayer",
        "--onefile",  # Single executable file
        "--console",  # Console application (required for curses)
        "--clean",
        "--noconfirm",
        # Add hidden imports
        "--hidden-import=keyboard",
        "--hidden-import=keyboard._winkeyboard",
        "--hidden-import=keyboard._canonical_names",
        "--hidden-import=keyboard._keyboard_event",
        "--hidden-import=curses",
        "--hidden-import=_curses",
        # Plugin system
        "--hidden-import=src.plugins",
        "--hidden-import=src.plugins.core",
        "--hidden-import=src.plugins.core.loader",
        "--hidden-import=src.plugins.core.manager",
        "--hidden-import=src.plugins.core.plugin",
        "--hidden-import=src.plugins.core.context",
        "--hidden-import=src.plugins.builtin",
        "--hidden-import=src.plugins.builtin.config",
        "--hidden-import=src.plugins.builtin.config.config_manager",
        # Add data files
        "--add-data=plugins.toml;.",  # IMPORTANT: Include plugins config
        "--add-data=tests/sample_score.txt;tests",
        "--add-data=README.md;.",
        "--add-data=docs;docs",
        # Version info
        "--version-file=version_info.txt",
        # Icon (if you have one)
        # "--icon=icon.ico",
        # Entry point
        "main.py",
    ]

    print("Running PyInstaller with command:")
    print(" ".join(cmd))
    print()

    result = subprocess.run(cmd, check=False)

    if result.returncode != 0:
        print("\nBuild failed.")
        sys.exit(1)

    print("\nBuild completed successfully!")


def create_release_package() -> None:
    """Create a release package with executable and documentation."""
    print("\n" + "=" * 60)
    print("Creating release package...")
    print("=" * 60 + "\n")

    release_dir = Path("release")
    if release_dir.exists():
        shutil.rmtree(release_dir)

    release_dir.mkdir()

    # Copy executable
    exe_path = Path("dist/GIPianoPlayer.exe")
    if exe_path.exists():
        shutil.copy(exe_path, release_dir / "GIPianoPlayer.exe")
        print(f"Copied {exe_path}")
    else:
        print(f"Executable not found: {exe_path}")
        sys.exit(1)

    # Copy documentation
    shutil.copy("README.md", release_dir / "README.md")
    print("Copied README.md")

    # Copy docs directory
    shutil.copytree("docs", release_dir / "docs")
    print("Copied docs/")

    # Copy sample score
    (release_dir / "examples").mkdir()
    shutil.copy("tests/sample_score.txt", release_dir / "examples" / "sample_score.txt")
    print("Copied sample_score.txt")

    # Create usage instructions
    usage_text = """# GIPianoPlayer - 使用说明

## 快速开始

1. 准备一个谱面文件（参考 examples/sample_score.txt）
2. 以管理员权限运行命令提示符或PowerShell
3. 运行程序：
   ```
   GIPianoPlayer.exe path/to/your/score.txt
   ```

## 重要提示

- **必须以管理员权限运行**，否则快捷键功能无法使用
- 运行后将焦点切换到目标应用（如游戏窗口）
- 使用快捷键控制播放（详见 docs/USAGE.md）

## 快捷键

- F8: 播放/暂停
- F2: 退出
- F5: 重新加载谱面
- F6: 重新解析（应用新配置）
- F7: 切换延音模式
- F9: 保存配置
- +/-: 调整速度
- Ctrl++/Ctrl+-: 快速调整速度
- [/]: 调整琶音间隔
- ,/.: 调整音符间隔
- Up/Down: 调整行间隔
- PgUp/PgDn: 调整段落长度
- Left/Right: 跳过1个音符
- Ctrl+Left/Right: 跳过1行

## 更多文档

请查看 docs/ 目录中的详细文档。
"""

    with open(release_dir / "使用说明.txt", "w", encoding="utf-8") as f:
        f.write(usage_text)
    print("Created usage instructions")

    print(f"\nRelease package created in: {release_dir.absolute()}")
    print("\nPackage contents:")
    for item in release_dir.rglob("*"):
        if item.is_file():
            size = item.stat().st_size / 1024 / 1024  # MB
            print(f"   {size:.2f} MB")


def main() -> None:
    """Main build process."""
    print("\n" + "=" * 60)
    print("GIPianoPlayer Build Script")
    print("=" * 60 + "\n")

    # Step 1: Clean
    print("Step 1: Cleaning previous builds...")
    clean_build_dirs()
    print("Clean completed\n")

    # Step 2: Create version file
    print("Step 2: Creating version info...")
    create_version_file()
    print("Version info created\n")

    # Step 3: Build executable
    print("Step 3: Building executable...")
    build_executable()

    # Step 4: Create release package
    print("Step 4: Creating release package...")
    create_release_package()

    print("\n" + "=" * 60)
    print("Build process completed successfully!")
    print("=" * 60)
    print("\nYou can find the release package in the 'release/' directory.")
    print("The standalone executable is: release/GIPianoPlayer.exe")
    print("\nRemember: run with administrator privileges when required.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nBuild failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
