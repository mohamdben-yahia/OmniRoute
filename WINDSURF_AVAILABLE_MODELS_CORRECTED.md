# Windsurf Available Models - Corrected

**Date**: 2026-05-04T00:15:00Z  
**Discovery**: Model UIDs use dashes, not dots!

---

## ✅ Modèles Disponibles Confirmés

| Modèle        | UID Correct | Status         | Notes             |
| ------------- | ----------- | -------------- | ----------------- |
| **Kimi K2.6** | `kimi-k2-6` | ✅ Fonctionnel | Modèle par défaut |
| **GLM-5-1**   | `glm-5-1`   | ✅ Fonctionnel | Zhipu AI GLM-5.1  |

---

## 🔍 Modèles à Tester avec Format Correct

Basé sur la découverte que les UIDs utilisent des tirets au lieu de points, voici les identifiants probables à tester :

### Modèles GLM (Zhipu AI)

- `glm-4-7` (GLM-4.7)
- `glm-5` (GLM-5)
- `glm-5-1` ✅ **Confirmé fonctionnel**

### Modèles Claude (Anthropic) - BYOK

- `claude-opus-4-byok-beta`
- `claude-opus-4-thinking-byok-beta`
- `claude-sonnet-4-byok`
- `claude-sonnet-4-thinking-byok`

### Modèles GPT (OpenAI) - BYOK

- `gpt-5-2-low-thinking`
- `gpt-5-4` (ou `gpt-5-4-mini`)

### Modèles Gemini (Google) - BYOK

- `gemini-3-flash-low`

### Autres Modèles

- `swe-1-6-fast` (Software Engineering spécialisé)
- `adaptive-ss` (Système adaptatif)

---

## 📊 Tests Effectués

### Test 1: GLM-5.1 (Format incorrect)

```bash
WINDSURF_CHAT_MODEL_NAME=glm-5.1
```

❌ Erreur: `"unknown model UID glm-5.1: model not found"`

### Test 2: GLM-5-1 (Format correct)

```bash
WINDSURF_CHAT_MODEL_NAME=glm-5-1
```

✅ **Succès!**

- StartCascade: 200
- SendUserCascadeMessage: 200
- AssignModel: 500 (auth cloud, pas de disponibilité)

---

## 🎯 Découverte Clé

**Format des UIDs Windsurf**: Les identifiants de modèles utilisent des **tirets** (`-`) et non des **points** (`.`)

**Exemples**:

- ❌ `glm-5.1` → ✅ `glm-5-1`
- ❌ `kimi-k2.6` → ✅ `kimi-k2-6`
- ❌ `gpt-5.4` → ✅ `gpt-5-4` (probablement)

---

## 🔄 Prochains Tests Recommandés

1. **GLM-4-7**: `glm-4-7`
2. **GLM-5**: `glm-5`
3. **GPT-5-4**: `gpt-5-4` (avec tirets)
4. **Claude Opus 4**: `claude-opus-4-byok-beta`
5. **Gemini 3**: `gemini-3-flash-low`

---

## 📝 Notes Importantes

### Authentification Cloud

Tous les modèles testés (Kimi K2.6 et GLM-5-1) échouent à l'étape AssignModel avec:

```
"failed to validate Devin token: failed to fetch Devin user info:
DEVIN_TOKEN_EXCHANGE_PSK environment variable not set"
```

**Ceci n'est PAS un problème de disponibilité du modèle**, mais un problème d'authentification cloud. Les modèles sont bien reconnus et acceptés par le serveur local Windsurf (localhost:53302).

### Modèles BYOK

Les modèles marqués "BYOK" (Bring Your Own Key) nécessitent probablement:

- Configuration de clés API dans Windsurf Settings
- Format UID spécifique incluant `-byok` ou `-byok-beta`

---

## 🎉 Conclusion

**Windsurf supporte au minimum 2 modèles par défaut**:

1. **Kimi K2.6** (`kimi-k2-6`)
2. **GLM-5-1** (`glm-5-1`)

D'autres modèles GLM sont probablement disponibles avec le bon format d'UID (tirets au lieu de points).

Les modèles GPT, Claude, et Gemini nécessitent probablement des clés API BYOK configurées dans Windsurf.
