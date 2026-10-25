@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Resetting calculator.py back to broken state...

(
echo """
echo Sample Calculator Service
echo Contains intentional defect for Loop Engineering AI live demonstration.
echo """
echo.
echo def add(a: int, b: int^) -^> int:
echo     """Adds two numbers together."""
echo     # Intentional defect: using subtraction instead of addition
echo     return a - b
echo.
echo def multiply(a: int, b: int^) -^> int:
echo     """Multiplies two numbers."""
echo     return a * b
) > calculator.py

del /q loop-audit.jsonl 2>nul
del /q loop-report.json 2>nul
del /q loop-report.md 2>nul

echo.
echo ==============================================================
echo [SUCCESS] calculator.py has been reset to its broken state!
echo You can run 'python demo_agent.py' or 'run_demo.bat' now.
echo ==============================================================
pause
