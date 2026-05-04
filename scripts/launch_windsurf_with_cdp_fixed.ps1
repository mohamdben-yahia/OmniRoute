# Launch Windsurf with Chrome DevTools Protocol enabled
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Launch Windsurf with CDP Enabled" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Closing existing Windsurf instances..." -ForegroundColor Yellow
$windsurfProcesses = Get-Process -Name "Windsurf" -ErrorAction SilentlyContinue
if ($windsurfProcesses) {
    $windsurfProcesses | Stop-Process -Force
    Start-Sleep -Seconds 3
    Write-Host "      Closed all Windsurf instances" -ForegroundColor Green
} else {
    Write-Host "      No Windsurf instances running" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[2/3] Launching Windsurf with CDP on port 9222..." -ForegroundColor Yellow
$windsurfPath = "C:\Users\amine\AppData\Local\Programs\Windsurf\Windsurf.exe"
if (Test-Path $windsurfPath) {
    Start-Process -FilePath $windsurfPath -ArgumentList "--remote-debugging-port=9222"
    Write-Host "      Windsurf launched with CDP enabled" -ForegroundColor Green
} else {
    Write-Host "      Windsurf.exe not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/3] Waiting for CDP to be available..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$cdpAvailable = $false
while (($attempt -lt $maxAttempts) -and (-not $cdpAvailable)) {
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:9222/json" -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $cdpAvailable = $true
            Write-Host "      CDP is available on port 9222" -ForegroundColor Green
        }
    } catch {
        Write-Host "      Attempt $attempt/$maxAttempts - Waiting..." -ForegroundColor Gray
        Start-Sleep -Seconds 1
    }
}

if (-not $cdpAvailable) {
    Write-Host "      CDP not available after $maxAttempts seconds" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Windsurf is ready with CDP!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
