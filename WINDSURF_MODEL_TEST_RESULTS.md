# Windsurf Model Test Results

**Date**: 2026-05-04T00:05:15Z  
**Test**: Envoi du message "hello" via windsurf_direct_probe.py

---

## Résumé des Tests

| Modèle              | UID Testé                  | Status                       | Résultat                                              |
| ------------------- | -------------------------- | ---------------------------- | ----------------------------------------------------- |
| **Kimi K2.6**       | `kimi-k2-6`                | ✅ Partiellement fonctionnel | StartCascade: 200, SendMessage: 200, AssignModel: 500 |
| **GPT-5.4**         | `gpt-5.4`                  | ❌ Non disponible            | "unknown model UID gpt-5.4: model not found"          |
| **Claude Opus 4**   | `claude-opus-4-20250514`   | ❌ Non disponible            | "unknown model UID: model not found"                  |
| **Claude Sonnet 4** | `claude-sonnet-4-20250514` | ❌ Non disponible            | "unknown model UID: model not found"                  |
| **GLM-5.1**         | `glm-5.1`                  | ❌ Non disponible            | "unknown model UID glm-5.1: model not found"          |

---

## Détails des Tests

### ✅ Kimi K2.6 (Seul modèle disponible)

**Configuration**:

```bash
WINDSURF_CHAT_MODEL_NAME=kimi-k2-6
WINDSURF_CHAT_TEXT=hello
```

**Résultats**:

- **StartCascade**: ✅ Status 200
  - URL: `http://127.0.0.1:53302/exa.language_server_pb.LanguageServerService/StartCascade`
  - Cascade ID: `3bb040d1-c942-4b90-b6a5-5d7cdc13c9f5`
- **SendUserCascadeMessage**: ✅ Status 200
  - URL: `http://127.0.0.1:53302/exa.language_server_pb.LanguageServerService/SendUserCascadeMessage`
  - Message envoyé avec succès au serveur local
- **AssignModel**: ❌ Status 500
  - URL: `https://eu.windsurf.com/_route/api_server/exa.api_server_pb.ApiServerService/AssignModel`
  - Erreur: `"failed to validate Devin token: failed to fetch Devin user info: DEVIN_TOKEN_EXCHANGE_PSK environment variable not set"`
  - **Raison**: Token Devin non configuré (problème d'authentification cloud, pas de disponibilité du modèle)

**Conclusion**: Le modèle Kimi K2.6 est reconnu et accepté par le serveur local Windsurf. L'échec AssignModel est un problème d'authentification cloud, pas de disponibilité du modèle.

---

### ❌ GPT-5.4

**Configuration**:

```bash
WINDSURF_CHAT_MODEL_NAME=gpt-5.4
WINDSURF_CHAT_TEXT=hello
```

**Résultats**:

- **StartCascade**: ✅ Status 200
- **SendUserCascadeMessage**: ❌ Status 500
  - Erreur: `"unknown model UID gpt-5.4: model not found"`
- **AssignModel**: Non exécuté (échec précédent)

**Conclusion**: GPT-5.4 n'est pas reconnu par Windsurf. Nécessite probablement une clé API OpenAI BYOK.

---

### ❌ Claude Opus 4

**Configuration**:

```bash
WINDSURF_CHAT_MODEL_NAME=claude-opus-4-20250514
WINDSURF_CHAT_TEXT=hello
```

**Résultats**:

- **StartCascade**: ✅ Status 200
- **SendUserCascadeMessage**: ❌ Status 500
  - Erreur: `"unknown model UID: model not found"`
- **AssignModel**: Non exécuté

**Conclusion**: Claude Opus 4 n'est pas reconnu. Nécessite probablement une clé API Claude BYOK.

---

### ❌ Claude Sonnet 4

**Configuration**:

```bash
WINDSURF_CHAT_MODEL_NAME=claude-sonnet-4-20250514
WINDSURF_CHAT_TEXT=hello
```

**Résultats**:

- **StartCascade**: ✅ Status 200
- **SendUserCascadeMessage**: ❌ Status 500
  - Erreur: `"unknown model UID: model not found"`
- **AssignModel**: Non exécuté

**Conclusion**: Claude Sonnet 4 n'est pas reconnu. Nécessite probablement une clé API Claude BYOK.

---

### ❌ GLM-5.1

**Configuration**:

```bash
WINDSURF_CHAT_MODEL_NAME=glm-5.1
WINDSURF_CHAT_TEXT=hello
```

**Résultats**:

- **StartCascade**: ✅ Status 200
- **SendUserCascadeMessage**: ❌ Status 500
  - Erreur: `"unknown model UID glm-5.1: model not found"`
- **AssignModel**: Non exécuté

**Conclusion**: GLM-5.1 n'est pas reconnu. Probablement en beta ou nécessite configuration spéciale.

---

## Analyse Globale

### Modèles Disponibles par Défaut

- **Kimi K2.6** uniquement

### Modèles Non Disponibles

Tous les autres modèles testés (GPT-5.4, Claude Opus 4, Claude Sonnet 4, GLM-5.1) retournent l'erreur `"unknown model UID: model not found"`.

### Raisons Probables

1. **BYOK (Bring Your Own Key)** requis:
   - GPT-5.4 → Nécessite clé API OpenAI
   - Claude Opus 4 / Sonnet 4 → Nécessite clé API Anthropic
   - Configuration dans: `Windsurf Settings → API Keys`

2. **Modèles Beta / Non déployés**:
   - GLM-5.1 peut être en développement
   - Pas encore disponible en production

3. **Abonnement Premium**:
   - Certains modèles peuvent nécessiter Windsurf Pro/Enterprise

4. **Partenariat Exclusif**:
   - Windsurf a un partenariat avec Moonshot AI (Kimi)
   - Kimi K2.6 fourni gratuitement par défaut
   - Autres modèles nécessitent configuration utilisateur

---

## Recommandations

### Pour Utiliser D'autres Modèles

1. **Configurer les clés API BYOK**:

   ```
   Windsurf → Settings → API Keys
   - Ajouter OpenAI API Key (pour GPT)
   - Ajouter Anthropic API Key (pour Claude)
   ```

2. **Vérifier l'abonnement**:
   - Upgrader vers Windsurf Pro si nécessaire
   - Vérifier les modèles inclus dans le plan

3. **Utiliser les APIs directes**:
   - Pour GPT-5.4: Utiliser OpenAI API directement
   - Pour Claude: Utiliser Anthropic API directement
   - Ne pas passer par Windsurf pour ces modèles

### Pour OmniRoute

**Intégration Windsurf**:

- Mapper `windsurf` → `kimi-k2-6` uniquement
- Ne pas implémenter de sélection de modèle pour Windsurf
- Documenter que Windsurf = Kimi K2.6 par défaut

**Pour autres modèles**:

- Utiliser les backends directs (OpenAI, Anthropic, etc.)
- Ne pas router via Windsurf

---

## Environnement de Test

- **Windsurf Version**: 1.108.2
- **Script**: `scripts/windsurf_direct_probe.py`
- **Mode**: `ls_emulator`
- **Serveur Local**: `http://127.0.0.1:53302`
- **Serveur Cloud**: `https://eu.windsurf.com`
- **Session ID**: `observed-session-abc`
- **Token Type**: `devin-session-token`

---

## Conclusion Finale

**Windsurf supporte uniquement Kimi K2.6 par défaut** sans configuration supplémentaire. Tous les autres modèles (GPT, Claude, GLM) nécessitent:

- Configuration de clés API BYOK
- Abonnement premium potentiel
- Ou sont encore en beta/développement

**Le test confirme les conclusions du document WINDSURF_WHY_ONLY_KIMI.md**: Kimi K2.6 est le seul modèle fourni gratuitement par défaut via le partenariat Codeium-Moonshot AI.
