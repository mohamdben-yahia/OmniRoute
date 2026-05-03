$ErrorActionPreference = 'Stop'
$CaptureDir = 'C:\Users\amine\OmniRoute\tmp_windsurf_capture'
$ProfileDir = Join-Path $CaptureDir 'windsurf-profile-nodehook'
$WindsurfExe = 'C:\Users\amine\AppData\Local\Programs\Windsurf\Windsurf.exe'
$HookFile = Join-Path $CaptureDir 'node_request_hook.js'
$HookOut = Join-Path $CaptureDir 'node-hook.jsonl'

New-Item -ItemType Directory -Force -Path $CaptureDir | Out-Null
New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null
if (Test-Path $HookOut) { Remove-Item $HookOut -Force }

$env:NODE_OPTIONS = '--require=' + $HookFile
$env:WINDSURF_HOOK_OUT = $HookOut
$env:NODE_TLS_REJECT_UNAUTHORIZED = '0'
$env:ELECTRON_ENABLE_LOGGING = '1'

$windsurfArgs = @(
  '--user-data-dir=' + $ProfileDir,
  '--ignore-certificate-errors'
)

$windsurf = Start-Process -FilePath $WindsurfExe -ArgumentList $windsurfArgs -PassThru
Write-Host ('Windsurf PID=' + $windsurf.Id)
Write-Host ('Hook output=' + $HookOut)
Write-Host 'If requests run through Node/Electron utility processes inheriting NODE_OPTIONS, they will be logged here.'
