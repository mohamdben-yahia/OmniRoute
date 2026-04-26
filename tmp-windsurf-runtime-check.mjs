import { WINDSURF_CONFIG } from "./src/lib/oauth/constants/oauth.ts";
import { windsurf } from "./src/lib/oauth/providers/windsurf.ts";
console.log(
  JSON.stringify(
    {
      config: WINDSURF_CONFIG,
      authUrl: windsurf.buildAuthUrl(
        WINDSURF_CONFIG,
        "http://localhost/callback",
        "state-123",
        "challenge-456"
      ),
      metadata: windsurf.metadata,
    },
    null,
    2
  )
);
