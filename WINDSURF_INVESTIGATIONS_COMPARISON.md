# 🔍 Comparaison des Investigations Windsurf

**Date de comparaison**: 2026-05-04T14:10:30Z

---

## 📊 Vue d'Ensemble

### Investigation 1: Architecture & Routing (8h00 - 13h40)

- **Focus**: Reverse engineering de l'architecture de routage
- **Méthode**: Analyse statique + tests ciblés
- **Modèles identifiés**: 19 (4 free + 8 pro + 7 byok)
- **Objectif**: Comprendre modelRouterUid et patterns de nommage

### Investigation 2: Identity Testing (14h51)

- **Focus**: Test d'identité des modèles ("what model are you?")
- **Méthode**: Tests en production avec compte PRO
- **Modèles testés**: 78
- **Objectif**: Identifier les backends réels derrière chaque nom

---

## 🎯 Découvertes Clés

### Investigation 1 (Architecture)

✅ **modelRouterUid = session token** (pas identifiant statique)
✅ **Pattern de versioning date-based** pour Pro (`-YYYYMMDD`)
✅ **3 tiers distincts**: free, pro, byok
✅ **4 variantes**: medium, thinking, fast, low

### Investigation 2 (Identity)

✅ **78 modèles testés** avec réponses d'identité
✅ **5 catégories**: Gratuits (18), PRO Subscription (21), Claude Quotas (14), Claude Opus Variants (12), BYOK (13)
✅ **Backends réels identifiés** (GPT-4o, Claude, Gemini, DeepSeek, etc.)
✅ **Compte PRO** utilisé pour les tests

---

## 📊 Comparaison Détaillée

### Modèles Gratuits

**Investigation 1** (4 modèles):

- kimi-k2-6
- kimi-k2-6-e
- glm-5
- glm-5-1

**Investigation 2** (18 modèles):

- cascade
- gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
- claude-opus-4, claude-sonnet-4, claude-haiku-4
- claude-3.5-sonnet, claude-3-opus, claude-3-sonnet, claude-3-haiku
- gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash
- deepseek-chat, deepseek-reasoner
- o1

**Différence**: Investigation 2 a testé beaucoup plus de modèles "gratuits" incluant GPT, Claude, Gemini

### Modèles Pro

**Investigation 1** (8 modèles avec suffixe `-20260424`):

- gpt-5-5-low-20260424
- claude-opus-4-7-medium-20260424
- claude-opus-4-6-thinking-20260424
- claude-sonnet-4-6-thinking-20260424
- deepseek-v4-20260424
- kimi-k2-6-20260424
- swe-1-6-20260424
- swe-1-6-fast-20260424

**Investigation 2** (21 modèles "PRO Subscription"):

- claude-haiku-4.5, claude-haiku-5
- claude-opus-4.5, claude-opus-5
- claude-sonnet-4.5, claude-sonnet-5
- deepseek-v3-pro, deepseek-v4-pro
- gemini-2.5-pro, gemini-3-pro
- gpt-5-pro, gpt-5.5-pro
- kimi-k3-pro
- qwen-max-pro
- ... et plus

**Différence**: Investigation 2 a identifié plus de modèles Pro mais sans le pattern de date

### Modèles BYOK

**Investigation 1** (7 modèles):

- gpt-5-5, gpt-5-4, gpt-5-2-low-thinking
- claude-opus-4-7, claude-opus-4-byok-beta, claude-sonnet-4-byok
- gemini-3-flash-low

**Investigation 2** (13 modèles):

- claude-opus-4-thinking, claude-opus-4.7
- deepseek-r1, deepseek-v3
- gemini-2.5-flash, gemini-2.5-pro, gemini-3-flash
- gpt-4.5, gpt-4.5-mini, gpt-4.5-turbo, gpt-5.5
- qwen-max, qwen-plus

**Différence**: Investigation 2 a identifié plus de modèles BYOK

### Claude Opus Variants (Investigation 2 uniquement)

**12 modèles testés**:

- claude-opus-4.5-20250101, claude-opus-4.5-20250514
- claude-opus-4.5-thinking-20250101, claude-opus-4.5-thinking-20250514
- claude-opus-4.6-20250101, claude-opus-4.6-20250514
- claude-opus-4.6-thinking-20250101, claude-opus-4.6-thinking-20250514
- claude-opus-4.7-20250101, claude-opus-4.7-20250514
- claude-opus-4.7-thinking-20250101, claude-opus-4.7-thinking-20250514

**Note**: Ces modèles utilisent des dates différentes (`-20250101`, `-20250514`) vs notre pattern `-20260424`

### Claude Quotas (Investigation 2 uniquement)

**14 modèles testés**:

- claude-2.0, claude-2.1
- claude-3-haiku-20240307
- claude-3-opus-20240229
- claude-3-sonnet-20240229
- claude-3.5-sonnet-20240620
- claude-3.5-sonnet-20241022
- claude-opus-3, claude-opus-3.5, claude-opus-4
- claude-sonnet-3, claude-sonnet-3.5, claude-sonnet-3.7, claude-sonnet-4

**Note**: Modèles avec quotas limités, différents des modèles Pro

---

## 🔍 Analyse des Différences

### 1. Scope Différent

**Investigation 1**:

- Focus sur l'architecture et le routage
- Tests ciblés sur les modèles avec pattern de date
- Découverte du pattern `-YYYYMMDD` pour Pro

**Investigation 2**:

- Focus sur l'identité des modèles
- Tests exhaustifs de 78 modèles
- Identification des backends réels

### 2. Patterns de Nommage

**Investigation 1** a découvert:

- Pattern Pro: `{provider}-{version}-{variant}-{YYYYMMDD}`
- Date: `20260424` (avril 2026)

**Investigation 2** a testé:

- Dates variées: `20240229`, `20240307`, `20240620`, `20241022`, `20250101`, `20250514`
- Pas de pattern uniforme `-20260424`

**Conclusion**: Le pattern `-20260424` est spécifique à un snapshot de modèles, pas universel

### 3. Catégorisation

**Investigation 1** (3 tiers):

- Free (4)
- Pro (8)
- BYOK (7)

**Investigation 2** (5 catégories):

- Gratuits (18)
- PRO Subscription (21)
- Claude Quotas (14)
- Claude Opus Variants (12)
- BYOK (13)

**Conclusion**: Investigation 2 a une catégorisation plus granulaire

### 4. Backends Réels

**Investigation 1**:

- N'a pas testé les backends réels
- Focus sur le routage et modelRouterUid

**Investigation 2**:

- A testé l'identité de chaque modèle
- Réponses: "I am GPT-4o", "I am Claude Opus 4", etc.
- Identifie les vrais backends vs aliases

---

## 🎯 Modèles Uniques à Chaque Investigation

### Uniquement dans Investigation 1 (8 modèles)

Tous avec suffixe `-20260424`:

- gpt-5-5-low-20260424
- claude-opus-4-7-medium-20260424
- claude-opus-4-6-thinking-20260424
- claude-sonnet-4-6-thinking-20260424
- deepseek-v4-20260424
- kimi-k2-6-20260424
- swe-1-6-20260424
- swe-1-6-fast-20260424

### Uniquement dans Investigation 2 (69 modèles)

Incluant:

- 18 modèles gratuits (GPT, Claude, Gemini, DeepSeek)
- 21 modèles PRO Subscription
- 14 modèles Claude Quotas
- 12 modèles Claude Opus Variants (dates 2025)
- 4 modèles BYOK additionnels

### Modèles Communs (0 modèles)

**Aucun modèle identique** entre les deux investigations!

**Raison**: Investigation 1 utilise le pattern `-20260424`, Investigation 2 utilise des noms sans ce suffixe ou avec d'autres dates

---

## 💡 Insights Combinés

### 1. Système de Versioning Complexe

Windsurf utilise **plusieurs patterns de versioning**:

- **Sans date**: `kimi-k2-6`, `claude-opus-4` (gratuits/aliases)
- **Dates 2024**: `claude-3-opus-20240229` (modèles historiques)
- **Dates 2025**: `claude-opus-4.5-20250101` (snapshots 2025)
- **Dates 2026**: `claude-opus-4-7-medium-20260424` (snapshots 2026)

### 2. Tiers Multiples

Au moins **5 niveaux d'accès**:

1. **Gratuits de base** (18): GPT-4o, Claude 3/4, Gemini, DeepSeek
2. **Free avec quotas** (14): Claude avec quotas limités
3. **Pro Subscription** (21+8): Modèles Pro payants
4. **Claude Opus Variants** (12): Variantes spéciales Claude
5. **BYOK** (13+7): Bring Your Own Key

### 3. Backends vs Aliases

Investigation 2 révèle que certains modèles sont des **aliases**:

- Plusieurs noms → même backend
- Exemple: `cascade` → "I am Kimi" (Moonshot AI)

Investigation 1 a découvert le **mécanisme de routage**:

- modelRouterUid = session token
- Permet de router vers différents backends

### 4. Total Estimé de Modèles

**Combiné**: ~97 modèles uniques

- Investigation 1: 19 modèles
- Investigation 2: 78 modèles
- Overlap: 0 modèles (noms différents)

**Réalité**: Probablement **100+ modèles** disponibles dans Windsurf

---

## 🚀 Recommandations

### Pour OmniRoute

1. **Intégrer les deux investigations**
   - Utiliser Investigation 1 pour l'architecture de routage
   - Utiliser Investigation 2 pour la liste complète des modèles

2. **Supporter plusieurs patterns de date**

   ```typescript
   function detectWindsurfModelTier(modelUid: string) {
     if (modelUid.includes("-byok")) return "byok";
     // Support multiple date patterns
     if (/\d{8}$/.test(modelUid)) return "pro"; // Any YYYYMMDD
     if (modelUid.includes("-pro")) return "pro";
     return "free";
   }
   ```

3. **Catégoriser par niveau d'accès**
   - Free basic (18 modèles)
   - Free with quotas (14 modèles)
   - Pro subscription (29 modèles: 21+8)
   - Claude variants (12 modèles)
   - BYOK (20 modèles: 13+7)

4. **Tester les backends réels**
   - Utiliser la méthode "what model are you?"
   - Identifier les aliases vs vrais modèles
   - Documenter les backends réels

### Pour Investigation Continue

1. **Réconcilier les patterns de date**
   - Tester si `-20260424` est un snapshot spécifique
   - Vérifier si d'autres dates existent
   - Documenter la stratégie de versioning

2. **Mapper les aliases**
   - Identifier quels noms pointent vers le même backend
   - Créer une table alias → backend réel

3. **Tester les modèles manquants**
   - Investigation 1 n'a pas testé les 78 modèles de Investigation 2
   - Investigation 2 n'a pas testé les 8 modèles `-20260424`

---

## 📊 Tableau Récapitulatif

| Aspect                | Investigation 1       | Investigation 2    | Combiné             |
| --------------------- | --------------------- | ------------------ | ------------------- |
| **Date**              | 2026-05-04 (8h-13h40) | 2026-05-04 (14h51) | -                   |
| **Durée**             | ~5.5 heures           | ~1 test            | -                   |
| **Modèles**           | 19                    | 78                 | ~97                 |
| **Focus**             | Architecture          | Identity           | Complet             |
| **Méthode**           | Reverse engineering   | Production testing | -                   |
| **Account**           | Non spécifié          | PRO                | -                   |
| **Pattern découvert** | `-YYYYMMDD`           | Multiples dates    | Versioning complexe |
| **Backends testés**   | Non                   | Oui                | Oui                 |
| **modelRouterUid**    | Élucidé               | Non testé          | Élucidé             |

---

## 🎯 Conclusion

Les deux investigations sont **complémentaires**:

**Investigation 1** a révélé:

- ✅ L'architecture de routage (modelRouterUid = session token)
- ✅ Le pattern de versioning Pro (`-YYYYMMDD`)
- ✅ Les variantes (medium, thinking, fast, low)
- ✅ La structure protobuf

**Investigation 2** a révélé:

- ✅ La liste exhaustive de 78 modèles
- ✅ Les backends réels derrière chaque nom
- ✅ Les 5 catégories d'accès
- ✅ Les aliases vs vrais modèles

**Ensemble**, elles fournissent:

- 🎉 **~97 modèles uniques** identifiés
- 🎉 **Architecture complète** comprise
- 🎉 **Backends réels** documentés
- 🎉 **Patterns de versioning** multiples découverts

**Prochaine étape**: Créer une **table unifiée** combinant les deux investigations.

---

**Date**: 2026-05-04T14:10:30Z  
**Status**: ✅ Comparaison complète  
**Recommandation**: Intégrer les deux investigations dans OmniRoute
