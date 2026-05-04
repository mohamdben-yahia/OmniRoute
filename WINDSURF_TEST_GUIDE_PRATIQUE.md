# Guide Pratique - Tester Tous Les Modèles Windsurf

**Date**: 2026-05-04T10:48:00Z

---

## 🚀 Option 1: Test Automatisé (Recommandé)

### Étape 1: Lancer Windsurf

```powershell
# Trouver l'exécutable Windsurf
$windsurfPath = "C:\Users\amine\AppData\Local\Programs\Windsurf\Windsurf.exe"

# Lancer Windsurf
Start-Process $windsurfPath
```

**Ou manuellement**:
1. Ouvrir le menu Démarrer
2. Chercher "Windsurf"
3. Cliquer pour lancer

### Étape 2: Attendre que le serveur démarre

Attendre 10-15 secondes que le serveur local démarre sur localhost:53302.

### Étape 3: Exécuter le test automatisé

```bash
cd C:\Users\amine\OmniRoute\scripts
python test_windsurf_local_direct.py
```

**Résultat attendu**:
- 5 modèles avec Status 200 (kimi-k2-6, kimi-k2-5, glm-5, glm-5-1, swe-1-6-fast)
- 4 modèles avec Status 500 (claude, gpt, gemini, deepseek)
- Fichier de résultats: `test_windsurf_local_direct_results.json`

---

## 📝 Option 2: Test Manuel dans l'Interface

### Pour Chaque Modèle

1. **Ouvrir Windsurf**
2. **Ouvrir le chat** (Ctrl+L ou icône chat)
3. **Sélectionner le modèle** dans le menu déroulant
4. **Envoyer le message**: `quelle model llm vous etes`
5. **Noter la réponse**

### Liste des Modèles à Tester

**Modèles Premium** (nécessitent compte Pro):
- [ ] claude-3-5-sonnet-20241022
- [ ] claude-3-5-haiku-20241022
- [ ] claude-3-opus-20240229
- [ ] gpt-4o
- [ ] gpt-4o-mini
- [ ] o1-preview
- [ ] o1-mini
- [ ] gemini-2.0-flash-exp
- [ ] gemini-1.5-pro
- [ ] gemini-1.5-flash
- [ ] deepseek-chat
- [ ] deepseek-reasoner
- [ ] grok-2-1212
- [ ] llama-3.3-70b-versatile
- [ ] mixtral-8x7b-32768

**Modèles Gratuits** (disponibles sans Pro):
- [ ] kimi-k2-6
- [ ] kimi-k2-5
- [ ] glm-5
- [ ] glm-5-1
- [ ] swe-1-6-fast

### Template de Résultats

```markdown
## Résultats Test Manuel

**Date**: 2026-05-04
**Message testé**: "quelle model llm vous etes"

### Modèles Fonctionnels (✅)

| Modèle | Réponse | Temps |
|--------|---------|-------|
| claude-3-5-sonnet-20241022 | [réponse] | [temps] |
| ... | ... | ... |

### Modèles Non Fonctionnels (❌)

| Modèle | Erreur |
|--------|--------|
| ... | ... |
```

---

## 🔍 Option 3: Vérifier l'État du Serveur

### Vérifier si Windsurf est lancé

```powershell
# Vérifier le processus
Get-Process | Where-Object {$_.ProcessName -like "*Windsurf*"}

# Vérifier le port 53302
Test-NetConnection -ComputerName localhost -Port 53302
```

### Vérifier si le serveur répond

```bash
cd C:\Users\amine\OmniRoute\scripts
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:53302', timeout=5).status)"
```

**Résultat attendu**:
- Si Windsurf lancé: `200` ou autre code HTTP
- Si Windsurf non lancé: `Connection refused`

---

## 📊 Interpréter les Résultats

### Résultat Attendu (API Locale)

```json
{
  "success": 5,
  "rejected": 4,
  "errors": 0,
  "results": [
    {"model": "kimi-k2-6", "status": "success", "http_status": 200},
    {"model": "kimi-k2-5", "status": "success", "http_status": 200},
    {"model": "glm-5", "status": "success", "http_status": 200},
    {"model": "glm-5-1", "status": "success", "http_status": 200},
    {"model": "swe-1-6-fast", "status": "success", "http_status": 200},
    {"model": "claude-3-5-sonnet-20241022", "status": "rejected", "http_status": 500},
    {"model": "gpt-4o", "status": "rejected", "http_status": 500},
    {"model": "gemini-2.0-flash-exp", "status": "rejected", "http_status": 500},
    {"model": "deepseek-chat", "status": "rejected", "http_status": 500}
  ]
}
```

### Résultat Attendu (Interface Windsurf avec Pro)

Selon vos tests précédents (SESSION_COMPLETE_SUMMARY.md):
- ✅ 21 modèles fonctionnent
- ✅ Tous avec Status 200
- ✅ Temps de réponse: 7000-9000ms

---

## 🎯 Que Faire Ensuite

### Si Test Automatisé Réussit (5 modèles)

**Conclusion**: L'API locale fonctionne correctement.

**Pour OmniRoute**:
```typescript
// Implémenter les 5 modèles locaux
const WINDSURF_LOCAL_MODELS = [
  'kimi-k2-6',
  'kimi-k2-5',
  'glm-5',
  'glm-5-1',
  'swe-1-6-fast'
];
```

### Si Test Manuel Réussit (21 modèles)

**Conclusion**: L'interface Windsurf avec compte Pro fonctionne.

**Pour OmniRoute**:
```typescript
// Ajouter support pour les modèles Pro
const WINDSURF_PRO_MODELS = [
  'claude-3-5-sonnet-20241022',
  'gpt-4o',
  'gemini-2.0-flash-exp',
  // ... tous les modèles Pro
];
```

### Si Aucun Test Ne Fonctionne

**Vérifier**:
1. Windsurf est-il lancé?
2. Le serveur local répond-il sur localhost:53302?
3. Avez-vous un compte Windsurf Pro?

---

## 🔧 Dépannage

### Erreur: "Connection refused"

**Cause**: Windsurf n'est pas lancé ou le serveur local n'a pas démarré.

**Solution**:
1. Lancer Windsurf
2. Attendre 15 secondes
3. Réessayer le test

### Erreur: "DEVIN_TOKEN_EXCHANGE_PSK"

**Cause**: Tentative d'accès à l'API cloud directement (impossible).

**Solution**: Utiliser l'API locale (localhost:53302) ou l'interface Windsurf.

### Tous les modèles rejetés (Status 500)

**Cause**: Whitelist serveur stricte pour l'API locale.

**Solution**: 
- Normal pour les modèles Premium via API locale
- Utiliser l'interface Windsurf pour tester les modèles Pro

---

## 📝 Script Complet de Test

```powershell
# Script PowerShell complet pour tester Windsurf

# 1. Lancer Windsurf
Write-Host "Lancement de Windsurf..." -ForegroundColor Cyan
$windsurfPath = "C:\Users\amine\AppData\Local\Programs\Windsurf\Windsurf.exe"
if (Test-Path $windsurfPath) {
    Start-Process $windsurfPath
    Write-Host "Windsurf lancé. Attente du démarrage du serveur..." -ForegroundColor Green
    Start-Sleep -Seconds 15
} else {
    Write-Host "Windsurf non trouvé à: $windsurfPath" -ForegroundColor Red
    exit 1
}

# 2. Vérifier que le serveur répond
Write-Host "Vérification du serveur local..." -ForegroundColor Cyan
$serverOk = Test-NetConnection -ComputerName localhost -Port 53302 -WarningAction SilentlyContinue

if ($serverOk.TcpTestSucceeded) {
    Write-Host "Serveur local OK sur localhost:53302" -ForegroundColor Green
} else {
    Write-Host "Serveur local non accessible" -ForegroundColor Red
    exit 1
}

# 3. Exécuter le test
Write-Host "Exécution du test automatisé..." -ForegroundColor Cyan
cd C:\Users\amine\OmniRoute\scripts
python test_windsurf_local_direct.py

# 4. Afficher les résultats
Write-Host "`nTest terminé. Résultats sauvegardés dans:" -ForegroundColor Cyan
Write-Host "  test_windsurf_local_direct_results.json" -ForegroundColor Yellow
```

**Sauvegarder ce script**: `test_windsurf_complete.ps1`

**Exécuter**:
```powershell
.\test_windsurf_complete.ps1
```

---

## ✅ Checklist Finale

- [ ] Windsurf est installé
- [ ] Windsurf est lancé
- [ ] Serveur local répond sur localhost:53302
- [ ] Script de test exécuté
- [ ] Résultats sauvegardés
- [ ] 5 modèles gratuits fonctionnent (API locale)
- [ ] 21 modèles Pro fonctionnent (interface, si compte Pro)

---

**Document créé**: 2026-05-04T10:48:00Z  
**Statut**: Guide pratique complet  
**Prochaine étape**: Lancer Windsurf et exécuter le test automatisé
