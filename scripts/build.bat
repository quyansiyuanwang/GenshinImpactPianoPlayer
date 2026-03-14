@echo off
chcp 65001 >nul
echo ============================================================
echo GIPianoPlayer 打包脚本
echo ============================================================
echo.

REM 切换到项目根目录
cd /d "%~dp0\.."

REM 检查是否以管理员权限运行
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  警告: 建议以管理员权限运行此脚本
    echo.
    pause
)

echo 正在激活虚拟环境...
call .venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo ❌ 无法激活虚拟环境
    echo 请确保已运行: uv sync
    pause
    exit /b 1
)

echo.
echo 开始打包...
echo.

python scripts\build.py

if %errorLevel% equ 0 (
    echo.
    echo ============================================================
    echo ✅ 打包完成！
    echo ============================================================
    echo.
    echo 可执行文件位置: release\GIPianoPlayer.exe
    echo.
    echo 按任意键打开 release 目录...
    pause >nul
    explorer release
) else (
    echo.
    echo ❌ 打包失败！
    echo.
    pause
)
