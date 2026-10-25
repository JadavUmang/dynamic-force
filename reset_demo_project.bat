@echo off
cd /d "%~dp0"
echo Resetting demo_project back to broken state...
git -C demo_project checkout HEAD -- calculator.py
del /q demo_project\loop-audit.jsonl 2>nul
del /q demo_project\loop-report.json 2>nul
del /q demo_project\loop-report.md 2>nul
echo.
echo ==============================================================
echo [SUCCESS] demo_project has been reset to its broken state!
echo You can run 'repair_demo_project.bat' again now.
echo ==============================================================
pause
