$env:PYTHONUTF8 = "1"
$env:Path = "C:\Users\HP\AppData\Local\Programs\Python\Python312;C:\Users\HP\AppData\Local\Programs\Python\Python312\Scripts;" + $env:Path
Write-Host "Starting Loop Engineering AI Demonstrator..." -ForegroundColor Cyan
python demo_agent.py
