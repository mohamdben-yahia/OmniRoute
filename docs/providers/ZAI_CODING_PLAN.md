# Z.AI Coding Plan Provider

> **Provider ID:** `zai-coding-plan`
> **Alias:** `zcp`
> **Format:** Anthropic-compatible (Claude Messages API)
> **Authentication:** OAuth 2.0 with PKCE (JWT token-based)
> **Added:** v3.8.32 (2026-06-23)

## Overview

Z.AI Coding Plan is a subscription-based service that provides access to GLM models through an Anthropic-compatible API endpoint. It uses a custom OAuth flow based on the ZCode CLI authentication pattern.

## Authentication Flow

### OAuth PKCE Flow

Unlike standard OAuth providers, Z.AI Coding Plan uses a custom three-step flow:

1. **Initialize** (`POST /oauth/cli/init`)
   - Generate a 32-byte hex poll token
   - Request a flow_id and authorization URL
   - Server returns browser URL for user authentication

2. **User Authorization**
   - Open the authorize_url in a browser
   - User logs in and authorizes the application
   - No callback URL - uses polling instead

3. **Poll for Completion** (`GET /oauth/cli/poll/{flow_id}`)
   - Poll every 3 seconds for up to 5 minutes
   - Server returns JWT token when ready
   - Extract both `jwt_token` (for storage) and `access_token` (for API calls)

### Environment Variables

Add to your `.env` file:

```bash
# Z.AI Coding Plan OAuth Client ID (optional - will use default if not set)
ZAI_CODING_PLAN_CLIENT_ID=your_client_id_here
```

## API Endpoints

| Endpoint | URL |
|----------|-----|
| Base API | `https://zcode.z.ai/api/v1` |
| OAuth Init | `https://zcode.z.ai/api/v1/oauth/cli/init` |
| OAuth Poll | `https://zcode.z.ai/api/v1/oauth/cli/poll/{flow_id}` |
| Token Exchange | `https://zcode.z.ai/api/v1/oauth/token` |
| Chat API | `https://zcode.z.ai/api/v1/zcode-plan/anthropic/v1/messages` |

## Available Models

The Coding Plan subscription provides access to 2 GLM models:

### GLM-5.2
- **Model ID:** `glm-5.2`
- **Context Window:** 1,000,000 tokens (1M)
- **Max Output:** 8,192 tokens
- **Reasoning:** Supported (enabled by default)
- **Modalities:** text → text

### GLM-5-Turbo
- **Model ID:** `glm-5-turbo`
- **Context Window:** 200,000 tokens (200K)
- **Max Output:** 64,000 tokens (64K)
- **Reasoning:** Supported with modes (`enabled`, `off`)
- **Modalities:** text → text

## Usage Example

### 1. Setup OAuth Connection

```bash
# In OmniRoute dashboard
1. Navigate to Providers → Z.AI Coding Plan
2. Click "Connect via OAuth"
3. Open the authorization URL in your browser
4. Complete authentication in ZCode
5. Wait for polling to complete (typically 10-30 seconds)
```

### 2. API Request

```bash
curl https://your-omniroute-instance/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_OMNIROUTE_API_KEY" \
  -d '{
    "model": "zai-coding-plan/glm-5.2",
    "messages": [
      {
        "role": "user",
        "content": "Explain async/await in JavaScript"
      }
    ]
  }'
```

### 3. OpenAI SDK

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://your-omniroute-instance/v1",
  apiKey: "YOUR_OMNIROUTE_API_KEY",
});

const response = await client.chat.completions.create({
  model: "zai-coding-plan/glm-5.2",
  messages: [
    { role: "user", content: "Write a quicksort in Python" }
  ],
});

console.log(response.choices[0].message.content);
```

## Comparison with Standard Z.AI Provider

| Feature | `zai` (API Key) | `zai-coding-plan` (OAuth) |
|---------|-----------------|---------------------------|
| **Authentication** | API Key (`x-api-key`) | OAuth JWT (`Bearer`) |
| **Base URL** | `api.z.ai/api/anthropic` | `zcode.z.ai/api/v1/zcode-plan/anthropic` |
| **Models Available** | 6 models (GLM-5.2, GLM-5.1, GLM-5, GLM-5-Turbo, GLM-4.7-Flash, GLM-4.7) | 2 models (GLM-5.2, GLM-5-Turbo) |
| **Subscription** | Pay-per-use | Fixed plan (coding subscription) |
| **Setup** | Direct API key | Browser OAuth flow |

## Technical Implementation

### Provider Registration

- **Location:** `src/shared/constants/providers.ts`
- **Provider Entry:** `zai-coding-plan`
- **Service Kinds:** `llm`
- **Risk Notice:** OAuth variant

### OAuth Provider

- **Location:** `src/lib/oauth/providers/zaiCodingPlan.ts`
- **Config:** `src/lib/oauth/constants/oauth.ts` → `ZAI_CODING_PLAN_CONFIG`
- **Flow Type:** Custom PKCE with polling
- **Token Format:** JWT (stored in `idToken` field)

### Model Registry

- **Location:** `open-sse/config/providers/registry/zai-coding-plan/index.ts`
- **Format:** `claude` (Anthropic-compatible)
- **Executor:** `default`
- **Auth Type:** `bearer`

## Troubleshooting

### OAuth Flow Timeout

**Symptom:** Poll times out after 5 minutes without completing

**Solution:**
1. Ensure you opened the authorize_url in a browser
2. Check that you completed the authentication in ZCode
3. Verify the poll_token is correctly generated (32 bytes hex)

### Invalid JWT Token

**Symptom:** API returns 401 Unauthorized with JWT

**Solution:**
1. JWT tokens may expire - re-run OAuth flow
2. Check that the token is stored in the `idToken` field
3. Verify the `Bearer` prefix is added to the Authorization header

### Model Not Found

**Symptom:** API returns "model not found" error

**Solution:**
1. Only `glm-5.2` and `glm-5-turbo` are available in coding plan
2. Use the full provider prefix: `zai-coding-plan/glm-5.2`
3. Verify your subscription includes the coding plan

## Security Considerations

- **JWT Token Storage:** Tokens are stored encrypted in OmniRoute's database
- **No Refresh Tokens:** Z.AI uses long-lived JWT tokens, no refresh mechanism
- **Public Client:** OAuth client_id is public (embedded in ZCode CLI binary)
- **PKCE Security:** The code_verifier provides security, not client_secret confidentiality

## References

- [Z.AI Official Website](https://zcode.z.ai)
- [GLM Model Documentation](https://open.bigmodel.cn)
- [OAuth 2.0 PKCE RFC 7636](https://tools.ietf.org/html/rfc7636)
- [OmniRoute OAuth Guide](../architecture/AUTHZ_GUIDE.md)

## Changelog

### v3.8.32 (2026-06-23)
- Initial release of Z.AI Coding Plan provider
- OAuth PKCE flow with custom polling implementation
- Support for GLM-5.2 and GLM-5-Turbo models
- Anthropic-compatible API format
