# Configuration du Workspace Windsurf Test

**Date**: 2026-05-04T00:09:00Z  
**Workspace Path**: `C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest`

---

## Structure du Workspace

```
C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\
├── 01-setup/                    # Configuration initiale
├── 02-auth/                     # Tests d'authentification
├── 03-captures/                 # Captures réseau et payloads
│   ├── network/                 # Captures DevTools
│   └── payloads/                # Fichiers .bin et .hex
├── 04-investigation/            # Scripts d'investigation
│   └── scripts/                 # Scripts Python
├── 05-integration/              # Intégration avec OmniRoute
└── docs/                        # Documentation locale
```

---

## Variables d'Environnement Découvertes

### Session Active (Terminal PowerShell)

```powershell
$env:WINDSURF_USER_ID = "user-a0877fa492bb4eb3b0697a7c72bbb97b"
$env:WINDSURF_TEAM_ID = "devin-team`$account-2a2bd7ac9a4e47ee83140eace192c9be"
$env:WINDSURF_METADATA_F = "000103"
$env:WINDSURF_SESSION_ID = "20924"
$env:WINDSURF_SWE_VERSION = "swe-1-6"
$env:WINDSURF_BOOTSTRAP_PATH = "C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\03-captures\network\windsurf-live-bootstrap.json"
```

### Informations Extraites

- **User ID**: `user-a0877fa492bb4eb3b0697a7c72bbb97b`
- **Team ID**: `devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be`
- **Session ID**: `20924`
- **SWE Version**: `swe-1-6`
- **Bootstrap JSON**: Disponible dans `03-captures/network/`

---

## Scripts à Adapter

### 1. windsurf_direct_probe.py

**Localisation**: `C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\04-investigation\scripts\windsurf_direct_probe.py`

**Statut**: Exécuté avec erreur (Exit Code: 1)

**Commande Exécutée**:

```powershell
python windsurf_direct_probe.py --audit-local-au...366-813f-322502f9257a
```

**Action Requise**: Vérifier les logs d'erreur et corriger

### 2. Scripts de Test à Migrer

Depuis `C:\Users\amine\OmniRoute\scripts\` vers le nouveau workspace:

- `windsurf_test.py` → `04-investigation/scripts/`
- `windsurf_verify.py` → `04-investigation/scripts/`
- `windsurf_one_click_test.py` → `04-investigation/scripts/`
- `windsurf_test_with_captured_payload.py` → `04-investigation/scripts/`
- `windsurf_server_detector.py` → `04-investigation/scripts/`
- Tous les autres scripts de test

---

## Configuration des Chemins

### Mise à Jour des Scripts

Tous les scripts doivent être mis à jour pour utiliser les nouveaux chemins:

```python
# Ancien chemin (OmniRoute)
BASE_DIR = r"C:\Users\amine\OmniRoute"
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

# Nouveau chemin (Workspace Test)
BASE_DIR = r"C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest"
SCRIPTS_DIR = os.path.join(BASE_DIR, "04-investigation", "scripts")
CAPTURES_DIR = os.path.join(BASE_DIR, "03-captures")
PAYLOADS_DIR = os.path.join(CAPTURES_DIR, "payloads")
NETWORK_DIR = os.path.join(CAPTURES_DIR, "network")
```

### Fichiers de Configuration

Créer `config.json` dans le workspace:

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
    "port_range": [50000, 60000],
    "last_known_port": 59455,
    "csrf_token": "a5d004fc-a32d-49ab-ab4d-3d27db4167f9"
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

## Bootstrap JSON

### Localisation

`C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\03-captures\network\windsurf-live-bootstrap.json`

### Contenu Attendu

Ce fichier contient probablement:

- Configuration de session
- Tokens d'authentification
- Endpoints API
- Métadonnées de connexion

### Action Requise

Lire et analyser ce fichier pour extraire:

- Session token complet
- API endpoints
- Configuration des modèles
- Paramètres de connexion

---

## Prochaines Étapes

### 1. Analyser l'Erreur du Script

```powershell
cd "C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\04-investigation\scripts"
python windsurf_direct_probe.py --help
# Voir les options disponibles et corriger la commande
```

### 2. Lire le Bootstrap JSON

```powershell
type "C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\03-captures\network\windsurf-live-bootstrap.json"
```

### 3. Migrer les Scripts

Copier tous les scripts de test depuis OmniRoute vers le nouveau workspace:

```powershell
# Depuis C:\Users\amine\OmniRoute
xcopy scripts\windsurf_*.py "C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\04-investigation\scripts\" /Y
```

### 4. Créer le Fichier de Configuration

```powershell
cd "C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest"
# Créer config.json avec le contenu ci-dessus
```

### 5. Mettre à Jour les Chemins dans les Scripts

Éditer chaque script pour utiliser les nouveaux chemins du workspace.

### 6. Tester la Configuration

```powershell
cd "C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\04-investigation\scripts"
python windsurf_test.py
```

---

## Avantages du Nouveau Workspace

### Organisation

- ✓ Structure claire par phase (setup, auth, captures, investigation, integration)
- ✓ Séparation des captures réseau et des scripts
- ✓ Documentation locale dans le workspace
- ✓ Configuration centralisée dans config.json

### Isolation

- ✓ Séparé du code OmniRoute principal
- ✓ Peut être versionné indépendamment
- ✓ Facilite le partage et la collaboration
- ✓ Évite la pollution du repo principal

### Traçabilité

- ✓ Toutes les captures au même endroit
- ✓ Historique des tests dans le workspace
- ✓ Variables d'environnement documentées
- ✓ Bootstrap JSON disponible localement

---

## Commandes Rapides

### Navigation

```powershell
# Aller au workspace
cd "C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest"

# Aller aux scripts
cd "04-investigation\scripts"

# Aller aux captures
cd "03-captures\network"
```

### Exécution

```powershell
# Depuis le workspace root
python 04-investigation\scripts\windsurf_test.py

# Depuis le dossier scripts
cd 04-investigation\scripts
python windsurf_test.py
```

### Analyse

```powershell
# Lire le bootstrap
type 03-captures\network\windsurf-live-bootstrap.json

# Lister les captures
dir 03-captures\network

# Lister les payloads
dir 03-captures\payloads
```

---

## Notes Importantes

### Variables d'Environnement

Les variables d'environnement découvertes dans le terminal PowerShell sont **critiques** pour l'authentification:

- `WINDSURF_USER_ID`: Identifie l'utilisateur
- `WINDSURF_TEAM_ID`: Identifie l'équipe/compte
- `WINDSURF_SESSION_ID`: ID de session unique
- `WINDSURF_BOOTSTRAP_PATH`: Chemin vers la config de session

Ces variables doivent être **préservées** et **utilisées** dans les scripts de test.

### Bootstrap JSON

Le fichier `windsurf-live-bootstrap.json` est probablement la **source de vérité** pour:

- Tokens d'authentification complets
- Configuration de session
- Endpoints API
- Métadonnées requises

**Action prioritaire**: Lire et analyser ce fichier.

### Erreur du Script

Le script `windsurf_direct_probe.py` a échoué (Exit Code: 1). Causes possibles:

- Arguments manquants ou incorrects
- Dépendances Python manquantes
- Erreur de connexion API
- Problème de permissions

**Action requise**: Analyser les logs d'erreur et corriger.

---

## Résumé

### Workspace Configuré

✓ Chemin: `C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest`  
✓ Structure: 6 dossiers principaux  
✓ Variables d'environnement: Découvertes et documentées  
✓ Bootstrap JSON: Disponible dans `03-captures/network/`

### Actions Immédiates

1. Lire le bootstrap JSON
2. Analyser l'erreur de windsurf_direct_probe.py
3. Migrer les scripts de test
4. Créer config.json
5. Tester la configuration

### Prochaine Phase

Une fois le workspace configuré et les scripts migrés, nous pourrons:

- Exécuter les tests avec les vraies variables d'environnement
- Utiliser le bootstrap JSON pour l'authentification complète
- Capturer de nouveaux payloads dans la structure organisée
- Intégrer avec OmniRoute (phase 05-integration)
