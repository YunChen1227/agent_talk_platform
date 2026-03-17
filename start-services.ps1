# Start MySQL and Elasticsearch for local dev environment

Write-Host "[1/2] Starting MySQL80 service..."
$mysql = Get-Service -Name "MySQL80" -ErrorAction SilentlyContinue
if (-not $mysql) {
    Write-Host "  ERROR: MySQL80 service not found" -ForegroundColor Red
} elseif ($mysql.Status -eq "Running") {
    Write-Host "  MySQL80 already running" -ForegroundColor Green
} else {
    try {
        Start-Service -Name "MySQL80" -ErrorAction Stop
        Start-Sleep -Seconds 1
        $mysql = Get-Service -Name "MySQL80"
        if ($mysql.Status -eq "Running") {
            Write-Host "  MySQL80 started" -ForegroundColor Green
        } else {
            Write-Host "  MySQL80 did not reach Running (Status: $($mysql.Status))" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ERROR: Could not start MySQL80 — $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "  Fix: Right-click PowerShell -> Run as administrator, then run this script again." -ForegroundColor Yellow
        Write-Host "  Or: Win+R -> services.msc -> find MySQL80 -> Start." -ForegroundColor Yellow
    }
}

Write-Host "[2/2] Starting Elasticsearch..."
$esProc = Get-Process -Name "java" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "elasticsearch" }
if ($esProc) {
    Write-Host "  Elasticsearch already running (PID $($esProc.Id))" -ForegroundColor Green
} else {
    Start-Process -FilePath "C:\elasticsearch-9.3.1\bin\elasticsearch.bat" -WindowStyle Hidden
    Write-Host "  Elasticsearch starting in background, waiting for port 9200..." -ForegroundColor Yellow

    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 2
        try {
            $null = (New-Object System.Net.Sockets.TcpClient).Connect("localhost", 9200)
            $ready = $true
            break
        } catch {}
    }
    if ($ready) {
        Write-Host "  Elasticsearch ready on :9200" -ForegroundColor Green
    } else {
        Write-Host "  Elasticsearch did not respond within 60s, check logs" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Done. Services status:" -ForegroundColor Cyan
$s = Get-Service -Name "MySQL80" -ErrorAction SilentlyContinue
if ($s) { $s | Format-Table Name, Status -AutoSize } else { Write-Host "  MySQL80: (service not found)" }
