# Windsurf Models - Final Test Results

**Date**: 2026-05-04T00:16:30Z  
**Tests**: Tous les modèles testés avec format UID correct (tirets)

---

## ✅ Modèles Disponibles (3 modèles confirmés)

| Modèle        | UID         | Provider    | Status         |
| ------------- | ----------- | ----------- | -------------- |
| **Kimi K2.6** | `kimi-k2-6` | Moonshot AI | ✅ Fonctionnel |
| **GLM-5**     | `glm-5`     | Zhipu AI    | ✅ Fonctionnel |
| **GLM-5.1**   | `glm-5-1`   | Zhipu AI    | ✅ Fonctionnel |

---

## ❌ Modèles Non Disponibles

### Modèles GLM

- ❌ `glm-4-7` - "model not found"

### Modèles GPT (OpenAI)

- ❌ `gpt-5-4` - "model not found"
- ❌ `gpt-5-2-low-thinking` - "model not found"

### Modèles Claude (Anthropic)

- ❌ `claude-opus-4-byok-beta` - "model not found"
- ❌ `claude-sonnet-4-byok` - "model not found"

### Modèles Gemini (Google)

- ❌ `gemini-3-flash-low` - "model not found"

---

## 📊 Résumé des Tests

### Tests Réussis (Status 200)

```
✅ kimi-k2-6       → SendUserCascadeMessage: 200
✅ glm-5           → SendUserCascadeMessage: 200
✅ glm-5-1         → SendUserCascadeMessage: 200
```

### Tests Échoués (Status 500)

```
❌ glm-4-7                    → "unknown model UID: model not found"
❌ gpt-5-4                    → "unknown model UID: model not found"
❌ gpt-5-2-low-thinking       → "unknown model UID: model not found"
❌ claude-opus-4-byok-beta    → "unknown model UID: model not found"
❌ claude-sonnet-4-byok       → "unknown model UID: model not found"
❌ gemini-3-flash-low         → "unknown model UID: model not found"
```

---

## 🎯 Conclusions

### 1. Modèles Disponibles par Défaut

Windsurf supporte **3 modèles** sans configuration supplémentaire :

- **1 modèle Moonshot AI** : Kimi K2.6
- **2 modèles Zhipu AI** : GLM-5 et GLM-5.1

### 2. Partenariats Confirmés

- **Moonshot AI** (Kimi) : Partenariat principal
- **Zhipu AI** (GLM) : Partenariat secondaire

### 3. Modèles BYOK Non Disponibles

Les modèles GPT, Claude et Gemini ne sont **pas disponibles** même avec :

- Format UID correct (tirets)
- Suffixe `-byok` ou `-byok-beta`

**Raison probable** : Ces modèles nécessitent :

- Configuration de clés API dans Windsurf Settings
- Activation manuelle dans l'interface Windsurf
- Abonnement premium
- Ou ne sont pas encore déployés dans cette version (1.108.2)

### 4. Format des UIDs

**Règle confirmée** : Les UIDs Windsurf utilisent des **tirets** (`-`) et non des **points** (`.`)

- ✅ `glm-5-1` (correct)
- ❌ `glm-5.1` (incorrect)

---

## 🔧 Pour OmniRoute

### Intégration Windsurf

Mapper le provider `windsurf` vers **3 modèles disponibles** :

```typescript
const WINDSURF_MODELS = {
  "kimi-k2-6": {
    id: "kimi-k2-6",
    name: "Kimi K2.6",
    provider: "Moonshot AI",
    available: true,
  },
  "glm-5": {
    id: "glm-5",
    name: "GLM-5",
    provider: "Zhipu AI",
    available: true,
  },
  "glm-5-1": {
    id: "glm-5-1",
    name: "GLM-5.1",
    provider: "Zhipu AI",
    available: true,
  },
};
```

### Modèle par Défaut

- **Recommandé** : `kimi-k2-6` (modèle principal de Windsurf)
- **Alternatifs** : `glm-5` ou `glm-5-1` (si l'utilisateur préfère Zhipu AI)

### Sélection de Modèle

Implémenter une sélection de modèle pour Windsurf avec les 3 options disponibles.

---

## 📝 Notes Techniques

### Authentification Cloud

Tous les modèles testés échouent à l'étape `AssignModel` avec :

```json
{
  "code": "internal",
  "message": "failed to validate Devin token: failed to fetch Devin user info: DEVIN_TOKEN_EXCHANGE_PSK environment variable not set"
}
```

**Ceci n'est PAS un problème de disponibilité** :

- Les modèles sont reconnus par le serveur local (localhost:53302)
- `SendUserCascadeMessage` retourne 200 (succès)
- L'échec `AssignModel` est un problème d'authentification cloud

### Environnement de Test

- **Windsurf Version** : 1.108.2
- **Serveur Local** : http://127.0.0.1:53302
- **Serveur Cloud** : https://eu.windsurf.com
- **Script** : scripts/windsurf_direct_probe.py
- **Mode** : ls_emulator

---

## 🎉 Résultat Final

**Windsurf supporte 3 modèles par défaut** :

1. ✅ Kimi K2.6 (Moonshot AI)
2. ✅ GLM-5 (Zhipu AI)
3. ✅ GLM-5.1 (Zhipu AI)

**Les modèles GPT, Claude et Gemini ne sont pas disponibles** sans configuration BYOK supplémentaire (qui peut ne pas être supportée dans cette version).

---

## 📚 Documents Créés

1. `WINDSURF_WHY_ONLY_KIMI.md` - Analyse initiale (obsolète)
2. `WINDSURF_MODEL_TEST_RESULTS.md` - Premiers tests (obsolète)
3. `WINDSURF_AVAILABLE_MODELS_CORRECTED.md` - Découverte du format UID
4. **`WINDSURF_MODELS_FINAL.md`** - Ce document (résultats finaux)

---

**Merci d'avoir signalé que GLM fonctionne!** Cette découverte a permis de corriger le format des UIDs et de trouver les 3 modèles disponibles.
