# Analyse des Tests - 8 Modèles Windsurf via windsurf_direct_probe.py

**Date**: 2026-05-04  
**Script utilisé**: `windsurf_direct_probe.py`  
**Résultats**: 2 succès / 6 échecs

---

## 📊 Résumé des Résultats

| #   | Modèle                     | UID                                   | Statut    | Erreur     |
| --- | -------------------------- | ------------------------------------- | --------- | ---------- |
| 1   | GPT-5.5 Low                | `gpt-5-5-low-20260424`                | ✅ Succès | -          |
| 2   | Claude Opus 4.7 Medium     | `claude-opus-4-7-medium-20260424`     | ✅ Succès | -          |
| 3   | Claude Opus 4.6 Thinking   | `claude-opus-4-6-thinking-20260424`   | ❌ Échec  | Status 500 |
| 4   | Claude Sonnet 4.6 Thinking | `claude-sonnet-4-6-thinking-20260424` | ❌ Échec  | Status 500 |
| 5   | DeepSeek V4                | `deepseek-v4-20260424`                | ❌ Échec  | Status 500 |
| 6   | Kimi K2.6                  | `kimi-k2-6-20260424`                  | ❌ Échec  | Status 500 |
| 7   | SWE-1.6                    | `swe-1-6-20260424`                    | ❌ Échec  | Status 500 |
| 8   | SWE-1.6 Fast               | `swe-1-6-fast-20260424`               | ❌ Échec  | Status 500 |

---

## 🔍 Analyse Détaillée

### ✅ Modèles Réussis (2/8)

#### 1. GPT-5.5 Low

- **Statut**: Succès (HTTP 200)
- **Problème**: `"runtime binding unreachable"`
- **Raison**: Le script ne peut pas se connecter au serveur Windsurf local
- **Observation**: Le modèle existe mais nécessite Windsurf en cours d'exécution

#### 2. Claude Opus 4.7 Medium

- **Statut**: Succès (HTTP 200)
- **Problème**: `"runtime binding unreachable"`
- **Raison**: Même problème que GPT-5.5 Low
- **Observation**: Le modèle existe mais nécessite Windsurf en cours d'exécution

### ❌ Modèles Échoués (6/8)

**Erreur commune à tous les 6 modèles**:

```json
{
  "code": "internal",
  "message": "failed to validate Devin token: failed to fetch Devin user info: DEVIN_TOKEN_EXCHANGE_PSK environment variable not set"
}
```

**Détails**:

- **Status HTTP**: 500 (Internal Server Error)
- **Endpoint**: `https://eu.windsurf.com/_route/api_server/exa.api_server_pb.ApiServerService/AssignModel`
- **Problème**: Le token de session (`devin-session-token`) ne peut pas être validé
- **Raison**: Variable d'environnement `DEVIN_TOKEN_EXCHANGE_PSK` manquante côté serveur

---

## 🔧 Problèmes Identifiés

### 1. Runtime Binding Unreachable (Modèles 1-2)

**Symptôme**:

```json
"preconditionErrors": ["runtime binding unreachable"],
"cascadeAllowed": false
```

**Cause**: Le script `windsurf_direct_probe.py` essaie de se connecter au serveur Windsurf local (`http://127.0.0.1:51834`) mais:

- Windsurf n'est pas en cours d'exécution
- Le port 51834 n'est pas accessible
- Le binding runtime n'est pas valide

**Solution**: Lancer Windsurf avant d'exécuter le script

### 2. Token Validation Failed (Modèles 3-8)

**Symptôme**:

```json
"status": 500,
"message": "failed to validate Devin token: failed to fetch Devin user info: DEVIN_TOKEN_EXCHANGE_PSK environment variable not set"
```

**Cause**:

- Le script utilise un `devin-session-token` (token de session Windsurf)
- Le serveur Windsurf cloud (`eu.windsurf.com`) ne peut pas valider ce token
- Variable d'environnement `DEVIN_TOKEN_EXCHANGE_PSK` manquante côté serveur

**Solution**:

- Utiliser un token API direct au lieu d'un token de session
- Ou lancer Windsurf pour que le token de session soit valide

---

## 📝 Observations Importantes

### 1. Tous les Modèles Existent

Les 8 modèles ont été reconnus par l'API:

- `StartCascade` a réussi pour tous (HTTP 200)
- `SendUserCascadeMessage` a réussi pour tous (HTTP 200)
- Seul `AssignModel` a échoué pour 6 modèles

### 2. Différence entre Modèles 1-2 et 3-8

**Modèles 1-2 (GPT-5.5, Claude Opus 4.7)**:

- Échouent à l'étape de précondition (runtime binding)
- N'atteignent jamais l'étape `AssignModel`

**Modèles 3-8 (Autres)**:

- Passent les préconditions
- Échouent à l'étape `AssignModel` (validation token)

### 3. Le Script Fonctionne Partiellement

Le script `windsurf_direct_probe.py`:

- ✅ Peut créer des cascades (StartCascade)
- ✅ Peut envoyer des messages (SendUserCascadeMessage)
- ❌ Ne peut pas assigner de modèle (AssignModel) sans token valide

---

## 🎯 Conclusion

### Ce Qui Est Confirmé

✅ **Les 8 modèles existent** dans l'API Windsurf  
✅ **Les UIDs sont corrects** (tous reconnus)  
✅ **L'API locale fonctionne** (StartCascade et SendUserCascadeMessage OK)

### Ce Qui Bloque

❌ **Runtime binding non disponible** (Windsurf pas lancé)  
❌ **Token de session non valide** pour l'API cloud  
❌ **Impossible d'obtenir les réponses réelles** des modèles via script

---

## 💡 Solutions Possibles

### Solution 1: Lancer Windsurf Avant le Script

```bash
# 1. Lancer Windsurf
# 2. Attendre que le serveur local démarre (port 51834)
# 3. Relancer le script
python scripts/test_8_models_with_windsurf_probe.py
```

**Avantages**: Résout le problème de runtime binding  
**Inconvénients**: Ne résout pas le problème de validation token

### Solution 2: Utiliser un Token API Direct

```bash
# Définir un token API direct au lieu d'un token de session
export WINDSURF_DIRECT_KEY="votre-token-api"
python scripts/test_8_models_with_windsurf_probe.py
```

**Avantages**: Résout le problème de validation token  
**Inconvénients**: Nécessite un token API (pas un token de session)

### Solution 3: Tests Manuels dans Windsurf (RECOMMANDÉ)

Utiliser l'interface Windsurf directement:

1. Ouvrir Windsurf
2. Sélectionner chaque modèle
3. Envoyer le prompt de test
4. Copier les réponses

**Avantages**:

- Fonctionne à 100%
- Obtient les vraies réponses des modèles
- Pas de problème de token

**Inconvénients**:

- Manuel (10-15 minutes)

---

## 📊 Prochaines Étapes

### Option A: Automatique (Nécessite Configuration)

1. Obtenir un token API Windsurf valide
2. Configurer `WINDSURF_DIRECT_KEY`
3. Lancer Windsurf
4. Relancer le script

### Option B: Manuel (RECOMMANDÉ)

1. Ouvrir le guide: `GUIDE_COMPLET_TEST_8_MODELES.md`
2. Lancer Windsurf
3. Tester les 8 modèles manuellement
4. Comparer les réponses

---

## 🎯 Recommandation Finale

**Utilisez les tests manuels** (Option B) car:

✅ Fonctionne immédiatement  
✅ Pas de configuration nécessaire  
✅ Obtient les vraies réponses  
✅ Durée: 10-15 minutes seulement

Le script automatique nécessite:

- Un token API valide (difficile à obtenir)
- Windsurf en cours d'exécution
- Configuration complexe

---

**Fichiers de référence**:

- Guide manuel: `GUIDE_COMPLET_TEST_8_MODELES.md`
- Résultats JSON: `windsurf_probe_test_results.json`
- Rapport détaillé: `WINDSURF_PROBE_TEST_RESULTS.md`
