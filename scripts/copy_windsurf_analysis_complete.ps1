# Windsurf Analysis Files Complete Copy Script
# Date: 2026-05-03T23:16:20Z
# Purpose: Copy ALL remaining Windsurf analysis, test, and research files to archive

$ErrorActionPreference = "Continue"
$baseDir = "C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest"

Write-Host "=== Windsurf Analysis Files Complete Copy ===" -ForegroundColor Cyan
Write-Host "Destination: $baseDir" -ForegroundColor Yellow
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

Write-Host "[1/5] Root-level Analysis Files" -ForegroundColor Cyan

# Root-level Windsurf files
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\.env.windsurf.local" -Destination "$baseDir\04-investigation\analysis\" -Description "Windsurf local env"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\extract_windsurf_response.py" -Destination "$baseDir\04-investigation\scripts\" -Description "Extract response script"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\test_windsurf_hello_response.py" -Destination "$baseDir\04-investigation\scripts\" -Description "Test hello response"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\tmp-windsurf-runtime-check.mjs" -Destination "$baseDir\05-temp\" -Description "Runtime check script"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_node_inspector_helper.py" -Destination "$baseDir\04-investigation\scripts\" -Description "Node inspector helper"

# Windsurf JSON captures
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-acp-capture-restored-env.json" -Destination "$baseDir\03-captures\network\" -Description "ACP capture restored env"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-acp-capture.json" -Destination "$baseDir\03-captures\network\" -Description "ACP capture"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-acp-runtime-probe.json" -Destination "$baseDir\03-captures\network\" -Description "ACP runtime probe"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-acp-status-after-auth.json" -Destination "$baseDir\03-captures\network\" -Description "ACP status after auth"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-live-bootstrap.json" -Destination "$baseDir\03-captures\network\" -Description "Live bootstrap"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-model-architecture-evidence.json" -Destination "$baseDir\03-captures\network\" -Description "Model architecture evidence"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-model-runtime-launch.json" -Destination "$baseDir\03-captures\network\" -Description "Model runtime launch"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-model-runtime-report.json" -Destination "$baseDir\03-captures\network\" -Description "Model runtime report"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-model-targeted-evidence.json" -Destination "$baseDir\03-captures\network\" -Description "Model targeted evidence"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_api_analysis.json" -Destination "$baseDir\03-captures\network\" -Description "API analysis"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_endpoint_discovery.json" -Destination "$baseDir\03-captures\network\" -Description "Endpoint discovery"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_network_monitor.json" -Destination "$baseDir\03-captures\network\" -Description "Network monitor"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_probe_final_run.json" -Destination "$baseDir\03-captures\network\" -Description "Probe final run"

# Windsurf log files
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-direct-launch.log" -Destination "$baseDir\03-captures\network\" -Description "Direct launch log"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-hook-launch.log" -Destination "$baseDir\03-captures\network\" -Description "Hook launch log"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf-noop-launch.log" -Destination "$baseDir\03-captures\network\" -Description "Noop launch log"

# Windsurf binary files
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_model_response.bin" -Destination "$baseDir\03-captures\network\" -Description "Model response binary"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_response_new.bin" -Destination "$baseDir\03-captures\network\" -Description "Response new binary"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_send_message.bin" -Destination "$baseDir\03-captures\network\" -Description "Send message binary"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\windsurf_start_cascade.bin" -Destination "$baseDir\03-captures\network\" -Description "Start cascade binary"

Write-Host "[2/5] Root-level Documentation" -ForegroundColor Cyan

# Root-level Windsurf documentation
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_API_INVESTIGATION_FINAL_REPORT.md" -Destination "$baseDir\06-documentation\" -Description "API investigation final report"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_API_TESTING_GUIDE.md" -Destination "$baseDir\06-documentation\" -Description "API testing guide"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_ASSIGNMODEL_INVESTIGATION.md" -Destination "$baseDir\06-documentation\" -Description "AssignModel investigation"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_AUTH_INVESTIGATION_COMPLETE.md" -Destination "$baseDir\06-documentation\" -Description "Auth investigation complete"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_AUTH_PROTOCOL.md" -Destination "$baseDir\06-documentation\" -Description "Auth protocol"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_DOCUMENTATION_INDEX.md" -Destination "$baseDir\06-documentation\" -Description "Documentation index"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_INVESTIGATION_FINAL_SUMMARY.md" -Destination "$baseDir\06-documentation\" -Description "Investigation final summary"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_INVESTIGATION_INDEX.md" -Destination "$baseDir\06-documentation\" -Description "Investigation index"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_PROBE_COMPLETE.md" -Destination "$baseDir\06-documentation\" -Description "Probe complete"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_PROBE_FINAL_STATUS.md" -Destination "$baseDir\06-documentation\" -Description "Probe final status"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_PROBE_QUICKSTART.md" -Destination "$baseDir\06-documentation\" -Description "Probe quickstart"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_PROBE_VERIFICATION_2026-05-03.md" -Destination "$baseDir\06-documentation\" -Description "Probe verification"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_QUICKSTART.md" -Destination "$baseDir\06-documentation\" -Description "Quickstart"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\WINDSURF_QUICK_REFERENCE.md" -Destination "$baseDir\06-documentation\" -Description "Quick reference"

Write-Host "[3/5] Docs Subdirectory Files" -ForegroundColor Cyan

# Additional docs files
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\docs\README-windsurf-investigation.md" -Destination "$baseDir\06-documentation\" -Description "README windsurf investigation"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\docs\show-windsurf-report.ps1" -Destination "$baseDir\04-investigation\scripts\" -Description "Show windsurf report script"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\docs\windsurf-auth-capture-action-plan.md" -Destination "$baseDir\06-documentation\" -Description "Auth capture action plan"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\docs\windsurf-investigation-summary.txt" -Destination "$baseDir\06-documentation\" -Description "Investigation summary txt"

# Superpowers plans and specs
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\docs\superpowers\plans\2026-04-25-windsurf-experimental-auth.md" -Destination "$baseDir\06-documentation\" -Description "Experimental auth plan"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\docs\superpowers\plans\2026-04-29-windsurf-runtime-trace.md" -Destination "$baseDir\06-documentation\" -Description "Runtime trace plan"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\docs\superpowers\specs\2026-04-25-windsurf-experimental-auth-design.md" -Destination "$baseDir\06-documentation\" -Description "Experimental auth design"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\docs\superpowers\specs\2026-04-29-windsurf-runtime-trace-design.md" -Destination "$baseDir\06-documentation\" -Description "Runtime trace design"

# Superpowers reports
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\docs\superpowers\reports" -Destination "$baseDir\06-documentation\superpowers-reports" -Description "Superpowers reports directory"

Write-Host "[4/5] Scripts Subdirectory Files" -ForegroundColor Cyan

# Scripts scratch directory
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\scripts\scratch\launch-windsurf-native-capture.ps1" -Destination "$baseDir\04-investigation\scripts\" -Description "Launch native capture"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\scripts\scratch\normalize-windsurf-native-capture.mjs" -Destination "$baseDir\04-investigation\scripts\" -Description "Normalize native capture"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\scripts\scratch\repair-windsurf-deburr.mjs" -Destination "$baseDir\04-investigation\scripts\" -Description "Repair deburr"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\scripts\scratch\run-windsurf-with-model-hook.mjs" -Destination "$baseDir\04-investigation\scripts\" -Description "Run with model hook"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\scripts\scratch\windsurf-acp-runtime-probe.mjs" -Destination "$baseDir\04-investigation\scripts\" -Description "ACP runtime probe mjs"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\scripts\scratch\windsurf-model-architecture-probe.mjs" -Destination "$baseDir\04-investigation\scripts\" -Description "Model architecture probe"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\scripts\scratch\windsurf-model-runtime-hook.cjs" -Destination "$baseDir\04-investigation\scripts\" -Description "Model runtime hook"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\scripts\scratch\windsurf-targeted-extract.mjs" -Destination "$baseDir\04-investigation\scripts\" -Description "Targeted extract"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\scripts\scratch\windsurf-trace-context.cjs" -Destination "$baseDir\04-investigation\scripts\" -Description "Trace context"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\scripts\scratch\windsurf-trace-report.cjs" -Destination "$baseDir\04-investigation\scripts\" -Description "Trace report"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\scripts\scratch\windsurf_ip_probe.py" -Destination "$baseDir\04-investigation\scripts\" -Description "IP probe"
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\scripts\scratch\windsurf_multi_endpoint_probe.py" -Destination "$baseDir\04-investigation\scripts\" -Description "Multi endpoint probe"

Write-Host "[5/5] Artifacts Directory" -ForegroundColor Cyan

# Artifacts windsurf-native directory (complete)
Copy-WithProgress -Source "C:\Users\amine\OmniRoute\artifacts\windsurf-native" -Destination "$baseDir\04-investigation\artifacts-windsurf-native" -Description "Complete windsurf-native artifacts"

Write-Host ""
Write-Host "=== Regenerating Inventory ===" -ForegroundColor Cyan

# Regenerate inventory
$allFiles = Get-ChildItem -Path $baseDir -Recurse -File
$inventory = "# Windsurf Archive Inventory (Updated)`n"
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
Write-Host "Updated inventory: $baseDir\INVENTORY.txt" -ForegroundColor Yellow
Write-Host ""

# Summary statistics
$totalFiles = $allFiles.Count
$totalSize = ($allFiles | Measure-Object -Property Length -Sum).Sum
$totalSizeMB = [math]::Round($totalSize / 1MB, 2)

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Total files: $totalFiles" -ForegroundColor White
Write-Host "  Total size: $totalSizeMB MB" -ForegroundColor White
Write-Host ""
Write-Host "All analysis and research files archived" -ForegroundColor Green
