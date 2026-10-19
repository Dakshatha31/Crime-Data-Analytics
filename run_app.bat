@echo off
TITLE Crime Data Analytics - Web Application
COLOR 0B
echo =======================================================================
echo          METROPOLITAN CRIME DATA ANALYTICS PLATFORM
echo          FastAPI + Leaflet GIS + Big Data Analytics
echo =======================================================================
echo.
echo [*] Checking Python environment...
python --version
if errorlevel 1 (
    echo [ERROR] Python is not found in PATH! Please install Python or add it to PATH.
    pause
    exit /b 1
)

echo.
echo [*] Launching Web Application on http://127.0.0.1:8000 ...
echo [*] Press Ctrl+C in this terminal window anytime to stop the server.
echo.

:: Automatically open the default browser after 2 seconds in the background
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000/"

:: Start the FastAPI / Uvicorn server
python web\server.py

pause
