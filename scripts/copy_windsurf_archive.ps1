# Windsurf Files Copy Script - Professional Archive
# Date: 2026-05-03T18:17:48Z
# Purpose: Copy all Windsurf-related files to professional archive structure

$ErrorActionPreference = "Continue"
$baseDir = "C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest"

Write-Host "=== Windsurf Professional Archive Copy ===" -ForegroundColor Cyan
Write-Host "Destination: $baseDir" -ForegroundColor Yellow
Write-Host ""

# Create directory structure
Write-Host "Creating directory structure..." -ForegroundColor Green
$directories = @(
    "$baseDir\01-application",
    "$baseDir\02-user-data\logs",
    "$baseDir\02-user-data\storage",
    "$baseDir\02-user-data\config",
    "$baseDir\02-user-data\cache",
    "$baseDir\03-captures\tokens",
    "$baseDir\03-captures\network",
    "$baseDir\03-captures\cdp",
    "$baseDir\03-captures\har",
    "$baseDir\04-investigation\scripts",
    "$baseDir\04-investigation\reports",
    "$baseDir\04-investigation\analysis",
    "$baseDir\05-temp",
    "$baseDir\06-documentation"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=== Copying Files ===" -ForegroundColor Cyan
Write-Host ""

# Function to copy with progress
function Copy-WithProgress {
    param(
        [string]$Source,
        [string]$Destination,
        [string]$Description
    )

    if (Test-Path $Source) {
        Write-Host "Copying: $Description" -ForegroundColor Yellow
        Write-Host "  From: $Source" -ForegroundColor Gray
        Write-Host "  To: $Destination" -ForegroundColor Gray

        try {
            Copy-Item -Path $Source -Destination $Destination -Recurse -Force -ErrorAction Stop
            Write-Host "  Success" -ForegroundColor Green
        } catch {
            Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        }
        Write-Host ""
    } else {
        Write-Host "Skipping: $Description (not found)" -ForegroundColor DarkGray
        Write-Host "  Path: $Source" -ForegroundColor DarkGray
        Write-Host ""
    }
}

# 1. Application Files
Write-Host "[1/7] Application Files" -ForegroundColor Cyan
Copy-WithProgress -Source "C:\Users\amine\AppData\Local\Programs\Windsurf\Windsurf.exe" -Destination "$baseDir\01-application\" -Description "Windsurf executable"
Copy-WithProgress -Source "C:\Users\amine\AppData\Local\Programs\Windsurf\resources" -Destination "$baseDir\01-application\resources" -Description "Windsurf resources"

# 2. User Data - Logs
Write-Host "[2/7] User Data - Logs" -ForegroundColor Cyan
Copy-WithProgress -Source "C:\Users\amine\AppData\Roaming\Windsurf\logs" -Destination "$baseDir\02-user-data\logs\roaming" -Description "Roaming logs"
Copy-WithProgress -Source "C:\Users\amine\AppData\Local\Windsurf\logs" -Destination "$baseDir\02-user-data\logs\local" -Description "Local logs"

# 3. User Data - Storage
Write-Host "[3/7] User Data - Storage" -ForegroundColor Cyan
Copy-WithProgress -Source "C:\Users\amine\AppData\Roaming\Windsurf\Local Storage" -Destination "$baseDir\02-user-data\storage\local-storage" -Description "Local Storage LevelDB"
Copy-WithProgress -Source "C:\Users\amine\AppData\Roaming\Windsurf\Session Storage" -Destination "$baseDir\02-user-data\storage\session-storage" -Description "Session Storage"
Copy-WithProgress -Source "C:\Users\amine\AppData\Roaming\Windsurf\User\globalStorage" -Destination "$baseDir\02-user-data\storage\global-storage" -Description "Global Storage"

# 4. User Data - Config
Write-Host "[4/7] User Data - Config" -ForegroundColor Cyan
Copy-WithProgress -Source "C:\Users\amine\AppData\Roaming\Windsurf\User\settings.json" -Destination "$baseDir\02-user-data\config\" -Description "User settings"
Copy-WithProgress -Source "C:\Users\amine\AppData\Roaming\Windsurf\User\keybindings.json" -Destination "$baseDir\02-user-data\config\" -Description "Keybindings"

# 5. Captures - Tokens
Write-Host "[5/7] Captures - Tokens and Network" -ForegroundColor Cyan
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_captured_tokens.json" -Destination "$baseDir\03-captures\tokens\" -Description "Captured tokens"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_capture_log.txt" -Destination "$baseDir\03-captures\tokens\" -Description "Capture log"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_tokens.json" -Destination "$baseDir\03-captures\tokens\" -Description "Tokens JSON"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_inspector_tokens.json" -Destination "$baseDir\03-captures\tokens\" -Description "Inspector tokens"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_leveldb_tokens.json" -Destination "$baseDir\03-captures\tokens\" -Description "LevelDB tokens"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_memory_tokens.json" -Destination "$baseDir\03-captures\tokens\" -Description "Memory tokens"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\AUTHTOKENWIND" -Destination "$baseDir\03-captures\tokens\" -Description "Auth token file"

# Captures - Network
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-auth-runtime-capture.jsonl" -Destination "$baseDir\03-captures\network\" -Description "Auth runtime capture"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-electron-lifecycle-trace.jsonl" -Destination "$baseDir\03-captures\network\" -Description "Electron lifecycle trace"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-live-request-capture.jsonl" -Destination "$baseDir\03-captures\network\" -Description "Live request capture"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-model-runtime-capture.jsonl" -Destination "$baseDir\03-captures\network\" -Description "Model runtime capture"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-acp-session-load-probe.json" -Destination "$baseDir\03-captures\network\" -Description "ACP session load probe"

# 6. Investigation - Scripts
Write-Host "[6/7] Investigation - Scripts and Reports" -ForegroundColor Cyan

$scriptFiles = Get-ChildItem "C:\Users\amine\OmniRoute\scripts\windsurf_*.py" -ErrorAction SilentlyContinue
foreach ($file in $scriptFiles) {
    Copy-WithProgress -Source $file.FullName -Destination "$baseDir\04-investigation\scripts\" -Description "Script: $($file.Name)"
}

$psScripts = Get-ChildItem "C:\Users\amine\OmniRoute\scripts\*windsurf*.ps1" -ErrorAction SilentlyContinue
foreach ($file in $psScripts) {
    Copy-WithProgress -Source $file.FullName -Destination "$baseDir\04-investigation\scripts\" -Description "Script: $($file.Name)"
}

$mjsScripts = Get-ChildItem "C:\Users\amine\OmniRoute\scripts\*windsurf*.mjs" -ErrorAction SilentlyContinue
foreach ($file in $mjsScripts) {
    Copy-WithProgress -Source $file.FullName -Destination "$baseDir\04-investigation\scripts\" -Description "Script: $($file.Name)"
}

$cjsScripts = Get-ChildItem "C:\Users\amine\OmniRoute\scripts\*windsurf*.cjs" -ErrorAction SilentlyContinue
foreach ($file in $cjsScripts) {
    Copy-WithProgress -Source $file.FullName -Destination "$baseDir\04-investigation\scripts\" -Description "Script: $($file.Name)"
}

# Investigation - Reports
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_AUTH_INVESTIGATION_SUMMARY.md" -Destination "$baseDir\04-investigation\reports\" -Description "Auth investigation summary"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_AUTH_FINAL_SUMMARY.md" -Destination "$baseDir\04-investigation\reports\" -Description "Auth final summary"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\STEP AUTH" -Destination "$baseDir\04-investigation\reports\" -Description "Step auth file"

# 7. Temporary Files
Write-Host "[7/7] Temporary Files" -ForegroundColor Cyan

$tmpFiles = Get-ChildItem "C:\Users\amine\OmniRoute\tmp_*windsurf*" -ErrorAction SilentlyContinue
foreach ($file in $tmpFiles) {
    Copy-WithProgress -Source $file.FullName -Destination "$baseDir\05-temp\" -Description "Temp: $($file.Name)"
}

Copy-WithProgress -Source "C:\Users\amine\OmniRoute\tmp" -Destination "$baseDir\05-temp\tmp-directory" -Description "Tmp directory"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\tmp_windsurf_capture" -Destination "$baseDir\05-temp\tmp-windsurf-capture" -Description "Windsurf capture temp"

# 8. Documentation
Write-Host "[8/8] Documentation" -ForegroundColor Cyan

$docFiles = Get-ChildItem "C:\Users\amine\OmniRoute\docs\windsurf-*.md" -ErrorAction SilentlyContinue
foreach ($file in $docFiles) {
    Copy-WithProgress -Source $file.FullName -Destination "$baseDir\06-documentation\" -Description "Doc: $($file.Name)"
}

Copy-WithProgress -Source "C:\Users\amine\OmniRoute\QUICKSTART-TOKEN-CAPTURE.md" -Destination "$baseDir\06-documentation\" -Description "Quick start guide"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\docs\SESSION-COMPLETE-2026-05-03.md" -Destination "$baseDir\06-documentation\" -Description "Session complete"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\docs\session-summary-2026-05-03.md" -Destination "$baseDir\06-documentation\" -Description "Session summary"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\docs\session-final-status-2026-05-03.md" -Destination "$baseDir\06-documentation\" -Description "Session final status"

# Generate inventory
Write-Host ""
Write-Host "=== Generating Inventory ===" -ForegroundColor Cyan

$allFiles = Get-ChildItem -Path $baseDir -Recurse -File
$inventory = "# Windsurf Archive Inventory`n"
$inventory += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n`n"
$inventory += "## Directory Structure`n`n"

$grouped = $allFiles | Group-Object Directory
foreach ($group in $grouped) {
    $relativePath = $group.Name.Replace($baseDir, "").TrimStart('\')
    $inventory += "### $relativePath`n"
    $inventory += "Files: $($group.Count)`n"
    foreach ($file in $group.Group) {
        $size = if ($file.Length -gt 1MB) { "{0:N2} MB" -f ($file.Length / 1MB) }
                elseif ($file.Length -gt 1KB) { "{0:N2} KB" -f ($file.Length / 1KB) }
                else { "$($file.Length) bytes" }
        $inventory += "- $($file.Name) ($size)`n"
    }
    $inventory += "`n"
}

$inventory | Out-File "$baseDir\INVENTORY.txt" -Encoding UTF8

Write-Host ""
Write-Host "=== Copy Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Archive location: $baseDir" -ForegroundColor Yellow
Write-Host "Inventory file: $baseDir\INVENTORY.txt" -ForegroundColor Yellow
Write-Host ""

# Summary statistics
$totalFiles = $allFiles.Count
$totalSize = ($allFiles | Measure-Object -Property Length -Sum).Sum
$totalSizeMB = [math]::Round($totalSize / 1MB, 2)

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Total files: $totalFiles" -ForegroundColor White
Write-Host "  Total size: $totalSizeMB MB" -ForegroundColor White
Write-Host ""
Write-Host "Archive ready for analysis" -ForegroundColor Green
