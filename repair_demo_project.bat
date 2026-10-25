@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PATH=C:\Users\HP\AppData\Local\Programs\Python\Python312;C:\Users\HP\AppData\Local\Programs\Python\Python312\Scripts;%PATH%"
cd /d "%~dp0"
echo ==============================================================
echo 🚀 Running Loop Engineering AI against ./demo_project
echo ==============================================================
echo Target: ./demo_project
echo Task: Fix calculation bug in calculator.py
echo.
python -m loop_ai --repo ./demo_project --task "Fix calculation bug in calculator.py" --test "python -m unittest discover -v" --provider offline --allow-dirty
echo.
echo Check the generated report: demo_project\loop-report.md
echo ==============================================================
pause
