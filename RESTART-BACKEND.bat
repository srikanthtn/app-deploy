@echo off
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║           RESTARTING BACKEND WITH PASSWORD FIX                 ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo The password fix has been applied!
echo Now restarting backend to load the new code...
echo.
echo Press Ctrl+C in your backend terminal, then run:
echo    .\venv\Scripts\python.exe run.py
echo.
echo OR just double-click this file to restart automatically!
echo.
pause
echo.
echo Starting backend...
.\venv\Scripts\python.exe run.py

