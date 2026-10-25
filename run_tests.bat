@echo off
set "PYTHONUTF8=1"
set "PATH=C:\Users\HP\AppData\Local\Programs\Python\Python312;C:\Users\HP\AppData\Local\Programs\Python\Python312\Scripts;%PATH%"
cd /d "%~dp0"
echo Running all 7 acceptance tests...
echo.
python -m unittest discover -s tests -v
pause
