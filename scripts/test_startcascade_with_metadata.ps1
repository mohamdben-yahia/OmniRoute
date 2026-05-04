#!/usr/bin/env pwsh
# Test StartCascade with complete metadata from HAR

# Set the extracted metadata fields
$env:WINDSURF_USER_ID = 'user-47ba71096f0b498daaf30bd1b11a9b6b'
$env:WINDSURF_METADATA_F = '000103'  # hex format
$env:WINDSURF_TEAM_ID = 'devin-team$account-ae790c86db964e3f9c0296307fcf4691'

# Read bootstrap for current runtime state
$bootstrap = Get-Content "windsurf-live-bootstrap.json" | ConvertFrom-Json

Write-Host "Testing StartCascade with complete metadata..." -ForegroundColor Cyan
Write-Host "  User ID: $env:WINDSURF_USER_ID" -ForegroundColor Gray
Write-Host "  Team ID: $env:WINDSURF_TEAM_ID" -ForegroundColor Gray
Write-Host "  Field f: $env:WINDSURF_METADATA_F" -ForegroundColor Gray
Write-Host "  CSRF Token: $($bootstrap.csrfToken)" -ForegroundColor Gray
Write-Host "  LS Port: $($bootstrap.languageServerPort)" -ForegroundColor Gray
Write-Host ""

# Run the probe with StartCascade
python scripts/windsurf_direct_probe.py `
    --mode start_cascade `
    --bootstrap-file windsurf-live-bootstrap.json `
    --verbose
