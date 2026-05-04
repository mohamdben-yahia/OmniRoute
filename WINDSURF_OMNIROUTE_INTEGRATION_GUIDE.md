# Guide d'Intégration Windsurf → OmniRoute

**Date**: 2026-05-04T01:24:19Z  
**Objectif**: Intégrer les découvertes Windsurf dans OmniRoute

---

## 🎯 Vue d'Ensemble

Suite à l'investigation complète de Windsurf, ce guide fournit les étapes concrètes pour intégrer le support Windsurf dans OmniRoute.

### Découvertes Clés à Intégrer

1. **39 modèles → 1 backend (Cascade/Kimi K2.6)**
   - 18 gratuits + 21 PRO = même backend
   - Performance identique (~8.1s)

2. **14 modèles Claude avec quotas limités**
   - Disponibles sans BYOK
   - Quotas limités
   - Performance différente (+2s)

3. **13 modèles BYOK**
   - Nécessitent configuration externe
   - Vrais modèles différents

---

## 📋 Architecture d'Intégration

### Option 1: Intégration Complète (Recommandée)

**Avantages**:
- Support de tous les modèles Windsurf
- Routage intelligent selon disponibilité
- Gestion des quotas Claude
- Fallback automatique

**Architecture**:

```typescript
// src/lib/windsurf/windsurfBackend.ts

export interface WindsurfBackendConfig {
  port: number;
  csrfToken: string;
  userId: string;
  teamId: string;
  sessionId: string;
}

export type WindsurfModelType = 
  | 'cascade'      // 39 modèles (gratuits + PRO)
  | 'claude-quota' // 14 modèles Claude avec quotas
  | 'byok';        // 13 modèles BYOK

export interface WindsurfModel {
  id: string;
  name: string;
  type: WindsurfModelType;
  backend: string;
  quotaLimited: boolean;
  requiresBYOK: boolean;
}

// Registre des modèles
export const WINDSURF_MODELS: Record<string, WindsurfModel> = {
  // Cascade backend (39 modèles)
  'kimi-k2-6': {
    id: 'kimi-k2-6',
    name: 'Kimi K2.6',
    type: 'cascade',
    backend: 'cascade',
    quotaLimited: false,
    requiresBYOK: false,
  },
  'claude-opus-4': {
    id: 'claude-opus-4',
    name: 'Claude Opus 4 (Cascade)',
    type: 'cascade',
    backend: 'cascade',
    quotaLimited: false,
    requiresBYOK: false,
  },
  // ... (tous les 39 modèles Cascade)
  
  // Claude avec quotas (14 modèles)
  'claude-opus-4-20250514': {
    id: 'claude-opus-4-20250514',
    name: 'Claude Opus 4 (2025-05-14)',
    type: 'claude-quota',
    backend: 'claude',
    quotaLimited: true,
    requiresBYOK: false,
  },
  // ... (tous les 14 modèles Claude)
  
  // BYOK (13 modèles)
  'gpt-5.5': {
    id: 'gpt-5.5',
    name: 'GPT-5.5',
    type: 'byok',
    backend: 'openai',
    quotaLimited: false,
    requiresBYOK: true,
  },
  // ... (tous les 13 modèles BYOK)
};
```

### Option 2: Intégration Minimale

**Avantages**:
- Simple et rapide
- Pas de gestion de quotas
- Utilise uniquement les modèles Cascade

**Architecture**:

```typescript
// src/lib/windsurf/windsurfSimple.ts

export const WINDSURF_CASCADE_MODELS = [
  'kimi-k2-6',
  'claude-opus-4',
  'gpt-5',
  'gemini-3-flash',
  // ... (liste des 39 modèles)
];

export function isWindsurfModel(modelId: string): boolean {
  return WINDSURF_CASCADE_MODELS.includes(modelId);
}

export function getWindsurfBackend(modelId: string): string {
  return isWindsurfModel(modelId) ? 'cascade' : 'unknown';
}
```

---

## 🔧 Implémentation Détaillée

### Étape 1: Auto-Détection Windsurf

**Fichier**: `src/lib/windsurf/autoDetect.ts`

```typescript
import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import path from 'path';

const execAsync = promisify(exec);

export interface WindsurfDetectionResult {
  found: boolean;
  port?: number;
  csrfToken?: string;
  configFile?: string;
}

/**
 * Auto-détecte le port actif du Language Server Windsurf
 */
export async function detectWindsurfPort(): Promise<number | null> {
  try {
    const { stdout } = await execAsync('netstat -ano');
    
    const lines = stdout.split('\n');
    const ports: number[] = [];
    
    for (const line of lines) {
      if (line.includes('LISTENING') && line.includes('127.0.0.1')) {
        const match = line.match(/127\.0\.0\.1:(\d+)/);
        if (match) {
          const port = parseInt(match[1], 10);
          if (port >= 50000 && port <= 60000) {
            ports.push(port);
          }
        }
      }
    }
    
    return ports.length > 0 ? ports[0] : null;
  } catch (error) {
    console.error('Failed to detect Windsurf port:', error);
    return null;
  }
}

/**
 * Recherche le token CSRF dans les fichiers de configuration
 */
export async function findCsrfToken(): Promise<{ token: string; file: string } | null> {
  const searchPaths = [
    process.cwd(),
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Windsurf', 'winsurftiwtest'),
    process.env.HOME || process.env.USERPROFILE || '',
  ];
  
  const searchFiles = [
    'windsurf-live-bootstrap.json',
    'tmp_windsurf_runtime_ls_binding.json',
    '.env.windsurf.local',
  ];
  
  const foundTokens: Array<{ token: string; file: string; modified: Date }> = [];
  
  for (const basePath of searchPaths) {
    for (const fileName of searchFiles) {
      try {
        const filePath = path.join(basePath, fileName);
        const stats = await fs.stat(filePath);
        
        if (fileName.endsWith('.json')) {
          const content = await fs.readFile(filePath, 'utf-8');
          const data = JSON.parse(content);
          
          if (data.csrfToken) {
            foundTokens.push({
              token: data.csrfToken,
              file: filePath,
              modified: stats.mtime,
            });
          }
        } else if (fileName.includes('.env')) {
          const content = await fs.readFile(filePath, 'utf-8');
          const match = content.match(/WINDSURF_CSRF_TOKEN=([a-f0-9-]+)/);
          
          if (match) {
            foundTokens.push({
              token: match[1],
              file: filePath,
              modified: stats.mtime,
            });
          }
        }
      } catch {
        // Fichier non trouvé, continuer
      }
    }
  }
  
  if (foundTokens.length === 0) {
    return null;
  }
  
  // Retourner le token le plus récent
  foundTokens.sort((a, b) => b.modified.getTime() - a.modified.getTime());
  return {
    token: foundTokens[0].token,
    file: foundTokens[0].file,
  };
}

/**
 * Auto-détecte la configuration Windsurf complète
 */
export async function autoDetectWindsurf(): Promise<WindsurfDetectionResult> {
  const port = await detectWindsurfPort();
  
  if (!port) {
    return { found: false };
  }
  
  const csrfResult = await findCsrfToken();
  
  if (!csrfResult) {
    return { found: false };
  }
  
  return {
    found: true,
    port,
    csrfToken: csrfResult.token,
    configFile: csrfResult.file,
  };
}
```

### Étape 2: Client Windsurf

**Fichier**: `src/lib/windsurf/client.ts`

```typescript
import fetch from 'node-fetch';

export interface WindsurfClientConfig {
  port: number;
  csrfToken: string;
  userId: string;
  teamId: string;
  sessionId: string;
}

export interface StartCascadeResponse {
  cascadeId: string;
}

export interface SendMessageResponse {
  success: boolean;
}

export interface GetTrajectoryResponse {
  messages: Array<{
    role: string;
    content: string;
  }>;
  modelAssignmentInfo?: {
    modelRouterUid: string;
  };
}

export class WindsurfClient {
  private config: WindsurfClientConfig;
  private baseUrl: string;
  
  constructor(config: WindsurfClientConfig) {
    this.config = config;
    this.baseUrl = `http://127.0.0.1:${config.port}`;
  }
  
  /**
   * Démarre une nouvelle cascade
   */
  async startCascade(): Promise<string> {
    const response = await fetch(`${this.baseUrl}/StartCascade`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': this.config.csrfToken,
      },
      body: JSON.stringify({
        userId: this.config.userId,
        teamId: this.config.teamId,
        sessionId: this.config.sessionId,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`StartCascade failed: ${response.status}`);
    }
    
    const data = await response.json() as StartCascadeResponse;
    return data.cascadeId;
  }
  
  /**
   * Envoie un message dans une cascade
   */
  async sendMessage(cascadeId: string, message: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/SendUserCascadeMessage`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': this.config.csrfToken,
      },
      body: JSON.stringify({
        cascadeId,
        message,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`SendMessage failed: ${response.status}`);
    }
  }
  
  /**
   * Récupère la trajectoire d'une cascade
   */
  async getTrajectory(cascadeId: string): Promise<GetTrajectoryResponse> {
    const response = await fetch(`${this.baseUrl}/GetCascadeTrajectory`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': this.config.csrfToken,
      },
      body: JSON.stringify({
        cascadeId,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`GetTrajectory failed: ${response.status}`);
    }
    
    return await response.json() as GetTrajectoryResponse;
  }
  
  /**
   * Exécute une requête de chat complète
   */
  async chat(message: string, waitTime: number = 10000): Promise<string> {
    // 1. Démarrer cascade
    const cascadeId = await this.startCascade();
    
    // 2. Envoyer message
    await this.sendMessage(cascadeId, message);
    
    // 3. Attendre la réponse
    await new Promise(resolve => setTimeout(resolve, waitTime));
    
    // 4. Récupérer la trajectoire
    const trajectory = await this.getTrajectory(cascadeId);
    
    // 5. Extraire la réponse
    const assistantMessages = trajectory.messages.filter(m => m.role === 'assistant');
    
    if (assistantMessages.length === 0) {
      throw new Error('No assistant response received');
    }
    
    return assistantMessages[assistantMessages.length - 1].content;
  }
}
```

### Étape 3: Intégration dans OmniRoute

**Fichier**: `src/lib/windsurf/integration.ts`

```typescript
import { WindsurfClient } from './client';
import { autoDetectWindsurf } from './autoDetect';
import { WINDSURF_MODELS, WindsurfModel } from './windsurfBackend';

export interface WindsurfIntegrationConfig {
  enabled: boolean;
  autoDetect: boolean;
  manualConfig?: {
    port: number;
    csrfToken: string;
    userId: string;
    teamId: string;
    sessionId: string;
  };
}

export class WindsurfIntegration {
  private client: WindsurfClient | null = null;
  private config: WindsurfIntegrationConfig;
  
  constructor(config: WindsurfIntegrationConfig) {
    this.config = config;
  }
  
  /**
   * Initialise l'intégration Windsurf
   */
  async initialize(): Promise<boolean> {
    if (!this.config.enabled) {
      return false;
    }
    
    if (this.config.autoDetect) {
      const detection = await autoDetectWindsurf();
      
      if (!detection.found || !detection.port || !detection.csrfToken) {
        console.warn('Windsurf auto-detection failed');
        return false;
      }
      
      // TODO: Récupérer userId, teamId, sessionId depuis les fichiers de config
      this.client = new WindsurfClient({
        port: detection.port,
        csrfToken: detection.csrfToken,
        userId: 'user-a0877fa492bb4eb3b0697a7c72bbb97b', // À récupérer dynamiquement
        teamId: 'devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be', // À récupérer dynamiquement
        sessionId: '20924', // À récupérer dynamiquement
      });
      
      return true;
    }
    
    if (this.config.manualConfig) {
      this.client = new WindsurfClient(this.config.manualConfig);
      return true;
    }
    
    return false;
  }
  
  /**
   * Vérifie si un modèle est supporté par Windsurf
   */
  isWindsurfModel(modelId: string): boolean {
    return modelId in WINDSURF_MODELS;
  }
  
  /**
   * Récupère les informations d'un modèle Windsurf
   */
  getModelInfo(modelId: string): WindsurfModel | null {
    return WINDSURF_MODELS[modelId] || null;
  }
  
  /**
   * Vérifie si un modèle nécessite BYOK
   */
  requiresBYOK(modelId: string): boolean {
    const model = this.getModelInfo(modelId);
    return model?.requiresBYOK || false;
  }
  
  /**
   * Vérifie si un modèle a des quotas limités
   */
  hasQuotaLimits(modelId: string): boolean {
    const model = this.getModelInfo(modelId);
    return model?.quotaLimited || false;
  }
  
  /**
   * Exécute une requête de chat via Windsurf
   */
  async chat(modelId: string, message: string): Promise<string> {
    if (!this.client) {
      throw new Error('Windsurf client not initialized');
    }
    
    if (!this.isWindsurfModel(modelId)) {
      throw new Error(`Model ${modelId} is not a Windsurf model`);
    }
    
    const model = this.getModelInfo(modelId);
    
    if (model?.requiresBYOK) {
      throw new Error(`Model ${modelId} requires BYOK configuration`);
    }
    
    return await this.client.chat(message);
  }
  
  /**
   * Liste tous les modèles Windsurf disponibles
   */
  listAvailableModels(): WindsurfModel[] {
    return Object.values(WINDSURF_MODELS).filter(m => !m.requiresBYOK);
  }
  
  /**
   * Liste les modèles Windsurf par type
   */
  listModelsByType(type: 'cascade' | 'claude-quota' | 'byok'): WindsurfModel[] {
    return Object.values(WINDSURF_MODELS).filter(m => m.type === type);
  }
}
```

---

## 🧪 Tests d'Intégration

**Fichier**: `tests/integration/windsurf.test.ts`

```typescript
import { describe, it, expect, beforeAll } from 'vitest';
import { WindsurfIntegration } from '@/lib/windsurf/integration';
import { autoDetectWindsurf } from '@/lib/windsurf/autoDetect';

describe('Windsurf Integration', () => {
  let integration: WindsurfIntegration;
  
  beforeAll(async () => {
    integration = new WindsurfIntegration({
      enabled: true,
      autoDetect: true,
    });
    
    await integration.initialize();
  });
  
  it('should auto-detect Windsurf configuration', async () => {
    const detection = await autoDetectWindsurf();
    
    expect(detection.found).toBe(true);
    expect(detection.port).toBeGreaterThan(50000);
    expect(detection.port).toBeLessThan(60000);
    expect(detection.csrfToken).toBeTruthy();
  });
  
  it('should identify Windsurf models', () => {
    expect(integration.isWindsurfModel('kimi-k2-6')).toBe(true);
    expect(integration.isWindsurfModel('claude-opus-4')).toBe(true);
    expect(integration.isWindsurfModel('gpt-5')).toBe(true);
    expect(integration.isWindsurfModel('unknown-model')).toBe(false);
  });
  
  it('should identify BYOK models', () => {
    expect(integration.requiresBYOK('gpt-5.5')).toBe(true);
    expect(integration.requiresBYOK('claude-opus-4.7')).toBe(true);
    expect(integration.requiresBYOK('kimi-k2-6')).toBe(false);
  });
  
  it('should identify quota-limited models', () => {
    expect(integration.hasQuotaLimits('claude-opus-4-20250514')).toBe(true);
    expect(integration.hasQuotaLimits('kimi-k2-6')).toBe(false);
  });
  
  it('should list available models', () => {
    const models = integration.listAvailableModels();
    
    expect(models.length).toBeGreaterThan(0);
    expect(models.every(m => !m.requiresBYOK)).toBe(true);
  });
  
  it('should list models by type', () => {
    const cascadeModels = integration.listModelsByType('cascade');
    const claudeQuotaModels = integration.listModelsByType('claude-quota');
    const byokModels = integration.listModelsByType('byok');
    
    expect(cascadeModels.length).toBe(39);
    expect(claudeQuotaModels.length).toBe(14);
    expect(byokModels.length).toBe(13);
  });
  
  it('should execute chat request', async () => {
    const response = await integration.chat('kimi-k2-6', 'Hello, what is 2+2?');
    
    expect(response).toBeTruthy();
    expect(typeof response).toBe('string');
  }, 15000); // 15s timeout
});
```

---

## 📊 Gestion des Quotas

**Fichier**: `src/lib/windsurf/quotaManager.ts`

```typescript
export interface QuotaStatus {
  modelId: string;
  available: boolean;
  exceeded: boolean;
  resetTime?: Date;
  remainingRequests?: number;
}

export class WindsurfQuotaManager {
  private quotaCache: Map<string, QuotaStatus> = new Map();
  
  /**
   * Vérifie le statut du quota pour un modèle
   */
  async checkQuota(modelId: string): Promise<QuotaStatus> {
    const cached = this.quotaCache.get(modelId);
    
    if (cached && cached.resetTime && cached.resetTime > new Date()) {
      return cached;
    }
    
    // TODO: Implémenter la vérification réelle du quota
    // Pour l'instant, retourner un statut par défaut
    const status: QuotaStatus = {
      modelId,
      available: true,
      exceeded: false,
    };
    
    this.quotaCache.set(modelId, status);
    return status;
  }
  
  /**
   * Marque un quota comme dépassé
   */
  markQuotaExceeded(modelId: string, resetTime?: Date): void {
    this.quotaCache.set(modelId, {
      modelId,
      available: false,
      exceeded: true,
      resetTime,
    });
  }
  
  /**
   * Réinitialise le cache des quotas
   */
  resetCache(): void {
    this.quotaCache.clear();
  }
  
  /**
   * Récupère tous les statuts de quotas
   */
  getAllQuotaStatuses(): QuotaStatus[] {
    return Array.from(this.quotaCache.values());
  }
}
```

---

## 🚀 Utilisation dans OmniRoute

### Exemple d'Intégration dans le Routeur

**Fichier**: `src/lib/routing/windsurfRouter.ts`

```typescript
import { WindsurfIntegration } from '@/lib/windsurf/integration';
import { WindsurfQuotaManager } from '@/lib/windsurf/quotaManager';

export class WindsurfRouter {
  private integration: WindsurfIntegration;
  private quotaManager: WindsurfQuotaManager;
  
  constructor() {
    this.integration = new WindsurfIntegration({
      enabled: true,
      autoDetect: true,
    });
    
    this.quotaManager = new WindsurfQuotaManager();
  }
  
  async initialize(): Promise<void> {
    await this.integration.initialize();
  }
  
  /**
   * Route une requête vers Windsurf si applicable
   */
  async routeRequest(modelId: string, message: string): Promise<string | null> {
    // Vérifier si c'est un modèle Windsurf
    if (!this.integration.isWindsurfModel(modelId)) {
      return null;
    }
    
    // Vérifier si BYOK requis
    if (this.integration.requiresBYOK(modelId)) {
      throw new Error(`Model ${modelId} requires BYOK configuration`);
    }
    
    // Vérifier les quotas
    if (this.integration.hasQuotaLimits(modelId)) {
      const quotaStatus = await this.quotaManager.checkQuota(modelId);
      
      if (quotaStatus.exceeded) {
        throw new Error(`Quota exceeded for model ${modelId}`);
      }
    }
    
    // Exécuter la requête
    try {
      const response = await this.integration.chat(modelId, message);
      return response;
    } catch (error) {
      // Vérifier si c'est une erreur de quota
      if (error instanceof Error && error.message.includes('quota')) {
        this.quotaManager.markQuotaExceeded(modelId);
      }
      
      throw error;
    }
  }
}
```

---

## 📝 Configuration Utilisateur

**Fichier**: `src/config/windsurf.config.ts`

```typescript
export interface WindsurfUserConfig {
  enabled: boolean;
  autoDetect: boolean;
  preferredModels: string[];
  fallbackEnabled: boolean;
  fallbackModel: string;
  quotaWarningEnabled: boolean;
  byokKeys?: {
    openai?: string;
    anthropic?: string;
    google?: string;
    zhipu?: string;
  };
}

export const defaultWindsurfConfig: WindsurfUserConfig = {
  enabled: false,
  autoDetect: true,
  preferredModels: ['kimi-k2-6'],
  fallbackEnabled: true,
  fallbackModel: 'kimi-k2-6',
  quotaWarningEnabled: true,
};
```

---

## ✅ Checklist d'Intégration

### Phase 1: Infrastructure de Base
- [ ] Créer `src/lib/windsurf/autoDetect.ts`
- [ ] Créer `src/lib/windsurf/client.ts`
- [ ] Créer `src/lib/windsurf/windsurfBackend.ts`
- [ ] Créer `src/lib/windsurf/integration.ts`
- [ ] Ajouter tests unitaires pour auto-détection
- [ ] Ajouter tests unitaires pour client

### Phase 2: Gestion des Modèles
- [ ] Implémenter registre des 66 modèles
- [ ] Implémenter détection type de modèle
- [ ] Implémenter vérification BYOK
- [ ] Implémenter vérification quotas
- [ ] Ajouter tests pour registre des modèles

### Phase 3: Gestion des Quotas
- [ ] Créer `src/lib/windsurf/quotaManager.ts`
- [ ] Implémenter cache des quotas
- [ ] Implémenter détection quota dépassé
- [ ] Implémenter reset automatique
- [ ] Ajouter tests pour gestion quotas

### Phase 4: Routage
- [ ] Créer `src/lib/routing/windsurfRouter.ts`
- [ ] Implémenter logique de routage
- [ ] Implémenter fallback automatique
- [ ] Implémenter retry sur quota dépassé
- [ ] Ajouter tests d'intégration

### Phase 5: Configuration
- [ ] Créer `src/config/windsurf.config.ts`
- [ ] Implémenter configuration utilisateur
- [ ] Implémenter gestion clés BYOK
- [ ] Ajouter UI de configuration
- [ ] Ajouter documentation utilisateur

### Phase 6: Tests et Documentation
- [ ] Tests unitaires complets
- [ ] Tests d'intégration complets
- [ ] Tests end-to-end
- [ ] Documentation API
- [ ] Guide utilisateur
- [ ] Guide de dépannage

---

## 🔍 Considérations Importantes

### Performance

**Temps de réponse attendus**:
- Modèles Cascade: ~8.1 secondes
- Modèles Claude Quotas: ~10.1 secondes
- Modèles BYOK: Variable selon le modèle

**Recommandations**:
- Implémenter timeout de 15 secondes minimum
- Ajouter retry automatique (max 3 tentatives)
- Implémenter cache des réponses si applicable

### Sécurité

**Tokens et Credentials**:
- Ne jamais logger les tokens CSRF
- Stocker les clés BYOK de manière sécurisée
- Implémenter rotation automatique des tokens

**Validation**:
- Valider tous les inputs utilisateur
- Sanitizer les messages avant envoi
- Vérifier les réponses avant retour

### Fiabilité

**Gestion des Erreurs**:
- Implémenter fallback automatique
- Logger toutes les erreurs
- Notifier l'utilisateur en cas de quota dépassé

**Monitoring**:
- Tracker les taux de succès/échec
- Monitorer les temps de réponse
- Alerter sur quotas proches de la limite

---

## 📚 Ressources

### Documentation Générée

- `WINDSURF_COMPLETE_INVESTIGATION_SUMMARY.md` - Résumé complet
- `WINDSURF_FINAL_COMPLETE_INDEX.md` - Index de tous les fichiers
- `WINDSURF_CLAUDE_QUOTA_MODELS_REPORT.md` - Détails modèles Claude
- `WINDSURF_PRO_SUBSCRIPTION_FINAL_REPORT.md` - Détails modèles PRO
- `WINDSURF_BYOK_VS_SUBSCRIPTION.md` - Comparaison BYOK vs Abonnement

### Scripts de Test

- `test_windsurf_builtin_models_auto.py` - Test modèles gratuits
- `test_windsurf_pro_subscription_models.py` - Test modèles PRO
- `test_windsurf_claude_quota_models.py` - Test modèles Claude
- `test_windsurf_pro_models.py` - Test modèles BYOK
- `windsurf_auto_detect.py` - Auto-détection standalone

---

**Date de création**: 2026-05-04T01:24:19Z  
**Version**: 1.0.0  
**Status**: ✅ PRÊT POUR IMPLÉMENTATION
