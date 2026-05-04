# Script PowerShell - Test Automatique Complet Windsurf
# Date: 2026-05-04

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Automatique Windsurf - Tous Modeles" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$windsurfPath = "C:\Users\amine\AppData\Local\Programs\Windsurf\Windsurf.exe"
$scriptsDir = "C:\Users\amine\OmniRoute\scripts"
$testScript = "test_windsurf_local_direct.py"

# Etape 1: Verifier si Windsurf est installe
Write-Host "[1/5] Verification de l'installation Windsurf..." -ForegroundColor Yellow

if (Test-Path $windsurfPath) {
    Write-Host "  [OK] Windsurf trouve: $windsurfPath" -ForegroundColor Green
} else {
    Write-Host "  [ERREUR] Windsurf non trouve a: $windsurfPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Chemins alternatifs a verifier:" -ForegroundColor Yellow
    Write-Host "  - C:\Program Files\Windsurf\Windsurf.exe"
    Write-Host "  - C:\Users\$env:USERNAME\AppData\Local\Programs\Windsurf\Windsurf.exe"
    Write-Host ""
    exit 1
}

# Etape 2: Verifier si Windsurf est deja lance
Write-Host ""
Write-Host "[2/5] Verification si Windsurf est deja lance..." -ForegroundColor Yellow

$windsurfProcess = Get-Process | Where-Object {$_.ProcessName -like "*Windsurf*"}

if ($windsurfProcess) {
    Write-Host "  [OK] Windsurf deja en cours d'execution (PID: $($windsurfProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "  [INFO] Windsurf non lance. Lancement en cours..." -ForegroundColor Yellow
    Start-Process $windsurfPath
    Write-Host "  [INFO] Attente du demarrage du serveur (15 secondes)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
}

# Etape 3: Verifier que le serveur local repond
Write-Host ""
Write-Host "[3/5] Verification du serveur local (localhost:53302)..." -ForegroundColor Yellow

$maxRetries = 3
$retryCount = 0
$serverOk = $false

while ($retryCount -lt $maxRetries -and -not $serverOk) {
    $retryCount++
    Write-Host "  [INFO] Tentative $retryCount/$maxRetries..." -ForegroundColor Yellow

    $testConnection = Test-NetConnection -ComputerName localhost -Port 53302 -WarningAction SilentlyContinue -InformationLevel Quiet

    if ($testConnection) {
        $serverOk = $true
        Write-Host "  [OK] Serveur local accessible sur localhost:53302" -ForegroundColor Green
    } else {
        if ($retryCount -lt $maxRetries) {
            Write-Host "  [INFO] Serveur non accessible. Nouvelle tentative dans 5 secondes..." -ForegroundColor Yellow
            Start-Sleep -Seconds 5
        }
    }
}

if (-not $serverOk) {
    Write-Host "  [ERREUR] Serveur local non accessible apres $maxRetries tentatives" -ForegroundColor Red
    Write-Host ""
    Write-Host "Solutions possibles:" -ForegroundColor Yellow
    Write-Host "  1. Attendre quelques secondes de plus et reessayer"
    Write-Host "  2. Verifier que Windsurf est bien lance"
    Write-Host "  3. Verifier qu'aucun firewall ne bloque le port 53302"
    Write-Host ""
    exit 1
}

# Etape 4: Executer le test Python
Write-Host ""
Write-Host "[4/5] Execution du test automatise..." -ForegroundColor Yellow

if (-not (Test-Path $scriptsDir)) {
    Write-Host "  [ERREUR] Repertoire scripts non trouve: $scriptsDir" -ForegroundColor Red
    exit 1
}

Set-Location $scriptsDir

if (-not (Test-Path $testScript)) {
    Write-Host "  [ERREUR] Script de test non trouve: $testScript" -ForegroundColor Red
    exit 1
}

Write-Host "  [INFO] Lancement de: python $testScript" -ForegroundColor Yellow
Write-Host ""

python $testScript

$testExitCode = $LASTEXITCODE

# Etape 5: Afficher le resume
Write-Host ""
Write-Host "[5/5] Resume des resultats..." -ForegroundColor Yellow

$resultsFile = "test_windsurf_local_direct_results.json"

if (Test-Path $resultsFile) {
    Write-Host "  [OK] Fichier de resultats cree: $resultsFile" -ForegroundColor Green

    # Lire et afficher le resume
    $results = Get-Content $resultsFile | ConvertFrom-Json

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "RESUME FINAL" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Total modeles testes: $($results.total)" -ForegroundColor White
    Write-Host "Succes (Status 200): $($results.success)" -ForegroundColor Green
    Write-Host "Rejetes (Status 500): $($results.rejected)" -ForegroundColor Yellow
    Write-Host "Erreurs: $($results.errors)" -ForegroundColor Red
    Write-Host ""

    if ($results.success -gt 0) {
        Write-Host "Modeles fonctionnels:" -ForegroundColor Green
        foreach ($result in $results.results) {
            if ($result.status -eq "success") {
                Write-Host "  - $($result.model)" -ForegroundColor Green
            }
        }
    }

    Write-Host ""

    if ($results.rejected -gt 0) {
        Write-Host "Modeles rejetes (normal pour modeles Premium via API locale):" -ForegroundColor Yellow
        foreach ($result in $results.results) {
            if ($result.status -eq "rejected") {
                Write-Host "  - $($result.model)" -ForegroundColor Yellow
            }
        }
    }

    Write-Host ""
    Write-Host "Fichier de resultats complet: $scriptsDir\$resultsFile" -ForegroundColor Cyan

} else {
    Write-Host "  [ERREUR] Fichier de resultats non trouve" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test termine" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

exit $testExitCode
