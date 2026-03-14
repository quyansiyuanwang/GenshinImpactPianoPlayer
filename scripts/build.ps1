# GIPianoPlayer Build Script (PowerShell)
# Encoding: UTF-8

# Change to project root directory
Set-Location $PSScriptRoot\..

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "GIPianoPlayer 打包脚本" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  警告: 建议以管理员权限运行此脚本" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "按 Enter 继续"
}

# Activate virtual environment
Write-Host "正在激活虚拟环境..." -ForegroundColor Green
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .venv\Scripts\Activate.ps1
} else {
    Write-Host "❌ 无法找到虚拟环境" -ForegroundColor Red
    Write-Host "请确保已运行: uv sync" -ForegroundColor Yellow
    Read-Host "按 Enter 退出"
    exit 1
}

Write-Host ""
Write-Host "开始打包..." -ForegroundColor Green
Write-Host ""

# Run build script
python scripts\build.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "✅ 打包完成！" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "可执行文件位置: release\GIPianoPlayer.exe" -ForegroundColor Cyan
    Write-Host ""

    $openFolder = Read-Host "是否打开 release 目录? (Y/n)"
    if ($openFolder -ne "n" -and $openFolder -ne "N") {
        explorer release
    }
} else {
    Write-Host ""
    Write-Host "❌ 打包失败！" -ForegroundColor Red
    Write-Host ""
    Read-Host "按 Enter 退出"
}
