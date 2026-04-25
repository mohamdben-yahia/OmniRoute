import { WINDSURF_CONFIG } from "../constants/oauth";

function getDisabledMessage(config: typeof WINDSURF_CONFIG): string {
  return (
    config?.disabledMessage ||
    "Windsurf internal auth has been observed in the desktop client, but third-party Windsurf OAuth is unsupported by default. Configure WINDSURF_OAUTH_* only after you have a stable, authorized public OAuth contract."
  );
}

export const windsurf = {
  config: WINDSURF_CONFIG,
  flowType: "authorization_code_pkce",
  buildAuthUrl: (config, redirectUri, state, codeChallenge) => {
    if (!config?.enabled || !config?.authorizeUrl || !config?.clientId || !config?.redirectUri) {
      return null;
    }

    const resolvedRedirectUri = redirectUri || config.redirectUri;

    const params = new URLSearchParams({
      client_id: config.clientId,
      response_type: "code",
      redirect_uri: resolvedRedirectUri,
      scope: Array.isArray(config.scopes) ? config.scopes.join(" ") : "",
      state,
      code_challenge: codeChallenge,
      code_challenge_method: config.codeChallengeMethod || "S256",
    });

    return `${config.authorizeUrl}?${params.toString()}`;
  },
  exchangeToken: async (config, code, _redirectUri, codeVerifier) => {
    const trimmedCode = typeof code === "string" ? code.trim() : "";

    if (!config?.enabled || !config?.tokenUrl || !config?.clientId || !config?.redirectUri) {
      throw new Error(getDisabledMessage(config));
    }

    if (!trimmedCode) {
      throw new Error("Windsurf authorization code is required.");
    }

    const bodyParams: Record<string, string> = {
      grant_type: "authorization_code",
      client_id: config.clientId,
      code: trimmedCode,
      redirect_uri: config.redirectUri,
      code_verifier: codeVerifier,
    };

    if (config.clientSecret) {
      bodyParams.client_secret = config.clientSecret;
    }

    const response = await fetch(config.tokenUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Accept: "application/json",
      },
      body: new URLSearchParams(bodyParams),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Token exchange failed: ${error}`);
    }

    return await response.json();
  },
  mapTokens: (tokens) => ({
    accessToken:
      typeof tokens.access_token === "string"
        ? tokens.access_token
        : typeof tokens.api_key === "string"
          ? tokens.api_key
          : undefined,
    apiKey: typeof tokens.api_key === "string" ? tokens.api_key : undefined,
    refreshToken: typeof tokens.refresh_token === "string" ? tokens.refresh_token : undefined,
    expiresIn:
      typeof tokens.expires_in === "number"
        ? tokens.expires_in
        : typeof tokens.access_token_expires_at === "string"
          ? Math.max(
              1,
              Math.floor((new Date(tokens.access_token_expires_at).getTime() - Date.now()) / 1000)
            )
          : undefined,
    name:
      typeof tokens.name === "string" && tokens.name.trim().length > 0
        ? tokens.name.trim()
        : undefined,
    providerSpecificData: {
      ...(typeof tokens.api_server_url === "string" && tokens.api_server_url.trim().length > 0
        ? { apiServerUrl: tokens.api_server_url.trim() }
        : {}),
      authFlow: "windsurf-oauth-pkce",
    },
    scope: typeof tokens.scope === "string" ? tokens.scope : undefined,
  }),
  metadata: {
    supportLevel: "oauth-ready-placeholder",
    observedInternalAuth: true,
    thirdPartyOAuthSupported: false,
    manualTokenSupported: false,
    disabledMessage: getDisabledMessage(WINDSURF_CONFIG),
  },
};

export default windsurf;
