@echo off
setlocal

echo =============================================
echo OpenSAP Copilot - Local AI Check
echo =============================================
echo.

where ollama >nul 2>nul
if errorlevel 1 (
  echo [FAIL] Ollama command was not found.
  echo Install/start Ollama, then run this file again.
  pause
  exit /b 1
)

echo [OK] Ollama is installed:
ollama --version
echo.

echo Checking installed model qwen2.5-coder:3b ...
ollama list | findstr /i /c:"qwen2.5-coder:3b" >nul
if errorlevel 1 (
  echo [FAIL] qwen2.5-coder:3b is not installed.
  echo Run: ollama pull qwen2.5-coder:3b
  pause
  exit /b 1
)

echo [OK] qwen2.5-coder:3b is installed.
echo.

echo Checking local Ollama API...
curl -s --max-time 5 http://127.0.0.1:11434/api/version
if errorlevel 1 (
  echo.
  echo [FAIL] Could not reach Ollama API on 127.0.0.1:11434.
  echo Open Ollama and run this check again.
  pause
  exit /b 1
)

echo.
echo.
echo [OK] Local AI prerequisites are ready.
pause
endlocal
