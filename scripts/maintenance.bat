@echo off
REM QuantFlow Maintenance - Quick Cleanup
REM This batch file runs the PowerShell maintenance script

echo QuantFlow Repository Maintenance
echo ================================

REM Check if we're in the right directory
if not exist ".git" (
    echo Error: Not in a git repository
    echo Please run this from the QuantFlow root directory
    pause
    exit /b 1
)

REM Run the PowerShell maintenance script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0maintenance.ps1" %*

echo.
echo Maintenance completed. Press any key to exit...
pause >nul
