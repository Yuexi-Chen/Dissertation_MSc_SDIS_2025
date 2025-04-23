
$env:SONAR_TOKEN = "YOUR_SONAR_TOKEN_HERE"

Write-Host "Token set: $($env:SONAR_TOKEN.Substring(0,4))...$($env:SONAR_TOKEN.Substring($env:SONAR_TOKEN.Length-4))"

$env:TEMP_DIR = "$env:TEMP\sonarqube_analysis_$([System.Random]::New().Next(10000, 99999))"
New-Item -ItemType Directory -Path $env:TEMP_DIR -Force | Out-Null
Write-Host "Using temporary directory: $env:TEMP_DIR"

Write-Host "Environment variables set successfully."
Write-Host "Running verify_analyzer.py..."

python scripts\verify_analyzer.py

exit $LASTEXITCODE 

# Run:
# powershell -ExecutionPolicy Bypass -File .\scripts\set_env.ps1