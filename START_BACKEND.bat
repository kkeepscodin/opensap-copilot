@echo off
setlocal
cd /d "%~dp0backend"

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py"
) else (
  set "PYTHON_CMD=python"
)

if not exist ".venv\Scripts\python.exe" (
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"

python -m pip install -r requirements.txt
if errorlevel 1 goto :error

python -m pytest -q
if errorlevel 1 goto :error

echo.
echo OpenSAP Copilot backend v0.4.0
echo Swagger: http://127.0.0.1:8000/docs
echo.
python -m uvicorn main:app --reload
exit /b 0

:error
echo.
echo Backend setup failed. Copy the last error lines and send them in the chat.
pause
exit /b 1
