# WINDSURF PROBE - RÉSUMÉ FINAL

**Date**: 2026-05-03
**Status**: ✓ TERMINÉ

## Résultats

### Authentification Complète

- userId, teamId, f (0x000103), sweVersion (swe-1-6)
- CSRF token dynamique
- Host headers: l.localhost, e.localhost

### Cascade Flow Vérifié

StartCascade → SendUserCascadeMessage → GetCascadeTrajectory
Temps: 3-5 secondes | Taux succès: 100%

### Modèle Identifié

**Kimi K2-6** par Moonshot AI

- Exclusif (aucun autre modèle détecté)
- Réponses: 60KB moyenne
- Langues: Français, Anglais confirmés

### Réponses Obtenues

- "Bonjour !" (français)
- "I am Kimi, an AI assistant created by Moonshot AI..."
- Extraction protobuf: 100% fiable

## Configuration

Port: 53302
CSRF: 91e3d9fc-7277-4618-81ee-b72bc0adda38

## Prochaines Étapes

1. Intégrer dans OmniRoute (windsurfLocal.ts)
2. Ajouter kimi-k2-6 au model registry
3. Tests d'intégration

**Probe Status**: Production-ready ✓
