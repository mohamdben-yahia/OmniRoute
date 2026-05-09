# Résultats Tests - 8 Modèles Windsurf (via windsurf_direct_probe.py)

**Date**: 2026-05-04 15:27:42

**Prompt**: "Quel modèle LLM êtes-vous? Répondez en une phrase courte avec votre nom exact et vos capacités principales."

---

## Résumé

- **Total**: 8 modèles
- **Succès**: 2/8
- **Échecs**: 6/8

---

## 1. GPT-5.5 Low

**UID**: `gpt-5-5-low-20260424`

**Statut**: success

**Longueur réponse**: 1061 caractères

**Réponse**:

```
{
  "mode": "ls_emulator",
  "instrumentation": {
    "observationLayer": "ls_emulator",
    "logChannels": {
      "execution": "ls_emulator.execution",
      "replay": "ls_emulator.replay",
      "transport": "ls_emulator.transport"
    }
  },
  "runObservation": {
    "run": "A",
    "sessionProvenance": null,
    "cascadeId": null,
    "assignedModelUid": null,
    "harnessUid": null,
    "jwtHash16": null,
    "waitingForCascadePreconditions": true,
    "cascadeAllowed": false,
    "preconditionErrors": [
      "runtime binding unreachable"
    ],
    "runtimeState": "RESET_CANDIDATE",
    "bindingSource": "PERSISTED",
    "bindingValidated": false,
    "lastValidationAt": "2026-05-04T14:27:06.299993+00:00",
    "candidateBindings": []
  },
  "startCascade": null,
  "sendUserCascadeMessage": null,
  "assignModel": null,
  "fieldOrigins": {
    "system_native": [],
    "instrumentation_added": [
      "assignModel",
      "instrumentation",
      "mode",
      "runObservation",
      "sendUserCascadeMessage",
      "startCascade"
    ]
  }
}
```

---

## 2. Claude Opus 4.7 Medium

**UID**: `claude-opus-4-7-medium-20260424`

**Statut**: success

**Longueur réponse**: 1061 caractères

**Réponse**:

```
{
  "mode": "ls_emulator",
  "instrumentation": {
    "observationLayer": "ls_emulator",
    "logChannels": {
      "execution": "ls_emulator.execution",
      "replay": "ls_emulator.replay",
      "transport": "ls_emulator.transport"
    }
  },
  "runObservation": {
    "run": "A",
    "sessionProvenance": null,
    "cascadeId": null,
    "assignedModelUid": null,
    "harnessUid": null,
    "jwtHash16": null,
    "waitingForCascadePreconditions": true,
    "cascadeAllowed": false,
    "preconditionErrors": [
      "runtime binding unreachable"
    ],
    "runtimeState": "RESET_CANDIDATE",
    "bindingSource": "PERSISTED",
    "bindingValidated": false,
    "lastValidationAt": "2026-05-04T14:27:14.434931+00:00",
    "candidateBindings": []
  },
  "startCascade": null,
  "sendUserCascadeMessage": null,
  "assignModel": null,
  "fieldOrigins": {
    "system_native": [],
    "instrumentation_added": [
      "assignModel",
      "instrumentation",
      "mode",
      "runObservation",
      "sendUserCascadeMessage",
      "startCascade"
    ]
  }
}
```

---

## 3. Claude Opus 4.6 Thinking

**UID**: `claude-opus-4-6-thinking-20260424`

**Statut**: failed

**Erreur**: Exit code 1

---

## 4. Claude Sonnet 4.6 Thinking

**UID**: `claude-sonnet-4-6-thinking-20260424`

**Statut**: failed

**Erreur**: Exit code 1

---

## 5. DeepSeek V4

**UID**: `deepseek-v4-20260424`

**Statut**: failed

**Erreur**: Exit code 1

---

## 6. Kimi K2.6

**UID**: `kimi-k2-6-20260424`

**Statut**: failed

**Erreur**: Exit code 1

---

## 7. SWE-1.6

**UID**: `swe-1-6-20260424`

**Statut**: failed

**Erreur**: Exit code 1

---

## 8. SWE-1.6 Fast

**UID**: `swe-1-6-fast-20260424`

**Statut**: failed

**Erreur**: Exit code 1

---
