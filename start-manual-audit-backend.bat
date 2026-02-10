@echo off
REM ============================================================================
REM Manual Audit Backend Startup Script
REM ============================================================================
REM This script starts the FastAPI backend with manual audit endpoints enabled
REM ============================================================================

echo.
echo ========================================================================
echo  STELLANTIS DEALER HYGIENE - MANUAL AUDIT API
echo ========================================================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
echo [2/4] Checking dependencies...
python -c "import fastapi, sqlalchemy, psycopg2" 2>nul
if errorlevel 1 (
    echo [WARNING] Dependencies missing. Installing...
    pip install -r requirements.txt
)

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found. Copying from .env.manual_audit...
    copy .env.manual_audit .env
    echo [ACTION REQUIRED] Please update DATABASE_URL in .env file
)

echo [3/4] Starting Manual Audit API Server...
echo.
echo API Documentation will be available at:
echo   - Swagger UI: http://localhost:8000/docs
echo   - ReDoc:      http://localhost:8000/redoc
echo   - Health:     http://localhost:8000/api/v1/health
echo.
echo Manual Audit Endpoints:
echo   - POST   /api/v1/manual-audit          - Submit new audit
echo   - GET    /api/v1/manual-audit/{id}     - Get audit by ID
echo   - GET    /api/v1/manual-audits         - List all audits
echo   - GET    /api/v1/manual-audits/dealer/{dealer_id} - Get by dealer
echo.
echo [4/4] Running server (Press Ctrl+C to stop)...
echo.

python run.py

pause

