@echo off
setlocal
cd /d "%~dp0"

echo =============================================
echo OpenSAP Copilot - PN-043 Evaluation
echo =============================================

if not exist "backend\.venv\Scripts\python.exe" (
  echo [ERROR] backend virtual environment not found.
  echo Run START_BACKEND.bat once first, then close it and retry.
  pause
  exit /b 1
)

"backend\.venv\Scripts\python.exe" "evaluation\evaluate.py"
set RC=%ERRORLEVEL%

echo.
if %RC%==0 (
  echo [PASS] PN-043 evaluation completed successfully.
) else (
  echo [FAIL] One or more evaluation checks failed.
)

echo Result file: evaluation\results\latest_report.json
pause
exit /b %RC%
