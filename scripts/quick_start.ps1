# Windsurf Authentication Toolkit - Quick Start Script
# This script automates the entire testing workflow
# Author: OmniRoute Research Team
# Date: 2026-05-02
# Version: 1.0.0

param(
    [switch]$SkipWindsurfLaunch,
    [switch]$Verbose,
    [switch]$Help
)

# Color functions
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Header { 
    param($Message)
    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor Blue
    Write-Host $Message.PadLeft(($Message.Length + 70) / 2) -ForegroundColor Blue
    Write-Host "=" * 70 -ForegroundColor Blue
    Write-Host ""
}

# Show help
if ($Help) {
    Write-Header "WINDSURF AUTHENTICATION TOOLKIT - QUICK START"
    Write-Host "Usage: .\quick_start.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SkipWindsurfLaunch    Skip Windsurf launch (if already running with CDP)"
    Write-Host "  -Verbose               Show detailed output"
    Write-Host "  -Help                  Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\quick_start.ps1                    # Full workflow"
    Write-Host "  .\quick_start.ps1 -SkipWindsurfLaunch # Skip Windsurf launch"
    Write-Host "  .\quick_start.ps1 -Verbose           # Verbose output"
    Write-Host ""
    exit 0
}

Write-Header "🚀 WINDSURF AUTHENTICATION TOOLKIT - QUICK START"

# Step 1: Verify setup
Write-Info "Step 1/5: Verifying setup..."
$verifyResult = python verify_setup.py 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "Setup verification passed"
} else {
    Write-Warning "Setup verification found issues (this is normal if CDP is not running yet)"
}

if ($Verbose) {
    Write-Host $verifyResult
}

# Step 2: Launch Windsurf with CDP (unless skipped)
if (-not $SkipWindsurfLaunch) {
    Write-Info "Step 2/5: Launching Windsurf with CDP..."
    
    # Check if Windsurf is already running
    $windsurfProcesses = Get-Process -Name "Windsurf" -ErrorAction SilentlyContinue
    if ($windsurfProcesses) {
        Write-Warning "Windsurf is already running. Closing it first..."
        $windsurfProcesses | Stop-Process -Force
        Start-Sleep -Seconds 3
    }
    
    # Launch Windsurf with CDP
    $windsurfPath = "C:\Users\amine\AppData\Local\Programs\Windsurf\Windsurf.exe"
    if (Test-Path $windsurfPath) {
        Write-Info "Launching Windsurf with --remote-debugging-port=9222..."
        Start-Process -FilePath $windsurfPath -ArgumentList "--remote-debugging-port=9222"
        
        Write-Info "Waiting 15 seconds for Windsurf to start..."
        Start-Sleep -Seconds 15
        
        Write-Success "Windsurf launched"
    } else {
        Write-Error "Windsurf executable not found at: $windsurfPath"
        Write-Warning "Please launch Windsurf manually with: Windsurf.exe --remote-debugging-port=9222"
        Write-Host ""
        Read-Host "Press Enter when Windsurf is running with CDP"
    }
} else {
    Write-Info "Step 2/5: Skipping Windsurf launch (--SkipWindsurfLaunch flag)"
}

# Step 3: Verify CDP is available
Write-Info "Step 3/5: Verifying CDP availability..."
$maxRetries = 5
$retryCount = 0
$cdpAvailable = $false

while ($retryCount -lt $maxRetries -and -not $cdpAvailable) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:9222/json" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $cdpAvailable = $true
            Write-Success "CDP is available on port 9222"
        }
    } catch {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Warning "CDP not available yet. Retrying in 5 seconds... ($retryCount/$maxRetries)"
            Start-Sleep -Seconds 5
        }
    }
}

if (-not $cdpAvailable) {
    Write-Error "CDP is not available after $maxRetries attempts"
    Write-Warning "Please ensure Windsurf is running with: Windsurf.exe --remote-debugging-port=9222"
    Write-Host ""
    Write-Host "Manual steps:"
    Write-Host "1. Close all Windsurf processes: Get-Process -Name 'Windsurf' | Stop-Process -Force"
    Write-Host "2. Launch with CDP: & 'C:\Users\amine\AppData\Local\Programs\Windsurf\Windsurf.exe' --remote-debugging-port=9222"
    Write-Host "3. Wait 15 seconds"
    Write-Host "4. Run this script again with: .\quick_start.ps1 -SkipWindsurfLaunch"
    Write-Host ""
    exit 1
}

# Step 4: Extract tokens
Write-Info "Step 4/5: Extracting authentication tokens..."
$extractResult = python windsurf_token_extractor.py --extract-all --output tokens.json 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "Tokens extracted successfully"
    
    # Verify tokens.json exists and has content
    if (Test-Path "tokens.json") {
        $tokensContent = Get-Content "tokens.json" -Raw | ConvertFrom-Json
        if ($tokensContent.sessionId -and $tokensContent.csrfToken) {
            Write-Success "Found sessionId: $($tokensContent.sessionId)"
            Write-Success "Found csrfToken: $($tokensContent.csrfToken)"
        } else {
            Write-Warning "tokens.json exists but may be incomplete"
        }
    }
} else {
    Write-Error "Token extraction failed"
    if ($Verbose) {
        Write-Host $extractResult
    }
    exit 1
}

if ($Verbose) {
    Write-Host $extractResult
}

# Step 5: Run authentication tests
Write-Info "Step 5/5: Running authentication tests..."
$testResult = python windsurf_auth_test_suite.py 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "All tests passed!"
} else {
    Write-Warning "Some tests failed. See output above for details."
}

if ($Verbose) {
    Write-Host $testResult
}

# Summary
Write-Header "📊 QUICK START SUMMARY"

Write-Host "Workflow completed. Results:"
Write-Host ""
Write-Host "1. Setup verification: " -NoNewline
if ($verifyResult -match "✅") { Write-Success "PASS" } else { Write-Warning "PARTIAL" }

Write-Host "2. Windsurf launch: " -NoNewline
if ($SkipWindsurfLaunch) { Write-Info "SKIPPED" } else { Write-Success "DONE" }

Write-Host "3. CDP availability: " -NoNewline
if ($cdpAvailable) { Write-Success "AVAILABLE" } else { Write-Error "NOT AVAILABLE" }

Write-Host "4. Token extraction: " -NoNewline
if (Test-Path "tokens.json") { Write-Success "SUCCESS" } else { Write-Error "FAILED" }

Write-Host "5. Authentication tests: " -NoNewline
if ($LASTEXITCODE -eq 0) { Write-Success "PASSED" } else { Write-Warning "FAILED" }

Write-Host ""
Write-Host "Next steps:"
Write-Host "  • Review test results above"
Write-Host "  • Check MANUAL_TEST_GUIDE.md for detailed testing"
Write-Host "  • See INTEGRATION_GUIDE.md for OmniRoute integration"
Write-Host "  • Run 'python cleanup.py --tokens' to clean up tokens.json"
Write-Host ""

Write-Info "For more information, see README.md or run: python windsurf_quick_start.py --help"
Write-Host ""
