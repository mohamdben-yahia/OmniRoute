# Guide: Comment Activer les Autres Modèles dans Windsurf

**Date**: 2026-05-03T23:49:00Z
**Objectif**: Activer Claude, GPT, Gemini et autres modèles dans Windsurf

---

## Étape 1: Vérifier les Paramètres Actuels

### Ouvrir les Paramètres Windsurf

```
Windows: Ctrl + ,
Mac: Cmd + ,
Ou: File → Preferences → Settings
```

### Chercher "Models" ou "API Keys"

Dans la barre de recherche des paramètres, taper:

- `models`
- `api keys`
- `llm`

---

## Étape 2: Configurer les Clés API

### Pour les Modèles Claude (BYOK)

1. **Obtenir une clé API Anthropic**:
   - Aller sur https://console.anthropic.com
   - Créer un compte ou se connecter
   - Aller dans "API Keys"
   - Créer une nouvelle clé
   - Copier la clé (commence par `sk-ant-...`)

2. **Configurer dans Windsurf**:

   ```
   Settings → API Keys → Claude API Key
   Coller: sk-ant-api03-xxxxx...
   ```

3. **Modèles qui seront disponibles**:
   - Claude Opus 4 BYOK Beta
   - Claude Opus 4 Thinking BYOK Beta
   - Claude Sonnet 4 BYOK
   - Claude Sonnet 4 Thinking BYOK

### Pour les Modèles GPT

1. **Obtenir une clé API OpenAI**:
   - Aller sur https://platform.openai.com
   - Créer un compte ou se connecter
   - Aller dans "API Keys"
   - Créer une nouvelle clé
   - Copier la clé (commence par `sk-...`)

2. **Configurer dans Windsurf**:

   ```
   Settings → API Keys → OpenAI API Key
   Coller: sk-xxxxx...
   ```

3. **Modèles qui seront disponibles**:
   - GPT-5.2 Low Thinking
   - GPT-4 Turbo
   - GPT-4

### Pour les Modèles Gemini

1. **Obtenir une clé API Google**:
   - Aller sur https://makersuite.google.com/app/apikey
   - Créer un compte ou se connecter
   - Créer une nouvelle clé API
   - Copier la clé

2. **Configurer dans Windsurf**:

   ```
   Settings → API Keys → Google API Key
   Coller: AIzaSy...
   ```

3. **Modèles qui seront disponibles**:
   - Gemini 3 Flash Low
   - Gemini Pro

### Pour les Modèles GLM (Zhipu AI)

1. **Obtenir une clé API Zhipu**:
   - Aller sur https://open.bigmodel.cn
   - Créer un compte (peut nécessiter numéro chinois)
   - Obtenir clé API

2. **Configurer dans Windsurf**:

   ```
   Settings → API Keys → Zhipu API Key
   Coller la clé
   ```

3. **Modèles qui seront disponibles**:
   - GLM-4.7 Beta
   - GLM-5
   - GLM-5.1

---

## Étape 3: Activer les Modèles

### Dans les Paramètres Windsurf

```
Settings → Models → Available Models
```

Cocher les modèles que vous voulez activer:

- [ ] Adaptive SS
- [ ] Claude Opus 4 BYOK Beta
- [ ] Claude Opus 4 Thinking BYOK Beta
- [ ] Claude Sonnet 4 BYOK
- [ ] Claude Sonnet 4 Thinking BYOK
- [ ] GLM4.7 Beta
- [ ] GLM-5
- [ ] SWE-1.6Fast
- [ ] Gemini 3 Flash Low
- [ ] GLM-5.1
- [ ] GPT-5.2 Low Thinking
- [ ] Kimi K2.5
- [x] Kimi K2.6 (déjà activé)

---

## Étape 4: Sélectionner un Modèle

### Dans l'Interface Chat

1. **Ouvrir le panneau de chat Cascade**
2. **Cliquer sur le sélecteur de modèle** (en haut)
3. **Choisir le modèle désiré**:
   - Kimi K2.6 (gratuit, par défaut)
   - Claude Opus 4 (si clé configurée)
   - GPT-5.2 (si clé configurée)
   - etc.

### Via Commande

```
Ctrl+Shift+P (Windows) ou Cmd+Shift+P (Mac)
Taper: "Cascade: Select Model"
Choisir le modèle
```

---

## Étape 5: Vérifier que ça Fonctionne

### Test Rapide

1. **Ouvrir le chat Cascade**
2. **Sélectionner un modèle (ex: Claude Opus 4)**
3. **Envoyer un message**: "What model are you?"
4. **Vérifier la réponse**:
   - Si Claude: "I am Claude..."
   - Si GPT: "I am ChatGPT..." ou "I am GPT..."
   - Si erreur: Vérifier la clé API

---

## Coûts et Limites

### Kimi K2.6 (Gratuit)

- ✓ Inclus gratuitement
- ✓ Pas de limite stricte
- ⚠️ Rate limiting possible (5 min reset)

### Claude BYOK

- 💰 Payant (facturation Anthropic)
- Prix: ~$15/million tokens (Opus 4)
- Nécessite crédits sur compte Anthropic

### GPT BYOK

- 💰 Payant (facturation OpenAI)
- Prix: Variable selon modèle
- Nécessite crédits sur compte OpenAI

### Gemini BYOK

- 💰 Gratuit jusqu'à limite, puis payant
- Quota gratuit: 60 requêtes/minute
- Au-delà: Facturation Google Cloud

### GLM BYOK

- 💰 Payant (facturation Zhipu AI)
- Prix: Variable selon modèle
- Nécessite compte Zhipu

---

## Dépannage

### Problème: "API Key Invalid"

**Solution**:

1. Vérifier que la clé est correcte (copier-coller complet)
2. Vérifier que la clé n'a pas expiré
3. Vérifier que le compte a des crédits
4. Régénérer une nouvelle clé si nécessaire

### Problème: "Model Not Available"

**Solution**:

1. Vérifier que la clé API est configurée
2. Vérifier que le modèle est coché dans Settings
3. Redémarrer Windsurf
4. Mettre à jour Windsurf vers la dernière version

### Problème: "Rate Limit Exceeded"

**Solution**:

1. Attendre le reset (généralement 1-5 minutes)
2. Utiliser un autre modèle temporairement
3. Upgrader le plan API si limites trop basses

### Problème: Modèle Toujours Pas Visible

**Solution**:

1. Vérifier la version de Windsurf (doit être récente)
2. Vérifier que le modèle n'est pas en beta fermée
3. Contacter le support Windsurf
4. Vérifier les logs: `Help → Toggle Developer Tools → Console`

---

## Alternative: Utiliser OmniRoute

### Si Configuration Windsurf Trop Complexe

Au lieu de configurer tous les modèles dans Windsurf, utiliser **OmniRoute** comme proxy:

1. **Configurer OmniRoute** avec vos clés API
2. **Pointer Windsurf vers OmniRoute** (si possible)
3. **OmniRoute gère** le routing vers les bons modèles
4. **Avantages**:
   - Configuration centralisée
   - Meilleure gestion des quotas
   - Analytics et monitoring
   - Fallback automatique

---

## Commandes Utiles

### Vérifier les Modèles Disponibles

```javascript
// Dans Developer Tools Console (F12)
// Peut ne pas fonctionner selon version Windsurf
console.log(window.cascade?.availableModels);
```

### Forcer Refresh des Modèles

```
Ctrl+Shift+P → "Developer: Reload Window"
```

### Voir les Logs d'Erreur

```
Help → Toggle Developer Tools → Console
Filtrer par "model" ou "api"
```

---

## Résumé

### Pour Activer les Autres Modèles:

1. ✓ Obtenir les clés API nécessaires
2. ✓ Configurer dans Windsurf Settings → API Keys
3. ✓ Activer dans Settings → Models
4. ✓ Sélectionner dans l'interface Chat
5. ✓ Tester avec un message

### Si Ça Ne Marche Pas:

- Vérifier la version de Windsurf
- Vérifier les logs d'erreur
- Contacter le support
- Utiliser OmniRoute comme alternative

---

**Note**: Ce guide est basé sur l'analyse de Windsurf 1.108.2. Les étapes exactes peuvent varier selon la version. Consulter la documentation officielle Windsurf pour les instructions les plus à jour.
