@echo off
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                  STARTING BACKEND - FIXED VERSION                          ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.
echo Checking Python...
python --version
echo.
echo Activating virtual environment...
if exist venv (
    call venv\Scripts\activate
) else (
    echo Creating new virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo.
    echo Installing requirements...
    pip install -r requirements.txt
)
echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                       STARTING BACKEND SERVER                              ║
echo ║                   http://localhost:8000                                    ║
echo ║                                                                            ║
echo ║   Health Check: http://localhost:8000/health                               ║
echo ║   API Docs: http://localhost:8000/docs                                     ║
echo ║                                                                            ║
echo ║   Press Ctrl+C to stop                                                     ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.
python run.py

