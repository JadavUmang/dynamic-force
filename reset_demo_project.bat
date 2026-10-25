@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Resetting demo_project back to broken baseline in Git...
git -C demo_project reset --hard broken-baseline
git -C demo_project clean -fd
git -C demo_project push origin master --force 2>nul
del /q demo_project\loop-audit.jsonl 2>nul
del /q demo_project\loop-report.json 2>nul
del /q demo_project\loop-report.md 2>nul
echo.
echo ==============================================================
echo [SUCCESS] demo_project has been reset to its broken state in Git and GitHub!
echo You can run 'python demo_agent.py' or 'repair_demo_project.bat' now.
echo ==============================================================
pause
