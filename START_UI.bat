@echo off
setlocal
cd /d "%~dp0frontend"
start "" http://127.0.0.1:5500
py -m http.server 5500 --bind 127.0.0.1
endlocal
