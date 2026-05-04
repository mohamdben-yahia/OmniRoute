# Amélioration: Auto-Détection de Configuration Windsurf

**Date**: 2026-05-04  
**Objectif**: Éliminer la configuration manuelle du port et du CSRF token

---

## 🎯 Problème Résolu

### Avant (Configuration Manuelle)

```python
# Configuration hardcodée dans le script
os.environ['WINDSURF_CSRF_TOKEN'] = 'a5d004fc-a32d-49ab-ab4d-3d27db4167f9'
os.environ['WINDSURF_LOCAL_LS_PORT'] = '59455'
```

**Problèmes**:

- ❌ Port change à chaque lancement de Windsurf
- ❌ CSRF token change périodiquement
- ❌ Nécessite modification manuelle du script
- ❌ Erreurs si configuration obsolète
- ❌ Non portable entre workspaces

### Après (Auto-Détection)

```python
# Détection automatique
port = find_active_ls_port()           # Scan netstat pour ports 50000-60000
csrf_token = find_csrf_token_in_files() # Cherche token le plus récent
credentials = find_user_credentials()   # Charge credentials depuis .env
```

**Avantages**:

- ✅ Détecte automatiquement le port actif
- ✅ Trouve le CSRF token le plus récent
- ✅ Aucune modification manuelle requise
- ✅ Fonctionne dans n'importe quel workspace
- ✅ Messages d'erreur clairs si Windsurf n'est pas actif

---

## 🔍 Méthodes de Détection

### 1. Détection du Port (find_active_ls_port)

**Méthode**: Scan netstat pour ports LISTENING sur 127.0.0.1

```python
def find_active_ls_port():
    result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)

    for line in result.stdout.split('\n'):
        if 'LISTENING' in line and '127.0.0.1' in line:
            match = re.search(r'127\.0\.0\.1:(\d+)', line)
            if match:
                port = int(match.group(1))
                # Windsurf LS utilise typiquement 50000-60000
                if 50000 <= port <= 60000:
                    return port
```

**Plage de ports**: 50000-60000 (plage typique du Language Server Windsurf)

**Exemples de ports détectés**:

- 53302 (workspace OmniRoute)
- 59455 (workspace winsurftiwtest)

### 2. Détection du CSRF Token (find_csrf_token_in_files)

**Méthode**: Recherche dans plusieurs emplacements, retourne le plus récent

**Emplacements recherchés**:

```python
search_paths = [
    Path('.'),                          # Répertoire courant
    Path('C:/Users/amine/OmniRoute'),   # Workspace OmniRoute
    Path('C:/Users/amine/AppData/Local/Programs/Windsurf/winsurftiwtest'),
    Path.home(),                        # Répertoire utilisateur
]

search_files = [
    'windsurf-live-bootstrap.json',
    'tmp_windsurf_runtime_ls_binding.json',
    '.env.windsurf.local',
    '03-captures/network/windsurf-live-bootstrap.json',
]
```

**Formats supportés**:

- JSON: `{"csrfToken": "..."}`
- ENV: `WINDSURF_CSRF_TOKEN=...`

**Sélection**: Token du fichier le plus récemment modifié

### 3. Détection des Credentials (find_user_credentials)

**Méthode**: Extraction depuis fichiers .env.windsurf.local

```python
# Cherche dans .env.windsurf.local:
WINDSURF_USER_ID=user-a0877fa492bb4eb3b0697a7c72bbb97b
WINDSURF_TEAM_ID=devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be
WINDSURF_SESSION_ID=20924
```

**Fallback**: Valeurs par défaut si non trouvées

---

## 📊 Flux d'Exécution

```
┌─────────────────────────────────────────────────────────────┐
│ 1. AUTO-DÉTECTION                                           │
├─────────────────────────────────────────────────────────────┤
│ [1/3] Auto-detecting Windsurf configuration...              │
│   ✓ Found active Language Server on port: 53302            │
│   ✓ Found CSRF token from: .env.windsurf.local             │
│   ✓ User credentials loaded                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CONFIGURATION                                            │
├─────────────────────────────────────────────────────────────┤
│ [2/3] Configuring environment...                            │
│   Port: 53302                                               │
│   CSRF Token: 3a1d0e5e-db26-4abe...                        │
│   User ID: user-a0877fa492bb4eb3...                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. TESTS                                                    │
├─────────────────────────────────────────────────────────────┤
│ [3/3] Starting model tests...                               │
│   Test 1/18: kimi-k2-6                                      │
│   Test 2/18: kimi-k2-5                                      │
│   ...                                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚨 Gestion des Erreurs

### Windsurf Non Actif

```
✗ No active Language Server found
→ Make sure Windsurf is running
```

**Action**: Lancer Windsurf dans n'importe quel workspace

### CSRF Token Non Trouvé

```
✗ No CSRF token found
→ Make sure Windsurf has been launched at least once
```

**Action**: Lancer Windsurf au moins une fois pour générer le token

---

## 📁 Fichiers Créés

### Script Principal

**Fichier**: `test_windsurf_builtin_models_auto.py`

**Localisation**:

- `C:\Users\amine\OmniRoute\test_windsurf_builtin_models_auto.py`
- `C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\test_windsurf_builtin_models_auto.py`

**Taille**: ~10 KB

**Fonctionnalités**:

- Auto-détection port + CSRF token + credentials
- Test de 18 modèles Windsurf
- Génération de rapport JSON
- Encodage UTF-8 pour Windows

### Résultats

**Fichier**: `windsurf_builtin_models_test_auto.json`

**Structure**:

```json
{
  "timestamp": "2026-05-04T...",
  "auto_detected": {
    "port": 53302,
    "csrf_token_file": "C:\\Users\\amine\\OmniRoute\\.env.windsurf.local"
  },
  "summary": {
    "total": 18,
    "available": 18,
    "unavailable": 0
  },
  "results": [...]
}
```

---

## 🎓 Utilisation

### Lancement Simple

```bash
# Dans n'importe quel workspace où Windsurf est actif
python test_windsurf_builtin_models_auto.py
```

**Prérequis**:

1. Windsurf en cours d'exécution
2. Fichier de configuration présent (généré automatiquement par Windsurf)

### Aucune Configuration Manuelle

Le script détecte automatiquement:

- ✅ Port du Language Server actif
- ✅ CSRF token le plus récent
- ✅ Credentials utilisateur
- ✅ Workspace actif

---

## 📈 Comparaison: Avant vs Après

| Aspect            | Avant (Manuel)                     | Après (Auto)            |
| ----------------- | ---------------------------------- | ----------------------- |
| **Configuration** | Modifier le script à chaque fois   | Aucune modification     |
| **Portabilité**   | Lié à un workspace spécifique      | Fonctionne partout      |
| **Maintenance**   | Mise à jour manuelle du port/token | Détection automatique   |
| **Erreurs**       | Fréquentes (config obsolète)       | Rares (messages clairs) |
| **Temps setup**   | 2-3 minutes                        | 0 seconde               |
| **Expérience**    | Frustrante                         | Fluide                  |

---

## 🔄 Évolution

### Version 1 (Manuelle)

```python
# Hardcodé
os.environ['WINDSURF_CSRF_TOKEN'] = 'a5d004fc-...'
os.environ['WINDSURF_LOCAL_LS_PORT'] = '59455'
```

### Version 2 (Auto-Détection)

```python
# Détection automatique
port = find_active_ls_port()
csrf_token, token_file = find_csrf_token_in_files()
credentials = find_user_credentials()

# Configuration automatique
os.environ['WINDSURF_CSRF_TOKEN'] = csrf_token
os.environ['WINDSURF_LOCAL_LS_PORT'] = str(port)
```

---

## ✅ Résultat Final

**Script amélioré**: `test_windsurf_builtin_models_auto.py`

**Avantages**:

- 🚀 Zéro configuration manuelle
- 🔄 Portable entre workspaces
- 🎯 Détection intelligente
- 📊 Messages d'erreur clairs
- ⚡ Prêt à l'emploi

**Utilisation**:

```bash
python test_windsurf_builtin_models_auto.py
```

**Résultat attendu**: Test automatique de 18 modèles avec rapport complet

---

**Date de création**: 2026-05-04  
**Status**: ✓ IMPLÉMENTÉ ET TESTÉ
