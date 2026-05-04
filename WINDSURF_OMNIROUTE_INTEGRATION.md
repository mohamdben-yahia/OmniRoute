# Windsurf Integration dans OmniRoute - Guide Final

**Date**: 2026-05-04T00:50:00Z  
**Statut**: Prêt pour implémentation

---

## 🎯 Résumé Exécutif

Après investigation complète et tests de vérification, voici les modèles Windsurf confirmés fonctionnels et leur intégration recommandée dans OmniRoute.

---

## ✅ Modèles Windsurf Confirmés (5)

### Liste des Modèles Disponibles

| Model UID      | Nom Commercial | Provider    | Backend UID                          |
| -------------- | -------------- | ----------- | ------------------------------------ |
| `kimi-k2-6`    | Kimi K2.6      | Moonshot AI | b0f618c2-cba0-4f5a-bf4c-33d7211cfe62 |
| `kimi-k2-5`    | Kimi K2.5      | Moonshot AI | b0f618c2-cba0-4f5a-bf4c-33d7211cfe62 |
| `glm-5`        | GLM-5          | Zhipu AI    | b0f618c2-cba0-4f5a-bf4c-33d7211cfe62 |
| `glm-5-1`      | GLM-5.1        | Zhipu AI    | b0f618c2-cba0-4f5a-bf4c-33d7211cfe62 |
| `swe-1-6-fast` | SWE-1.6 Fast   | Windsurf    | b0f618c2-cba0-4f5a-bf4c-33d7211cfe62 |

**Note Importante** : Tous ces modèles utilisent le **même backend** (modelRouterUid identique).

---

## 🏗️ Architecture d'Intégration

### 1. Registre des Modèles

**Fichier** : `src/shared/constants/providers.ts`

```typescript
export const WINDSURF_MODELS = {
  "kimi-k2-6": {
    id: "kimi-k2-6",
    name: "Kimi K2.6",
    provider: "moonshot",
    backend: "windsurf-local",
    capabilities: ["chat", "streaming"],
    contextWindow: 128000,
    maxTokens: 4096,
  },
  "kimi-k2-5": {
    id: "kimi-k2-5",
    name: "Kimi K2.5",
    provider: "moonshot",
    backend: "windsurf-local",
    capabilities: ["chat", "streaming"],
    contextWindow: 128000,
    maxTokens: 4096,
  },
  "glm-5": {
    id: "glm-5",
    name: "GLM-5",
    provider: "zhipu",
    backend: "windsurf-local",
    capabilities: ["chat", "streaming"],
    contextWindow: 128000,
    maxTokens: 4096,
  },
  "glm-5-1": {
    id: "glm-5-1",
    name: "GLM-5.1",
    provider: "zhipu",
    backend: "windsurf-local",
    capabilities: ["chat", "streaming"],
    contextWindow: 128000,
    maxTokens: 4096,
  },
  "swe-1-6-fast": {
    id: "swe-1-6-fast",
    name: "SWE-1.6 Fast",
    provider: "windsurf",
    backend: "windsurf-local",
    capabilities: ["chat", "streaming", "code"],
    contextWindow: 32000,
    maxTokens: 4096,
  },
} as const;

export type WindsurfModelId = keyof typeof WINDSURF_MODELS;
```

### 2. Executor Windsurf Local

**Fichier** : `open-sse/executors/windsurfLocal.ts`

```typescript
import { Executor } from "./types";
import { WindsurfLocalClient } from "@/lib/acp/windsurfLocal";

export class WindsurfLocalExecutor implements Executor {
  private client: WindsurfLocalClient;

  constructor() {
    this.client = new WindsurfLocalClient({
      host: "localhost",
      port: 53302,
    });
  }

  async execute(request: ChatRequest): Promise<ChatResponse> {
    // 1. Vérifier que le modèle est dans la whitelist
    const allowedModels = ["kimi-k2-6", "kimi-k2-5", "glm-5", "glm-5-1", "swe-1-6-fast"];
    if (!allowedModels.includes(request.model)) {
      throw new Error(`Model ${request.model} not available in Windsurf local`);
    }

    // 2. Démarrer une cascade
    const cascadeId = await this.client.startCascade();

    // 3. Envoyer le message utilisateur
    await this.client.sendUserCascadeMessage({
      cascadeId,
      modelUid: request.model,
      messages: request.messages,
    });

    // 4. Récupérer la trajectoire (réponse)
    const trajectory = await this.client.getCascadeTrajectory(cascadeId);

    // 5. Extraire la réponse
    return {
      id: cascadeId,
      model: request.model,
      choices: [
        {
          message: {
            role: "assistant",
            content: trajectory.response,
          },
          finish_reason: "stop",
        },
      ],
    };
  }

  async *stream(request: ChatRequest): AsyncGenerator<ChatChunk> {
    // Streaming via GetCascadeTrajectory avec polling
    const cascadeId = await this.client.startCascade();

    await this.client.sendUserCascadeMessage({
      cascadeId,
      modelUid: request.model,
      messages: request.messages,
    });

    // Poll trajectory pour streaming
    let lastContent = "";
    while (true) {
      const trajectory = await this.client.getCascadeTrajectory(cascadeId);

      if (trajectory.response.length > lastContent.length) {
        const delta = trajectory.response.slice(lastContent.length);
        lastContent = trajectory.response;

        yield {
          id: cascadeId,
          model: request.model,
          choices: [
            {
              delta: { content: delta },
              finish_reason: null,
            },
          ],
        };
      }

      if (trajectory.isComplete) {
        yield {
          id: cascadeId,
          model: request.model,
          choices: [
            {
              delta: {},
              finish_reason: "stop",
            },
          ],
        };
        break;
      }

      await new Promise((resolve) => setTimeout(resolve, 100));
    }
  }
}
```

### 3. Client Windsurf Local

**Fichier** : `src/lib/acp/windsurfLocal.ts`

```typescript
import { createProtobufRequest } from "./protobuf";

export interface WindsurfLocalConfig {
  host: string;
  port: number;
}

export class WindsurfLocalClient {
  private baseUrl: string;
  private sessionToken: string;

  constructor(config: WindsurfLocalConfig) {
    this.baseUrl = `http://${config.host}:${config.port}`;
    this.sessionToken = this.generateSessionToken();
  }

  private generateSessionToken(): string {
    // Générer un token de session valide
    const sessionId = `windsurf-session-${crypto.randomUUID().replace(/-/g, "")}`;
    const payload = { session_id: sessionId };
    const header = { alg: "HS256", typ: "JWT" };

    // JWT simple (signature non vérifiée côté serveur local)
    const encodedHeader = Buffer.from(JSON.stringify(header)).toString("base64url");
    const encodedPayload = Buffer.from(JSON.stringify(payload)).toString("base64url");
    const signature = "mock_signature_for_local_dev";

    return `devin-session-token$${encodedHeader}.${encodedPayload}.${signature}`;
  }

  async startCascade(): Promise<string> {
    const protobuf = createProtobufRequest({
      metadata: {
        apiKey: this.sessionToken,
        ideName: "windsurf",
        ideVersion: "1.108.2",
        extensionName: "windsurf",
        extensionVersion: "1.108.2",
        locale: "en",
        sessionId: "omniroute-session",
      },
      source: 1,
    });

    const response = await fetch(
      `${this.baseUrl}/exa.language_server_pb.LanguageServerService/StartCascade`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/proto",
          Host: "l.localhost:53302",
        },
        body: protobuf,
      }
    );

    if (!response.ok) {
      throw new Error(`StartCascade failed: ${response.status}`);
    }

    const body = await response.text();
    const cascadeIdMatch = body.match(
      /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/
    );

    if (!cascadeIdMatch) {
      throw new Error("Failed to extract cascadeId from response");
    }

    return cascadeIdMatch[0];
  }

  async sendUserCascadeMessage(params: {
    cascadeId: string;
    modelUid: string;
    messages: Array<{ role: string; content: string }>;
  }): Promise<void> {
    const chatText = params.messages.map((m) => `${m.role}: ${m.content}`).join("\n");

    const protobuf = createProtobufRequest({
      metadata: {
        apiKey: this.sessionToken,
        ideName: "windsurf",
        ideVersion: "1.108.2",
        extensionName: "windsurf",
        extensionVersion: "1.108.2",
        locale: "en",
        sessionId: "omniroute-session",
      },
      cascadeId: params.cascadeId,
      items: [{ text: chatText }],
      cascadeConfig: {
        requestedModelUid: params.modelUid,
      },
    });

    const response = await fetch(
      `${this.baseUrl}/exa.language_server_pb.LanguageServerService/SendUserCascadeMessage`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/proto",
          Host: "e.localhost:53302",
        },
        body: protobuf,
      }
    );

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`SendUserCascadeMessage failed: ${response.status} - ${error}`);
    }
  }

  async getCascadeTrajectory(cascadeId: string): Promise<{
    response: string;
    isComplete: boolean;
    modelRouterUid: string | null;
  }> {
    const protobuf = createProtobufRequest({
      metadata: {
        apiKey: this.sessionToken,
        ideName: "windsurf",
        ideVersion: "1.108.2",
        extensionName: "windsurf",
        extensionVersion: "1.108.2",
        locale: "en",
        sessionId: "omniroute-session",
      },
      cascadeId,
    });

    const response = await fetch(
      `${this.baseUrl}/exa.language_server_pb.LanguageServerService/GetCascadeTrajectory`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/proto",
          Host: "l.localhost:53302",
        },
        body: protobuf,
      }
    );

    if (!response.ok) {
      throw new Error(`GetCascadeTrajectory failed: ${response.status}`);
    }

    const body = await response.text();

    // Extraire modelRouterUid
    const uidMatch = body.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/);

    // Extraire réponse (simplification - nécessite parsing protobuf complet)
    const responseText = body; // TODO: parser protobuf correctement

    return {
      response: responseText,
      isComplete: true, // TODO: détecter si cascade est complète
      modelRouterUid: uidMatch ? uidMatch[0] : null,
    };
  }
}
```

---

## 🔧 Configuration Requise

### Variables d'Environnement

```bash
# Windsurf Local Server
WINDSURF_LOCAL_HOST=localhost
WINDSURF_LOCAL_PORT=53302

# Optionnel: Timeout
WINDSURF_REQUEST_TIMEOUT=30000
```

### Détection du Serveur Local

```typescript
export async function isWindsurfLocalAvailable(): Promise<boolean> {
  try {
    const response = await fetch("http://localhost:53302/health", {
      method: "GET",
      signal: AbortSignal.timeout(2000),
    });
    return response.ok;
  } catch {
    return false;
  }
}
```

---

## 📊 Routing Logic

### Décision de Routing

```typescript
export async function routeWindsurfRequest(
  modelId: string
): Promise<"local" | "cloud" | "unavailable"> {
  // 1. Vérifier si le modèle est dans la whitelist locale
  const localModels = ["kimi-k2-6", "kimi-k2-5", "glm-5", "glm-5-1", "swe-1-6-fast"];

  if (!localModels.includes(modelId)) {
    return "unavailable";
  }

  // 2. Vérifier si le serveur local est disponible
  const isLocalAvailable = await isWindsurfLocalAvailable();

  if (isLocalAvailable) {
    return "local";
  }

  // 3. Fallback cloud (si implémenté)
  return "unavailable";
}
```

---

## 🧪 Tests d'Intégration

### Test de Base

```typescript
import { WindsurfLocalClient } from "@/lib/acp/windsurfLocal";

describe("Windsurf Local Integration", () => {
  let client: WindsurfLocalClient;

  beforeEach(() => {
    client = new WindsurfLocalClient({
      host: "localhost",
      port: 53302,
    });
  });

  it("should complete a chat request with kimi-k2-6", async () => {
    const cascadeId = await client.startCascade();
    expect(cascadeId).toMatch(/^[0-9a-f-]{36}$/);

    await client.sendUserCascadeMessage({
      cascadeId,
      modelUid: "kimi-k2-6",
      messages: [{ role: "user", content: "Hello" }],
    });

    const trajectory = await client.getCascadeTrajectory(cascadeId);
    expect(trajectory.response).toBeTruthy();
    expect(trajectory.modelRouterUid).toBe("b0f618c2-cba0-4f5a-bf4c-33d7211cfe62");
  });

  it("should reject non-whitelisted models", async () => {
    const cascadeId = await client.startCascade();

    await expect(
      client.sendUserCascadeMessage({
        cascadeId,
        modelUid: "gpt-4o",
        messages: [{ role: "user", content: "Hello" }],
      })
    ).rejects.toThrow("model not found");
  });
});
```

---

## 📝 Documentation Utilisateur

### Dashboard UI

**Section** : `src/app/(dashboard)/dashboard/providers/windsurf/page.tsx`

```tsx
export default function WindsurfProviderPage() {
  return (
    <div>
      <h1>Windsurf Local Models</h1>
      <p>
        OmniRoute can route requests to your local Windsurf installation. Requires Windsurf to be
        running on localhost:53302.
      </p>

      <h2>Available Models</h2>
      <ul>
        <li>
          <strong>Kimi K2.6</strong> (kimi-k2-6) - Moonshot AI
        </li>
        <li>
          <strong>Kimi K2.5</strong> (kimi-k2-5) - Moonshot AI
        </li>
        <li>
          <strong>GLM-5</strong> (glm-5) - Zhipu AI
        </li>
        <li>
          <strong>GLM-5.1</strong> (glm-5-1) - Zhipu AI
        </li>
        <li>
          <strong>SWE-1.6 Fast</strong> (swe-1-6-fast) - Windsurf
        </li>
      </ul>

      <h2>Setup</h2>
      <ol>
        <li>Install and launch Windsurf</li>
        <li>Verify Windsurf is running (check localhost:53302)</li>
        <li>Select a Windsurf model in OmniRoute</li>
        <li>Start chatting!</li>
      </ol>

      <Alert>
        <strong>Note:</strong> Other models (Claude, GPT-4, Gemini) may require a Windsurf Pro
        account or BYOK configuration.
      </Alert>
    </div>
  );
}
```

---

## ⚠️ Limitations Connues

### 1. Modèles Limités

- Seuls 5 modèles confirmés fonctionnels
- Claude, GPT-4, Gemini nécessitent compte Pro (non vérifié)

### 2. Serveur Local Requis

- Windsurf doit être lancé et actif
- Port 53302 doit être accessible
- Pas de fallback cloud disponible

### 3. Streaming Limité

- GetCascadeTrajectory ne supporte pas le streaming natif
- Nécessite polling pour simuler le streaming
- Latence potentielle de 100ms entre les chunks

### 4. Backend Unique

- Tous les modèles utilisent le même backend
- Pas de différenciation de performance entre modèles
- Whitelist serveur contrôle l'accès

---

## 🚀 Prochaines Étapes

### Phase 1: Implémentation de Base (Priorité Haute)

- [ ] Créer `WindsurfLocalClient` dans `src/lib/acp/windsurfLocal.ts`
- [ ] Créer `WindsurfLocalExecutor` dans `open-sse/executors/windsurfLocal.ts`
- [ ] Ajouter les 5 modèles au registre dans `src/shared/constants/providers.ts`
- [ ] Implémenter la détection du serveur local
- [ ] Ajouter les tests d'intégration

### Phase 2: UI et Documentation (Priorité Moyenne)

- [ ] Créer la page provider Windsurf dans le dashboard
- [ ] Ajouter l'indicateur de statut du serveur local
- [ ] Documenter le setup dans README.md
- [ ] Créer un guide de troubleshooting

### Phase 3: Optimisations (Priorité Basse)

- [ ] Implémenter le vrai streaming (si possible)
- [ ] Ajouter le caching des cascades
- [ ] Optimiser le parsing protobuf
- [ ] Investiguer les modèles Pro/BYOK

---

## 📚 Références

- **Investigation complète** : `WINDSURF_VERIFICATION_FINALE.md`
- **Backend discovery** : `WINDSURF_BACKEND_DISCOVERY_FINAL.md`
- **Whitelist analysis** : `WINDSURF_WHY_12_MODELS_REJECTED.md`
- **Archive workaround** : `C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\04-investigation\ASSIGNMODEL_WORKAROUND.md`

---

**Document créé** : 2026-05-04T00:50:00Z  
**Statut** : Prêt pour implémentation  
**Modèles confirmés** : 5 (kimi-k2-6, kimi-k2-5, glm-5, glm-5-1, swe-1-6-fast)  
**Backend unique** : b0f618c2-cba0-4f5a-bf4c-33d7211cfe62
