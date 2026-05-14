@echo off
echo ============================================================
echo   SF Case Intent Processor - API Server
echo   Starting on http://localhost:5000
echo ============================================================
echo.

cd /d "%~dp0sf-case-intent-processor"

:: Install dependencies if needed
pip install simple-salesforce python-dotenv filelock requests --quiet 2>nul

:: Start API server
echo Starting API server...
echo Press Ctrl+C to stop
echo.
python api_server.py

pause
