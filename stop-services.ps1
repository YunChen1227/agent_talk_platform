# Stop MySQL and Elasticsearch (mirror of start-services.ps1)



Write-Host "[1/2] Stopping MySQL80 service..."

$mysql = Get-Service -Name "MySQL80" -ErrorAction SilentlyContinue

if (-not $mysql) {

    Write-Host "  ERROR: MySQL80 service not found" -ForegroundColor Red

} elseif ($mysql.Status -ne "Running") {

    Write-Host "  MySQL80 already stopped" -ForegroundColor Yellow

} else {
    try {
        Stop-Service -Name "MySQL80" -Force -ErrorAction Stop
        Start-Sleep -Seconds 1
        $mysqlAfterStop = Get-Service -Name "MySQL80"
        if ($mysqlAfterStop.Status -ne "Running") {
            Write-Host "  MySQL80 stopped" -ForegroundColor Green
        } else {
            Write-Host "  MySQL80 still Running (stop may need more time or admin rights)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ERROR: Could not stop MySQL80 — $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "  From CMD, run as admin (UAC):" -ForegroundColor Yellow
        Write-Host "  powershell -Command \"Start-Process powershell -ArgumentList '-NoExit','-ExecutionPolicy Bypass','-File','$PSScriptRoot\stop-services.ps1' -Verb RunAs\"" -ForegroundColor Gray
    }
}



Write-Host "[2/2] Stopping Elasticsearch..."

$esProcs = Get-CimInstance Win32_Process -Filter "Name = 'java.exe'" -ErrorAction SilentlyContinue |

    Where-Object { $_.CommandLine -match 'elasticsearch' }

if (-not $esProcs) {

    Write-Host "  No Elasticsearch Java process found (already stopped?)" -ForegroundColor Yellow

} else {

    foreach ($p in @($esProcs)) {

        try {

            Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop

            Write-Host "  Stopped Elasticsearch (PID $($p.ProcessId))" -ForegroundColor Green

        } catch {

            Write-Host "  ERROR: Could not stop PID $($p.ProcessId): $_" -ForegroundColor Red

        }

    }

}



Write-Host ""

Write-Host "Done. MySQL status:" -ForegroundColor Cyan

$mysqlAfter = Get-Service -Name "MySQL80" -ErrorAction SilentlyContinue

if ($mysqlAfter) {

    $mysqlAfter | Format-Table Name, Status -AutoSize

} else {

    Write-Host "  (MySQL80 service not found)"

}


