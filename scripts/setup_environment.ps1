<#
=============================================================================
Crime Data Analytics — Environment Setup & Execution Script
Sets up Hadoop, Java 8, Python dependencies, and verifies big data environment.
=============================================================================
#>

Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "  CRIME DATA ANALYTICS — BIG DATA PLATFORM SETUP" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan

# 1. Setup Java 8
if (Test-Path "C:\Java8") {
    $env:JAVA_HOME = "C:\Java8"
    Write-Host "[+] JAVA_HOME detected: C:\Java8" -ForegroundColor Green
} else {
    $javaPath = (Get-Command java -ErrorAction SilentlyContinue).Source
    if ($javaPath) {
        $env:JAVA_HOME = (Get-Item $javaPath).Directory.Parent.FullName
        Write-Host "[+] JAVA_HOME detected: $env:JAVA_HOME" -ForegroundColor Green
    }
}

# 2. Setup Hadoop
if (Test-Path "C:\hadoop-3.3.6") {
    $env:HADOOP_HOME = "C:\hadoop-3.3.6"
    $env:Path = "C:\hadoop-3.3.6\bin;" + $env:Path
    Write-Host "[+] HADOOP_HOME detected: C:\hadoop-3.3.6" -ForegroundColor Green
    Write-Host "[+] winutils.exe and hadoop.dll configured in bin" -ForegroundColor Green
}

# 3. Verify Python Dependencies
Write-Host "[*] Verifying Python libraries..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
python -m pip install pandas numpy networkx reportlab fastapi uvicorn pymongo mongomock scikit-learn --quiet
Write-Host "[+] Python libraries ready." -ForegroundColor Green

# 4. Run Pipelines
Write-Host "[*] Executing end-to-end Big Data pipelines..." -ForegroundColor Yellow
python d:\projects\Crime_Analytics_BDC\scripts\run_all_pipelines.py

Write-Host "`n==============================================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE! RUN THE APPLICATION WITH:" -ForegroundColor Cyan
Write-Host "  python d:\projects\Crime_Analytics_BDC\scripts\start_server.py" -ForegroundColor Yellow
Write-Host "  Then open: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Cyan
