@echo off
TITLE ICT Trading Suite
color 0A
echo ========================================
echo       ICT Autonomous Trading Suite      
echo ========================================
echo.
echo Checking environment...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed! Please install Python to run this software.
    pause
    exit /b
)

:: Install requirements silently if they don't exist
echo Installing/Verifying Dependencies...
pip install -r requirements.txt -q

echo.
echo Starting AI Engine...
echo.

:: Launch the system
python launcher.py

pause
