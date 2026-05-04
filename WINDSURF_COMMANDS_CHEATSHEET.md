# WINDSURF PROBE - COMMANDES ESSENTIELLES

## Setup Rapide

```powershell
# Variables d'environnement
$env:WINDSURF_USER_ID = 'user-a0877fa492bb4eb3b0697a7c72bbb97b'
$env:WINDSURF_TEAM_ID = 'devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be'
$env:WINDSURF_METADATA_F = '000103'
$env:WINDSURF_SESSION_ID = '20924'
$env:WINDSURF_SWE_VERSION = 'swe-1-6'
$env:WINDSURF_CSRF_TOKEN = '91e3d9fc-7277-4618-81ee-b72bc0adda38'
```

## Tests Rapides

```powershell
# Test identité modèle
$env:WINDSURF_CHAT_TEXT = 'What model are you?'
python ask_model_identity.py

# Test français
$env:WINDSURF_CHAT_TEXT = 'Say hello in French'
python get_fresh_response.py

# Test multiple cascades
python test_multiple_models.py
```

## Résultats Attendus

- **Modèle**: kimi-k2-6 (Moonshot AI)
- **Temps**: 3-5 secondes
- **Taille**: ~60KB

## Fichiers Importants

- windsurf-live-bootstrap.json (port + CSRF)
- tmp_windsurf_runtime_ls_binding.json (binding LS)
- WINDSURF_PROBE_FINAL_SUMMARY.md (documentation complète)

**Status**: Production-ready ✓
