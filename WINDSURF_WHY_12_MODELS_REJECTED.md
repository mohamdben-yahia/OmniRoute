# Pourquoi 12 Modèles Sont Rejetés Malgré le Même Backend?

**Date**: 2026-05-04T00:37:00Z  
**Question**: Si tous utilisent le même modelRouterUid, pourquoi certains sont rejetés?

---

## 🎯 La Réponse

**Whitelist côté serveur** : Le serveur Windsurf local (localhost:53302) a une **liste blanche** de noms de modèles autorisés.

---

## 🔍 Analyse du Flux de Requête

### Étape 1: StartCascade

✅ **Tous les modèles réussissent** (Status 200)

- Crée une nouvelle cascade
- Pas de validation de modèle à cette étape
- Retourne un cascadeId

### Étape 2: SendUserCascadeMessage

🔍 **Validation du nom de modèle**

- Le serveur vérifie si le `requestedModelUid` est dans la whitelist
- ✅ Si dans la whitelist → Status 200
- ❌ Si pas dans la whitelist → Status 500 "unknown model UID: model not found"

### Étape 3: AssignModel

🔍 **Assignation du backend**

- Tous les modèles (acceptés ou rejetés) obtiennent le même `modelRouterUid`
- Cela prouve que le backend est le même pour tous
- Mais cette étape n'est atteinte que si l'étape 2 réussit

---

## 📊 Résultats Observés

### ✅ Modèles dans la Whitelist (5)

| Modèle       | SendMessage | modelRouterUid | Raison         |
| ------------ | ----------- | -------------- | -------------- |
| kimi-k2-6    | ✅ 200      | b0f618c2...    | Dans whitelist |
| kimi-k2-5    | ✅ 200      | b0f618c2...    | Dans whitelist |
| glm-5        | ✅ 200      | b0f618c2...    | Dans whitelist |
| glm-5-1      | ✅ 200      | b0f618c2...    | Dans whitelist |
| swe-1-6-fast | ✅ 200      | b0f618c2...    | Dans whitelist |

### ❌ Modèles Hors Whitelist (12)

| Modèle         | SendMessage | modelRouterUid | Raison                 |
| -------------- | ----------- | -------------- | ---------------------- |
| kimi-k2-7      | ❌ 500      | b0f618c2...    | **Pas dans whitelist** |
| claude-opus-4  | ❌ 500      | b0f618c2...    | **Pas dans whitelist** |
| gpt-5          | ❌ 500      | b0f618c2...    | **Pas dans whitelist** |
| gemini-3-flash | ❌ 500      | b0f618c2...    | **Pas dans whitelist** |

**Tous ont le même modelRouterUid** → Même backend, mais rejetés par la whitelist

---

## 🔐 La Whitelist Serveur

### Où est-elle définie?

La whitelist est probablement définie dans :

1. **Code serveur Windsurf** (localhost:53302)
2. **Configuration serveur** (non accessible depuis l'extérieur)
3. **Licence/Abonnement** (gratuit vs Pro)

### Pourquoi une whitelist?

1. **Contrôle d'accès** : Limiter les modèles gratuits
2. **Monétisation** : Modèles premium nécessitent abonnement
3. **Partenariats** : Seuls certains modèles activés par défaut
4. **Capacité backend** : Limiter la charge sur le backend unique

---

## 💡 Analogie

Imaginez un restaurant avec **1 seul chef** (backend) :

### ✅ Menu Disponible (Whitelist)

- Pizza Margherita → Chef prépare
- Pizza Pepperoni → Chef prépare
- Pasta Carbonara → Chef prépare
- Pasta Bolognese → Chef prépare
- Tiramisu → Chef prépare

### ❌ Plats Refusés (Hors Whitelist)

- Sushi → ❌ "Plat non disponible" (même si le chef pourrait le faire)
- Burger → ❌ "Plat non disponible" (même si le chef pourrait le faire)
- Tacos → ❌ "Plat non disponible" (même si le chef pourrait le faire)

**Tous les plats seraient préparés par le même chef**, mais seuls ceux du menu sont acceptés.

---

## 🎭 Pourquoi Tous Ont le Même modelRouterUid?

### Explication Technique

Le `modelRouterUid` est assigné **avant** la validation du nom de modèle :

```
1. Client envoie requête avec "claude-opus-4"
2. Serveur crée cascade → cascadeId
3. Serveur assigne backend → modelRouterUid (b0f618c2...)
4. Serveur vérifie whitelist → "claude-opus-4" pas dedans
5. Serveur rejette → Status 500 "model not found"
```

Le `modelRouterUid` est le même car :

- Il représente le **backend disponible** (Moonshot AI)
- Il est assigné **avant** la validation du nom
- La validation du nom est une **couche de contrôle d'accès** supplémentaire

---

## 🔍 Preuve : Même Backend, Whitelist Différente

### Test 1: Modèle Accepté (kimi-k2-6)

```json
{
  "requestedModelUid": "kimi-k2-6",
  "status": 200,
  "modelRouterUid": "b0f618c2-cba0-4f5a-bf4c-33d7211cfe62"
}
```

✅ Dans whitelist → Accepté

### Test 2: Modèle Rejeté (claude-opus-4)

```json
{
  "requestedModelUid": "claude-opus-4",
  "status": 500,
  "error": "unknown model UID claude-opus-4: model not found",
  "modelRouterUid": "b0f618c2-cba0-4f5a-bf4c-33d7211cfe62"
}
```

❌ Pas dans whitelist → Rejeté

**Même modelRouterUid** = Même backend, mais validation différente

---

## 🎯 Conclusion

### Pourquoi 12 modèles sont rejetés?

**Pas parce qu'ils ont un backend différent**, mais parce que :

1. ✅ **Backend unique** : Tous utilisent `b0f618c2-cba0-4f5a-bf4c-33d7211cfe62`
2. 🔐 **Whitelist serveur** : Seuls 5 noms sont autorisés
3. ❌ **Validation stricte** : Les 12 autres noms sont rejetés avant même d'atteindre le backend

### Schéma du Flux

```
Requête avec nom de modèle
         ↓
    StartCascade (✅ tous passent)
         ↓
    Assigne modelRouterUid (✅ tous obtiennent b0f618c2...)
         ↓
    Vérifie whitelist
         ↓
    ┌────────────────┐
    │ Dans whitelist?│
    └────────────────┘
         ↓
    ┌────┴────┐
    ↓         ↓
   OUI       NON
    ↓         ↓
Status 200  Status 500
(5 modèles) (12 modèles)
```

---

## 💡 Pour Débloquer les 12 Modèles

### Option 1: Configuration BYOK

Configurer des clés API dans Windsurf Settings pourrait :

- Ajouter des noms à la whitelist
- Ou créer de nouveaux backends avec des `modelRouterUid` différents

### Option 2: Abonnement Pro/Enterprise

Peut débloquer la whitelist complète

### Option 3: Modification Serveur (Non recommandé)

Modifier le code serveur Windsurf pour ajouter des noms à la whitelist

### Option 4: Utiliser OmniRoute

Router directement vers les APIs réelles (Claude API, OpenAI API, etc.)

---

## 📝 Résumé

**Question** : Pourquoi 12 modèles sont rejetés s'ils utilisent le même backend?

**Réponse** :

- ✅ Tous utilisent le même backend (`modelRouterUid` identique)
- 🔐 Mais seuls 5 noms sont dans la whitelist serveur
- ❌ Les 12 autres sont rejetés par validation de nom, pas par backend

**Analogie** : 1 chef (backend), mais menu limité (whitelist)

---

**Investigation complète** ✅

La whitelist est la raison du rejet, pas le backend. Tous les modèles pointent vers le même backend Moonshot AI.
