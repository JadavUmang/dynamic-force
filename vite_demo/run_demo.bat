@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PATH=C:\Users\HP\AppData\Local\Programs\Python\Python312;C:\Users\HP\AppData\Local\Programs\Python\Python312\Scripts;%PATH%"
cd /d "%~dp0"

echo ==============================================================
echo 🚀 Running Loop Engineering AI on Vite Web Project
echo ==============================================================
echo Target: vite_demo (package.json)
echo.
python demo_agent.py
pause
