# Test multiple models with Windsurf direct probe
# Tests GPT-5.4 and Claude with "hello" message

$models = @(
    @{name="gpt-5.4"; uid="gpt-5.4"},
    @{name="claude-opus-4"; uid="claude-opus-4-20250514"},
    @{name="claude-sonnet-4"; uid="claude-sonnet-4-20250514"}
)

$results = @()

foreach ($model in $models) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Testing model: $($model.name)" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    $env:WINDSURF_CHAT_MODEL_NAME = $model.uid
    $env:WINDSURF_CHAT_TEXT = "hello"

    $output = python scripts/windsurf_direct_probe.py 2>&1 | Out-String

    try {
        $json = $output | ConvertFrom-Json
        $results += @{
            model = $model.name
            modelUid = $model.uid
            status = $json.sendUserCascadeMessage.status
            assignModelStatus = $json.assignModel.status
            success = ($json.sendUserCascadeMessage.status -eq 200)
        }

        Write-Host "Status: $($json.sendUserCascadeMessage.status)" -ForegroundColor $(if ($json.sendUserCascadeMessage.status -eq 200) { "Green" } else { "Yellow" })
        if ($json.assignModel.status -ne 200) {
            Write-Host "AssignModel Status: $($json.assignModel.status)" -ForegroundColor Yellow
            if ($json.assignModel.body.message) {
                Write-Host "Error: $($json.assignModel.body.message)" -ForegroundColor Red
            }
        }
    }
    catch {
        Write-Host "Failed to parse JSON output" -ForegroundColor Red
        Write-Host $output
        $results += @{
            model = $model.name
            modelUid = $model.uid
            status = "error"
            assignModelStatus = "error"
            success = $false
        }
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

foreach ($result in $results) {
    $statusColor = if ($result.success) { "Green" } else { "Red" }
    Write-Host "$($result.model): " -NoNewline
    Write-Host "$($result.status)" -ForegroundColor $statusColor
}
