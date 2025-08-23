@echo off
REM Windows launcher script for Boneglaive
REM Usage: run_boneglaive.bat [arguments]
REM Example: run_boneglaive.bat --mode vs_ai --debug

echo Starting Boneglaive on Windows...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if windows-curses is installed
python -c "import windows_curses" >nul 2>&1
if errorlevel 1 (
    echo WARNING: windows-curses not found
    echo Installing windows-curses for terminal support...
    pip install windows-curses
    if errorlevel 1 (
        echo ERROR: Failed to install windows-curses
        echo Please run: pip install windows-curses
        pause
        exit /b 1
    )
)

REM Run the game with all passed arguments
python boneglaive\main.py %*

REM Pause on exit if there was an error
if errorlevel 1 (
    echo.
    echo Game exited with error code %errorlevel%
    pause
)