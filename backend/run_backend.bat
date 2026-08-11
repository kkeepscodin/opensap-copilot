@echo off
setlocal

echo Installing backend dependencies...
py -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo Starting OpenSAP Copilot API...
echo Swagger UI: http://127.0.0.1:8000/docs
echo.
py -m uvicorn main:app --reload

endlocal
