@echo off
echo ========================================
echo    Email Auto-Download Tool - Build
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+
    exit /b 1
)

REM Create virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM Run tests first
echo.
echo Running tests...
pytest tests/ -v
if errorlevel 1 (
    echo.
    echo ERROR: Tests failed! Fix tests before building.
    pause
    exit /b 1
)

REM Build executable
echo.
echo Building executable...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "EmailAutoDownload" ^
    --add-data "config;config" ^
    --hidden-import "charset_normalizer" ^
    --hidden-import "keyring.backends.Windows" ^
    --hidden-import "customtkinter" ^
    --hidden-import "PIL._tkinter_finder" ^
    app.py

REM Copy fresh config to dist
echo.
echo Copying config files to dist...
if not exist dist\config mkdir dist\config
copy /Y config\rules.json dist\config\rules.json
copy /Y config\settings.json dist\config\settings.json

echo.
echo ========================================
echo Build complete!
echo Output: dist\EmailAutoDownload.exe
echo ========================================
pause
