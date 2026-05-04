# Launch Windsurf with Chrome DevTools Protocol enabled.
# This script closes existing Windsurf instances and relaunches with CDP on port 9222.

$ErrorActionPreference = "Stop"

function Write-Step {
    param(
        [string]$Message,
        [string]$Color = "Gray"
    )

    Write-Host $Message -ForegroundColor $Color
}

Write-Step "========================================" "Cyan"
Write-Step "  Launch Windsurf with CDP Enabled" "Cyan"
Write-Step "========================================" "Cyan"
Write-Step ""

$windsurfPath = "C:\Users\amine\AppData\Local\Programs\Windsurf\Windsurf.exe"
$cdpUrl = "http://127.0.0.1:9222/json/version"

Write-Step "[1/3] Closing existing Windsurf instances..." "Yellow"
$windsurfProcesses = Get-Process -Name "Windsurf" -ErrorAction SilentlyContinue

if ($windsurfProcesses) {
    Write-Step "      Found $($windsurfProcesses.Count) Windsurf process(es)" "Gray"
    $windsurfProcesses | Stop-Process -Force
    Start-Sleep -Seconds 4
    Write-Step "      [OK] Closed all Windsurf instances" "Green"
} else {
    Write-Step "      No Windsurf instances running" "Gray"
}

if (-not (Test-Path $windsurfPath)) {
    Write-Step "      [ERROR] Windsurf.exe not found at: $windsurfPath" "Red"
    exit 1
}

Write-Step ""
Write-Step "[2/3] Launching Windsurf with CDP on port 9222..." "Yellow"
Start-Process -FilePath $windsurfPath -ArgumentList "--remote-debugging-port=9222"
Write-Step "      [OK] Windsurf launch requested" "Green"

Write-Step ""
Write-Step "[3/3] Waiting for CDP to be available..." "Yellow"
$maxAttempts = 30
$attempt = 0
$cdpAvailable = $false

while (($attempt -lt $maxAttempts) -and (-not $cdpAvailable)) {
    $attempt += 1

    try {
        $response = Invoke-WebRequest -Uri $cdpUrl -TimeoutSec 2 -UseBasicParsing

        if ($response.StatusCode -eq 200) {
            $cdpAvailable = $true
            Write-Step "      [OK] CDP is available on port 9222" "Green"
            break
        }
    }
    catch {
        Write-Step "      Attempt $attempt/$maxAttempts - Waiting..." "Gray"
        Start-Sleep -Seconds 1
    }
}

if (-not $cdpAvailable) {
    Write-Step "      [ERROR] CDP not available after $maxAttempts seconds" "Red"
    Write-Step ""
    Write-Step "Troubleshooting:" "Yellow"
    Write-Step "  1. Check if Windsurf is running: Get-Process -Name Windsurf" "Gray"
    Write-Step "  2. Check if port 9222 is listening: netstat -ano | findstr 9222" "Gray"
    Write-Step "  3. If Windsurf was already open, close it completely and rerun this script" "Gray"
    exit 1
}

Write-Step ""
Write-Step "========================================" "Green"
Write-Step "  [OK] Windsurf is ready with CDP" "Green"
Write-Step "========================================" "Green"
Write-Step ""
Write-Step "Next steps:" "Cyan"
Write-Step "  1. python windsurf_token_extractor.py --extract-all --output tokens.json" "Gray"
Write-Step "  2. python windsurf_authenticated_probe.py --tokens tokens.json --test-start-cascade" "Gray"
Write-Step "  3. python windsurf_auth_test_suite.py" "Gray"
Write-Step ""
