@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Resetting package.json back to broken dependency state...

(
echo {
echo   "name": "vite-autonomous-demo",
echo   "private": true,
echo   "version": "1.0.0",
echo   "type": "module",
echo   "scripts": {
echo     "dev": "vite",
echo     "build": "vite build",
echo     "test": "node test.js"
echo   },
echo   "dependencies": {
echo     "canvas-confetti": "MISSING"
echo   },
echo   "devDependencies": {
echo     "vite": "^5.0.0"
echo   }
echo }
) > package.json

del /q loop-audit.jsonl 2>nul
del /q loop-report.json 2>nul
del /q loop-report.md 2>nul

echo.
echo ==============================================================
echo [SUCCESS] package.json has been reset to its broken state!
echo You can run 'python demo_agent.py' or 'run_demo.bat' now.
echo ==============================================================
pause
