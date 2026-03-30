@echo off
REM ─────────────────────────────────────────────────────────
REM  build_windows.bat — Build standalone Windows executables
REM
REM  Usage:
REM    build_windows.bat          Build both CLI and GUI
REM    build_windows.bat cli      Build CLI only
REM    build_windows.bat gui      Build GUI only
REM
REM  Output:
REM    dist\video-analyzer.exe      CLI executable
REM    dist\video-analyzer-gui.exe  GUI executable
REM ─────────────────────────────────────────────────────────
setlocal enabledelayedexpansion

cd /d "%~dp0"

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=all"

echo.
echo ═══════════════════════════════════════════════════════
echo   Video Analyzer — Windows Build
echo ═══════════════════════════════════════════════════════
echo.

REM ── Check Python ──────────────────────────────────────────
set "PYTHON="
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON=python"
) else (
    where python3 >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON=python3"
    )
)

if "%PYTHON%"=="" (
    echo [X] Python 3.10+ is required but not found.
    echo     Download from: https://www.python.org/downloads/
    exit /b 1
)

for /f "tokens=*" %%v in ('%PYTHON% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PY_VERSION=%%v
echo [*] Using Python %PY_VERSION% (%PYTHON%)

REM ── Create / activate virtual environment ─────────────────
set "VENV_DIR=build_venv"

if not exist "%VENV_DIR%" (
    echo [*] Creating build virtual environment...
    %PYTHON% -m venv %VENV_DIR%
)

call %VENV_DIR%\Scripts\activate.bat
echo [+] Virtual environment activated

REM ── Install dependencies ──────────────────────────────────
echo [*] Installing dependencies...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet
echo [+] Dependencies installed

REM ── Clean previous builds ─────────────────────────────────
echo [*] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM ── Build CLI ─────────────────────────────────────────────
if "%TARGET%"=="all" goto build_cli
if "%TARGET%"=="cli" goto build_cli
goto skip_cli

:build_cli
echo.
echo [*] Building CLI executable...
pyinstaller video-analyzer-cli.spec --noconfirm --clean
echo [+] CLI built: dist\video-analyzer.exe
:skip_cli

REM ── Build GUI ─────────────────────────────────────────────
if "%TARGET%"=="all" goto build_gui
if "%TARGET%"=="gui" goto build_gui
goto skip_gui

:build_gui
echo.
echo [*] Building GUI executable...
pyinstaller video-analyzer-gui.spec --noconfirm --clean
echo [+] GUI built: dist\video-analyzer-gui.exe
:skip_gui

REM ── Done ──────────────────────────────────────────────────
echo.
echo ═══════════════════════════════════════════════════════
echo   Build complete! Executables are in .\dist\
echo.

if "%TARGET%"=="all" (
    echo   CLI:  .\dist\video-analyzer.exe --help
    echo   GUI:  .\dist\video-analyzer-gui.exe
)
if "%TARGET%"=="cli" (
    echo   CLI:  .\dist\video-analyzer.exe --help
)
if "%TARGET%"=="gui" (
    echo   GUI:  .\dist\video-analyzer-gui.exe
)

echo.
echo   Note: FFprobe (ffmpeg) must be installed on the
echo   target system for video metadata extraction.
echo   Install via: winget install ffmpeg
echo ═══════════════════════════════════════════════════════
echo.

deactivate
endlocal
