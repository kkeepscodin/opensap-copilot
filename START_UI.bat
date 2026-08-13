@echo off
cd /d "%~dp0frontend"
echo OpenSAP Copilot UI: http://127.0.0.1:5500
start "" http://127.0.0.1:5500
py -m http.server 5500
