$env:PYTHONUTF8 = "1"
$env:Path = "C:\Users\HP\AppData\Local\Programs\Python\Python312;C:\Users\HP\AppData\Local\Programs\Python\Python312\Scripts;" + $env:Path
Write-Host "Running 7/7 Acceptance Tests..." -ForegroundColor Cyan
python -m unittest discover -s tests -v
