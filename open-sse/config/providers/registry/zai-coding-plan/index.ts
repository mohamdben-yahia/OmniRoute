import type { RegistryEntry } from "../../shared.ts";
import { getAnthropicCompatHeaders } from "../../shared.ts";

/**
 * Z.AI Coding Plan Provider
 * 
 * OAuth-based access to GLM models through ZCode's Anthropic-compatible endpoint.
 * Uses JWT token authentication obtained via the ZCode CLI OAuth flow.
 * 
 * Key differences from standard Z.AI provider:
 * - OAuth authentication (JWT token) instead of API key
 * - Different base URL: /zcode-plan/anthropic vs /api/anthropic
 * - Only exposes 2 models available in the coding plan: GLM-5.2 and GLM-5-Turbo
 * - Anthropic-compatible format (Claude Messages API)
 */
export const zaiCodingPlanProvider: RegistryEntry = {
  id: "zai-coding-plan",
  alias: "zcp",
  format: "claude",
  executor: "default",
  baseUrl: "https://zcode.z.ai/api/v1/zcode-plan/anthropic/v1/messages",
  authType: "bearer", // Uses JWT Bearer token from OAuth
  authHeader: "authorization",
  headers: getAnthropicCompatHeaders(),
  oauth: {
    // OAuth config is primarily in src/lib/oauth/constants/oauth.ts
    // This just marks the provider as OAuth-enabled
    tokenUrl: "https://zcode.z.ai/api/v1/oauth/token",
  },
  // Only 2 models available in the coding plan subscription
  models: [
    {
      id: "glm-5.2",
      name: "GLM 5.2",
      contextWindow: 1000000, // 1M tokens
      maxOutputTokens: 8192,
      reasoning: {
        supportsReasoning: true,
        defaultMode: "enabled",
      },
      kinds: ["chat"],
      modalities: {
        input: ["text"],
        output: ["text"],
      },
    },
    {
      id: "glm-5-turbo",
      name: "GLM 5 Turbo",
      contextWindow: 200000, // 200K tokens
      maxOutputTokens: 64000, // 64K tokens
      reasoning: {
        supportsReasoning: true,
        defaultMode: "enabled",
        modes: ["enabled", "off"],
      },
      kinds: ["chat"],
      modalities: {
        input: ["text"],
        output: ["text"],
      },
    },
  ],
};
