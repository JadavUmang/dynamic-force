@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PATH=C:\Users\HP\AppData\Local\Programs\Python\Python312;C:\Users\HP\AppData\Local\Programs\Python\Python312\Scripts;%PATH%"
cd /d "%~dp0"
echo Starting Loop Engineering AI Demonstrator...
echo.
python demo_agent.py
pause
