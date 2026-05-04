# Test whether complete metadata envelope (userId, teamId, f) unlocks StartCascade
# Run this after a fresh Windsurf session is active

# Values from accepted HAR StartCascade request (fiddler/new.har)
$env:WINDSURF_USER_ID = "user-47ba71096f0b498daaf30bd1b11a9b6b"
$env:WINDSURF_TEAM_ID = "devin-team`$account-ae790c86db964e3f9c0296307fcf4691"
$env:WINDSURF_METADATA_F = [char]0x00 + [char]0x01 + [char]0x03

# Session ID must be updated to match the current live runtime
# Check tmp_windsurf_runtime_ls_binding.json for the current session_id
if (-not $env:WINDSURF_SESSION_ID) {
    Write-Host "ERROR: Set WINDSURF_SESSION_ID first" -ForegroundColor Red
    Write-Host "Check tmp_windsurf_runtime_ls_binding.json for current session_id"
    Write-Host ""
    Write-Host "Example:"
    Write-Host '  $env:WINDSURF_SESSION_ID = "18996"'
    Write-Host '  .\scripts\test_complete_metadata.ps1'
    exit 1
}

# CSRF token and LS URL are read from windsurf-live-bootstrap.json by the probe
# Make sure that file has fresh values for the current session before running

Write-Host "Testing StartCascade with complete metadata envelope..." -ForegroundColor Cyan
Write-Host "  userId: $env:WINDSURF_USER_ID"
Write-Host "  teamId: $env:WINDSURF_TEAM_ID"
Write-Host "  f: (3 bytes)"
Write-Host "  sessionId: $env:WINDSURF_SESSION_ID"
Write-Host ""

python scripts/windsurf_direct_probe.py
