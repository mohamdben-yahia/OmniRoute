import { ZAI_CODING_PLAN_CONFIG } from "../constants/oauth";

/**
 * Z.AI Coding Plan OAuth Provider
 *
 * Uses standard OAuth 2.0 Authorization Code flow with PKCE:
 * - Authorization URL: https://chat.z.ai/auth/oauth/authorize
 * - Client ID: client_P8X5CMWmlaRO9gyO-KSqtg (from ZCode binary)
 * - Redirect URI: zcode://zai-auth/callback (custom URI scheme)
 * - Code Challenge Method: S256 (SHA-256)
 * 
 * Flow:
 * 1. Build authorization URL with PKCE code_challenge
 * 2. User authorizes in browser → redirect to zcode:// with code
 * 3. Exchange code for access_token
 * 4. Use access_token as Bearer token for API calls
 */

interface ZaiTokenResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
  refresh_token?: string;
  scope?: string;
}

export const zaiCodingPlan = {
  config: ZAI_CODING_PLAN_CONFIG,
  flowType: "authorization_code",

  /**
   * Build authorization URL with PKCE
   */
  buildAuthUrl: (config: typeof ZAI_CODING_PLAN_CONFIG, redirectUri: string, state: string) => {
    const params = new URLSearchParams({
      response_type: "code",
      client_id: config.clientId,
      redirect_uri: redirectUri,
      state: state,
    });
    
    return `${config.authorizeUrl}?${params.toString()}`;
  },

  /**
   * Exchange authorization code for access token
   */
  exchangeToken: async (
    config: typeof ZAI_CODING_PLAN_CONFIG,
    code: string,
    redirectUri: string
  ) => {
    const response = await fetch(config.tokenUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Accept: "application/json",
      },
      body: new URLSearchParams({
        grant_type: "authorization_code",
        client_id: config.clientId,
        code: code,
        redirect_uri: redirectUri,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Z.AI token exchange failed: ${error}`);
    }

    return await response.json();
  },

  /**
   * Map tokens to OmniRoute format
   */
  mapTokens: (tokens: ZaiTokenResponse) => ({
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token || null,
    idToken: null,
    expiresIn: tokens.expires_in,
    scope: tokens.scope || "coding",
  }),
};
