# Analyse du Bootstrap Windsurf

**Date**: 2026-05-04T00:11:00Z  
**Source**: `C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\03-captures\network\windsurf-live-bootstrap.json`

---

## Contenu du Bootstrap JSON

```json
{
  "csrfToken": "a5d004fc-a32d-49ab-ab4d-3d27db4167f9",
  "languageServerPort": 59455,
  "languageServerUrl": "http://localhost:59455",
  "apiUrl": null,
  "host": "127.0.0.1",
  "observedAt": "2026-05-03T18:12:29.821Z",
  "hookInstalledAt": "2026-05-03T18:06:05.387Z",
  "firstInterceptedMethod": null,
  "languageServerStartedSeen": true,
  "interceptedMethodsSample": [],
  "processPid": 20836,
  "processPpid": 25476,
  "processSurface": "host",
  "steps": []
}
```

---

## Informations Extraites

### Authentification

- **CSRF Token**: `a5d004fc-a32d-49ab-ab4d-3d27db4167f9`
- **Validité**: Token actif au moment de la capture (2026-05-03T18:12:29.821Z)
- **Usage**: Header `x-codeium-csrf-token` dans toutes les requêtes API

### API Endpoint

- **Port**: `59455`
- **URL Complète**: `http://localhost:59455`
- **Host**: `127.0.0.1`
- **Host Header**: `v.localhost:59455` (CRITIQUE - doit être v.localhost, pas localhost)

### Processus

- **Language Server PID**: `20836`
- **Parent Process PID**: `25476`
- **Surface**: `host` (processus principal)
- **Statut**: Language server démarré et observé

### Timeline

- **Hook Installé**: `2026-05-03T18:06:05.387Z`
- **Observation**: `2026-05-03T18:12:29.821Z`
- **Durée**: ~6 minutes entre installation du hook et observation

---

## Analyse du Script windsurf_direct_probe.py

### Architecture du Script

Le script `windsurf_direct_probe.py` est un **outil d'investigation avancé** qui:

1. **Découvre automatiquement** le Language Server en cours d'exécution
2. **Gère le runtime binding** (liaison dynamique avec le serveur)
3. **Lit les fichiers de configuration** (.env.windsurf.local, bootstrap JSON)
4. **Parse les réponses Protobuf** avec un parser dédié
5. **Maintient un registre** des sessions actives

### Dépendances Requises

```python
# Bibliothèques standard
import base64, ctypes, gzip, hashlib, json, os, pathlib, re, socket
import subprocess, sqlite3, sys, time, urllib, uuid
from datetime import datetime, timezone

# Bibliothèques tierces
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Modules locaux requis
from runtime_ls_state import RuntimeLSRegistry
from protobuf_parser import parse_trajectory_response, extract_model_router_uid
```

### Fichiers de Configuration Attendus

1. **`.env.windsurf.local`** (optionnel)
   - Variables d'environnement pour la configuration
   - Chemin par défaut: `../../../.env.windsurf.local` (relatif au script)

2. **`windsurf-live-bootstrap.json`** (requis)
   - Bootstrap JSON avec CSRF token et port
   - Chemin par défaut: `../../../windsurf-live-bootstrap.json`
   - **TROUVÉ**: `03-captures/network/windsurf-live-bootstrap.json`

3. **`tmp_windsurf_runtime_ls_binding.json`** (généré)
   - État du runtime binding
   - Chemin par défaut: `../../../tmp_windsurf_runtime_ls_binding.json`

4. **`windsurf-electron-lifecycle-trace.jsonl`** (optionnel)
   - Trace du cycle de vie Electron
   - Chemin par défaut: `../../../windsurf-electron-lifecycle-trace.jsonl`

### Variables d'Environnement Supportées

```bash
# Configuration de base
WINDSURF_DIRECT_KEY          # Token d'authentification direct
WINDSURF_CSRF_TOKEN          # CSRF token (alternative au bootstrap)
WINDSURF_CHAT_BASE_URL       # URL de base API (défaut: https://eu.windsurf.com/_route/api_server)
WINDSURF_CHAT_SERVICE        # Service à utiliser (api ou language_server)
WINDSURF_CHAT_METHOD_NAME    # Nom de la méthode RPC
WINDSURF_ASSIGN_MODEL_METHOD_NAME  # Méthode pour assigner un modèle

# Chemins de configuration
WINDSURF_LOCAL_ENV_PATH              # Chemin vers .env.windsurf.local
WINDSURF_RUNTIME_LS_BINDING_PATH     # Chemin vers runtime binding JSON
WINDSURF_LIVE_BOOTSTRAP_PATH         # Chemin vers bootstrap JSON
WINDSURF_ELECTRON_LIFECYCLE_TRACE_PATH  # Chemin vers trace lifecycle
```

### Endpoints API Configurables

```python
# Endpoint par défaut
DEFAULT_CHAT_BASE_URL = "https://eu.windsurf.com/_route/api_server"

# Services disponibles
- exa.api_server_pb.ApiServerService/GetChatMessage
- exa.language_server_pb.LanguageServerService/RawGetChatMessage
- exa.api_server_pb.ApiServerService/AssignModel
```

### Host Aliases par RPC

```python
LOCAL_LS_HOST_ALIAS_BY_RPC = {
    "StartCascade": "l",           # l.localhost
    "SendUserCascadeMessage": "e", # e.localhost
    "GetCascadeTrajectory": "l",   # l.localhost
    "CheckUserMessageRateLimit": "l",
    "GetModelStatuses": "b",       # b.localhost
    "GetUserStatus": "w",          # w.localhost
}
```

**IMPORTANT**: Chaque méthode RPC utilise un sous-domaine différent!

---

## Cause de l'Erreur (Exit Code: 1)

### Analyse de la Commande Exécutée

```powershell
python windsurf_direct_probe.py --audit-local-au...366-813f-322502f9257a
```

**Problème**: Commande tronquée ou argument incomplet

### Causes Probables

1. **Modules manquants**:
   - `runtime_ls_state.py` non trouvé
   - `protobuf_parser.py` non trouvé
   - `cryptography` non installé

2. **Fichiers de configuration manquants**:
   - `.env.windsurf.local` non trouvé (optionnel mais peut causer des warnings)
   - `tmp_windsurf_runtime_ls_binding.json` non initialisé

3. **Arguments incorrects**:
   - `--audit-local-au...` semble tronqué
   - Argument complet probablement: `--audit-local-auth-token` ou similaire

4. **Permissions**:
   - Accès au port 59455 bloqué
   - Processus Language Server non accessible

---

## Solution: Configuration Correcte

### Étape 1: Vérifier les Dépendances

```powershell
cd "C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\04-investigation\scripts"

# Vérifier les modules requis
python -c "import cryptography; print('cryptography OK')"
python -c "from runtime_ls_state import RuntimeLSRegistry; print('runtime_ls_state OK')"
python -c "from protobuf_parser import parse_trajectory_response; print('protobuf_parser OK')"
```

### Étape 2: Installer les Dépendances Manquantes

```powershell
# Si cryptography manquant
pip install cryptography

# Si modules locaux manquants, vérifier leur présence
dir runtime_ls_state.py
dir protobuf_parser.py
```

### Étape 3: Configurer les Variables d'Environnement

```powershell
# Définir le chemin vers le bootstrap JSON
$env:WINDSURF_LIVE_BOOTSTRAP_PATH = "C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\03-captures\network\windsurf-live-bootstrap.json"

# Définir le CSRF token (optionnel, déjà dans bootstrap)
$env:WINDSURF_CSRF_TOKEN = "a5d004fc-a32d-49ab-ab4d-3d27db4167f9"

# Définir les autres variables découvertes
$env:WINDSURF_USER_ID = "user-a0877fa492bb4eb3b0697a7c72bbb97b"
$env:WINDSURF_TEAM_ID = "devin-team`$account-2a2bd7ac9a4e47ee83140eace192c9be"
$env:WINDSURF_SESSION_ID = "20924"
$env:WINDSURF_SWE_VERSION = "swe-1-6"
```

### Étape 4: Voir l'Aide du Script

```powershell
python windsurf_direct_probe.py --help
```

### Étape 5: Exécuter avec les Bons Arguments

```powershell
# Exemple de commande correcte (à adapter selon --help)
python windsurf_direct_probe.py --discover
python windsurf_direct_probe.py --test-connection
python windsurf_direct_probe.py --audit-local-auth
```

---

## Configuration Recommandée

### Créer .env.windsurf.local

```bash
# C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\.env.windsurf.local

# Bootstrap et binding
WINDSURF_LIVE_BOOTSTRAP_PATH=C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\03-captures\network\windsurf-live-bootstrap.json
WINDSURF_RUNTIME_LS_BINDING_PATH=C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\tmp_windsurf_runtime_ls_binding.json

# Authentification
WINDSURF_CSRF_TOKEN=a5d004fc-a32d-49ab-ab4d-3d27db4167f9

# Identifiants
WINDSURF_USER_ID=user-a0877fa492bb4eb3b0697a7c72bbb97b
WINDSURF_TEAM_ID=devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be
WINDSURF_SESSION_ID=20924
WINDSURF_SWE_VERSION=swe-1-6

# API Configuration
WINDSURF_CHAT_BASE_URL=https://eu.windsurf.com/_route/api_server
WINDSURF_CHAT_SERVICE=api
WINDSURF_CHAT_METHOD_NAME=GetChatMessage
```

### Créer config.json Complet

```json
{
  "workspace_root": "C:\\Users\\amine\\AppData\\Local\\Programs\\Windsurf\\winsurftiwtest",
  "windsurf": {
    "user_id": "user-a0877fa492bb4eb3b0697a7c72bbb97b",
    "team_id": "devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be",
    "session_id": "20924",
    "swe_version": "swe-1-6",
    "bootstrap_path": "03-captures/network/windsurf-live-bootstrap.json"
  },
  "api": {
    "base_url": "http://127.0.0.1",
    "port": 59455,
    "language_server_url": "http://localhost:59455",
    "csrf_token": "a5d004fc-a32d-49ab-ab4d-3d27db4167f9",
    "host_header_prefix": "v.localhost"
  },
  "process": {
    "language_server_pid": 20836,
    "parent_pid": 25476,
    "surface": "host"
  },
  "timeline": {
    "hook_installed_at": "2026-05-03T18:06:05.387Z",
    "observed_at": "2026-05-03T18:12:29.821Z"
  },
  "host_aliases": {
    "StartCascade": "l",
    "SendUserCascadeMessage": "e",
    "GetCascadeTrajectory": "l",
    "CheckUserMessageRateLimit": "l",
    "GetModelStatuses": "b",
    "GetUserStatus": "w"
  },
  "paths": {
    "scripts": "04-investigation/scripts",
    "captures": "03-captures",
    "payloads": "03-captures/payloads",
    "network": "03-captures/network",
    "docs": "docs"
  }
}
```

---

## Découvertes Importantes

### 1. Host Aliases Multiples

**CRITIQUE**: Windsurf utilise des sous-domaines différents selon la méthode RPC!

- `StartCascade` → `l.localhost:59455`
- `SendUserCascadeMessage` → `e.localhost:59455`
- `GetModelStatuses` → `b.localhost:59455`
- `GetUserStatus` → `w.localhost:59455`

**Impact**: Nos scripts doivent utiliser le bon sous-domaine pour chaque méthode!

### 2. Deux Services API

```python
# Service 1: API Server (recommandé)
exa.api_server_pb.ApiServerService/GetChatMessage

# Service 2: Language Server (direct)
exa.language_server_pb.LanguageServerService/RawGetChatMessage
```

### 3. Runtime Binding Dynamique

Le script maintient un **registre dynamique** des sessions Language Server:

- Détection automatique du port
- Validation de la connexion
- Persistance de l'état
- Historique des bindings

### 4. Cryptographie

Le script utilise **AESGCM** (AES-GCM encryption):

- Probablement pour chiffrer/déchiffrer certaines données
- Nécessite la bibliothèque `cryptography`

---

## Prochaines Actions

### 1. Installer les Dépendances

```powershell
pip install cryptography
```

### 2. Vérifier les Modules Locaux

```powershell
cd "C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\04-investigation\scripts"
dir runtime_ls_state.py
dir protobuf_parser.py
```

### 3. Créer .env.windsurf.local

Avec le contenu recommandé ci-dessus.

### 4. Exécuter le Script Correctement

```powershell
# Voir l'aide
python windsurf_direct_probe.py --help

# Découvrir le Language Server
python windsurf_direct_probe.py --discover

# Tester la connexion
python windsurf_direct_probe.py --test-connection
```

### 5. Mettre à Jour Nos Scripts

Adapter nos scripts pour utiliser:

- Les bons sous-domaines par méthode RPC
- Le runtime binding dynamique
- Les deux services API (api_server et language_server)

---

## Résumé

### Bootstrap JSON ✓

- CSRF Token: `a5d004fc-a32d-49ab-ab4d-3d27db4167f9`
- Port: `59455`
- URL: `http://localhost:59455`
- PID: `20836`

### Script windsurf_direct_probe.py

- **Complexité**: Outil avancé avec découverte automatique
- **Dépendances**: cryptography, runtime_ls_state, protobuf_parser
- **Configuration**: .env.windsurf.local, bootstrap JSON, runtime binding
- **Erreur**: Probablement modules manquants ou arguments incorrects

### Découvertes Critiques

1. **Host aliases multiples** par méthode RPC
2. **Deux services API** disponibles
3. **Runtime binding dynamique** avec registre
4. **Cryptographie AESGCM** utilisée

### Actions Immédiates

1. Installer `cryptography`
2. Vérifier présence de `runtime_ls_state.py` et `protobuf_parser.py`
3. Créer `.env.windsurf.local`
4. Exécuter `python windsurf_direct_probe.py --help`
5. Adapter nos scripts avec les nouvelles découvertes
