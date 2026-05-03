$ErrorActionPreference = 'Stop'
$CaptureDir = 'C:\Users\amine\OmniRoute\tmp_windsurf_capture'
$MitmBin = 'C:\Program Files\mitmproxy\bin\mitmdump.exe'
$MitmScript = Join-Path $CaptureDir 'mitm_dump.py'
$TrafficFile = Join-Path $CaptureDir 'traffic.jsonl'
$MitmStdout = Join-Path $CaptureDir 'mitmproxy.stdout.log'
$MitmStderr = Join-Path $CaptureDir 'mitmproxy.stderr.log'
$ProfileDir = Join-Path $CaptureDir 'windsurf-profile'
$WindsurfExe = 'C:\Users\amine\AppData\Local\Programs\Windsurf\Windsurf.exe'
$Proxy = '127.0.0.1:8080'

New-Item -ItemType Directory -Force -Path $CaptureDir | Out-Null
New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null
if (Test-Path $TrafficFile) { Remove-Item $TrafficFile -Force }
if (Test-Path $MitmStdout) { Remove-Item $MitmStdout -Force }
if (Test-Path $MitmStderr) { Remove-Item $MitmStderr -Force }

$env:WINDSURF_MITM_OUT = $TrafficFile
$mitm = Start-Process -FilePath $MitmBin -ArgumentList @('-q', '-p', '8080', '-s', $MitmScript) -RedirectStandardOutput $MitmStdout -RedirectStandardError $MitmStderr -PassThru
Start-Sleep -Seconds 2

$env:NODE_TLS_REJECT_UNAUTHORIZED = '0'
$env:ELECTRON_ENABLE_LOGGING = '1'
$env:HTTP_PROXY = "http://$Proxy"
$env:HTTPS_PROXY = "http://$Proxy"
$env:ALL_PROXY = "http://$Proxy"

$windsurfArgs = @(
  '--user-data-dir=' + $ProfileDir,
  '--proxy-server=' + $Proxy,
  '--proxy-bypass-list=<-loopback>',
  '--ignore-certificate-errors',
  '--allow-insecure-localhost',
  '--log-net-log=' + (Join-Path $CaptureDir 'chromium-netlog.json')
)

$windsurf = Start-Process -FilePath $WindsurfExe -ArgumentList $windsurfArgs -PassThru

Write-Host ('MITM PID=' + $mitm.Id)
Write-Host ('Windsurf PID=' + $windsurf.Id)
Write-Host ('Traffic file=' + $TrafficFile)
Write-Host 'Complete login/session actions in Windsurf, then stop both processes when done.'
