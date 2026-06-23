import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { zaiCodingPlan } from "../../src/lib/oauth/providers/zaiCodingPlan.js";
import { ZAI_CODING_PLAN_CONFIG } from "../../src/lib/oauth/constants/oauth.js";

describe("Z.AI Coding Plan OAuth Provider", () => {
  describe("buildAuthUrl", () => {
    it("should build correct authorization URL with PKCE", () => {
      const redirectUri = "http://localhost:20128/api/oauth/callback";
      const state = "test_state_123";
      
      const authUrl = zaiCodingPlan.buildAuthUrl(ZAI_CODING_PLAN_CONFIG, redirectUri, state);
      
      assert.ok(authUrl.startsWith("https://chat.z.ai/auth/oauth/authorize?"));
      assert.ok(authUrl.includes("response_type=code"));
      assert.ok(authUrl.includes("client_id=client_P8X5CMWmlaRO9gyO-KSqtg"));
      assert.ok(authUrl.includes(`redirect_uri=${encodeURIComponent(redirectUri)}`));
      assert.ok(authUrl.includes(`state=${state}`));
    });
  });

  describe("mapTokens", () => {
    it("should map Z.AI tokens to OmniRoute format", () => {
      const tokens = {
        access_token: "za_test_access_token",
        token_type: "Bearer",
        expires_in: 3600,
        refresh_token: "za_test_refresh_token",
        scope: "coding",
      };

      const mapped = zaiCodingPlan.mapTokens(tokens);

      assert.strictEqual(mapped.accessToken, "za_test_access_token");
      assert.strictEqual(mapped.refreshToken, "za_test_refresh_token");
      assert.strictEqual(mapped.idToken, null);
      assert.strictEqual(mapped.expiresIn, 3600);
      assert.strictEqual(mapped.scope, "coding");
    });

    it("should handle missing refresh token", () => {
      const tokens = {
        access_token: "za_test_token",
        token_type: "Bearer",
      };

      const mapped = zaiCodingPlan.mapTokens(tokens);

      assert.strictEqual(mapped.accessToken, "za_test_token");
      assert.strictEqual(mapped.refreshToken, null);
      assert.strictEqual(mapped.scope, "coding");
    });
  });

  describe("config", () => {
    it("should have correct OAuth endpoints", () => {
      const config = zaiCodingPlan.config;

      assert.strictEqual(config.authorizeUrl, "https://chat.z.ai/auth/oauth/authorize");
      assert.strictEqual(config.tokenUrl, "https://chat.z.ai/auth/oauth/token");
      assert.strictEqual(
        config.apiBaseUrl,
        "https://zcode.z.ai/api/v1/zcode-plan/anthropic"
      );
    });

    it("should have correct client_id from embedded credentials", () => {
      const config = zaiCodingPlan.config;

      // Should resolve to the embedded default (client_P8X5CMWmlaRO9gyO-KSqtg)
      assert.ok(config.clientId);
      assert.ok(config.clientId.startsWith("client_"));
    });

    it("should use PKCE with S256", () => {
      const config = zaiCodingPlan.config;

      assert.strictEqual(config.codeChallengeMethod, "S256");
    });

    it("should have correct redirect URI", () => {
      const config = zaiCodingPlan.config;

      assert.strictEqual(config.redirectUri, "zcode://zai-auth/callback");
    });
  });

  describe("flowType", () => {
    it("should be authorization_code", () => {
      assert.strictEqual(zaiCodingPlan.flowType, "authorization_code");
    });
  });
});
