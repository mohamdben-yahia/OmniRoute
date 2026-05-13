# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick start

- `npm install` — install dependencies and sync `.env` from `.env.example`
- `npm run dev` — start the Next.js app at `http://localhost:20128`
- `npm run build` — isolated production build
- `npm run start` — run the production build
- `npm run lint` — ESLint across the repo
- `npm run typecheck:core` — core TypeScript check
- `npm run typecheck:noimplicit:core` — stricter TypeScript check
- `npm run check` — lint + unit tests
- `npm run check:cycles` — circular dependency check

## Tests

- `npm run test:unit` — main unit suite (`node:test` + `tsx`)
- `node --import tsx/esm --test tests/unit/your-file.test.ts` — run a single unit test file
- `npm run test:integration` — integration tests
- `npm run test:vitest` — Vitest suite for MCP / autoCombo areas
- `npm run test:e2e` — Playwright end-to-end tests
- `npm run test:protocols:e2e` — MCP + A2A protocol client tests
- `npm run test:ecosystem` — ecosystem compatibility tests
- `npm run test:coverage` — required coverage gate (60% statements / lines / functions / branches)
- `npm run coverage:report` — regenerate the coverage report

## Runtime and toolchain

- Node.js engine is `>=20.20.2 <21 || >=22.22.2 <23 || >=24 <25` (`package.json` is authoritative)
- The repo is ESM (`"type": "module"`)
- Path aliases:
  - `@/*` → `src/*`
  - `@omniroute/open-sse` → `open-sse`
  - `@omniroute/open-sse/*` → `open-sse/*`
- Default local port is `20128`
- Persistent data lives under `DATA_DIR` (defaults to `~/.omniroute/`)

### Running Tests

```bash
# Single test file (Node.js native test runner — most tests)
node --import tsx/esm --test tests/unit/your-file.test.ts

# Vitest (MCP server, autoCombo, cache)
npm run test:vitest

# All suites
npm run test:all
```

For full test matrix, see `CONTRIBUTING.md` → "Running Tests". For deep architecture, see `AGENTS.md`.

---

## Big picture architecture

OmniRoute is a Next.js 16 application wrapped around an internal streaming engine in the `open-sse/` workspace. Most feature work crosses these layers:

1. `src/app/api/v1/*` — Next.js route entrypoints
2. `open-sse/handlers/*` — request orchestration by capability (chat, embeddings, images, search, etc.)
3. `open-sse/translator/*` — format conversion between client/provider APIs
4. `open-sse/executors/*` — provider-specific upstream dispatch
5. `src/lib/db/*` + `src/domain/*` — persistence, policy, quota, routing state
6. `src/app/(dashboard)/*` + `src/shared/components/*` — dashboard UI for providers, combos, analytics, settings

### Chat request path

The core request path is:
**OmniRoute** — unified AI proxy/router. One endpoint, 160+ LLM providers, auto-fallback.

| Layer         | Location                | Purpose                                    |
| ------------- | ----------------------- | ------------------------------------------ |
| API Routes    | `src/app/api/v1/`       | Next.js App Router — entry points          |
| Handlers      | `open-sse/handlers/`    | Request processing (chat, embeddings, etc) |
| Executors     | `open-sse/executors/`   | Provider-specific HTTP dispatch            |
| Translators   | `open-sse/translator/`  | Format conversion (OpenAI↔Claude↔Gemini)   |
| Transformer   | `open-sse/transformer/` | Responses API ↔ Chat Completions           |
| Services      | `open-sse/services/`    | Combo routing, rate limits, caching, etc   |
| Database      | `src/lib/db/`           | SQLite domain modules (22 files)           |
| Domain/Policy | `src/domain/`           | Policy engine, cost rules, fallback logic  |
| MCP Server    | `open-sse/mcp-server/`  | 29 tools, 3 transports, 10 scopes          |
| A2A Server    | `src/lib/a2a/`          | JSON-RPC 2.0 agent protocol                |
| Skills        | `src/lib/skills/`       | Extensible skill framework                 |
| Memory        | `src/lib/memory/`       | Persistent conversational memory           |

Monorepo: `src/` (Next.js 16 app), `open-sse/` (streaming engine workspace), `electron/` (desktop app), `tests/`, `bin/` (CLI entry point).

`src/app/api/v1/chat/completions/route.ts`
→ request validation / auth policy / prompt-injection guard
→ `open-sse/handlers/chatCore.ts`
→ cache + rate-limit + combo routing decisions
→ request translation
→ executor selection
→ upstream fetch / retries / streaming
→ response translation back to client format

When debugging routing or provider behavior, start with `open-sse/handlers/chatCore.ts`, then follow into `open-sse/services/*`, `open-sse/translator/*`, and the relevant executor.

### Provider integration model

Provider integrations usually span multiple places:

## Request Pipeline

```
Client → /v1/chat/completions (Next.js route)
  → CORS → Zod validation → auth? → policy check → prompt injection guard
  → handleChatCore() [open-sse/handlers/chatCore.ts]
    → cache check → rate limit → combo routing?
      → resolveComboTargets() → handleSingleModel() per target
    → translateRequest() → getExecutor() → executor.execute()
      → fetch() upstream → retry w/ backoff
    → response translation → SSE stream or JSON
    → If Responses API: responsesTransformer.ts TransformStream
```

API routes follow a consistent pattern: `Route → CORS preflight → Zod body validation → Optional auth (extractApiKey/isValidApiKey) → API key policy enforcement → Handler delegation (open-sse)`. No global Next.js middleware — interception is route-specific.

**Combo routing** (`open-sse/services/combo.ts`): 13 strategies (priority, weighted, fill-first, round-robin, P2C, random, least-used, cost-optimized, strict-random, auto, lkgp, context-optimized, context-relay). Each target calls `handleSingleModel()` which wraps `handleChatCore()` with per-target error handling and circuit breaker checks.

---

- provider metadata / registry: `src/shared/constants/providers.ts`, `open-sse/config/providerRegistry.ts`
- provider-specific executor: `open-sse/executors/*`
- provider validation / setup checks: `src/lib/providers/validation.ts`
- OAuth providers: `src/lib/oauth/*`
- dashboard provider management: `src/app/(dashboard)/dashboard/providers/*`

## Resilience Runtime State

OmniRoute has three related but distinct temporary-failure mechanisms. Keep their
scope separate when debugging routing behavior.

### Provider Circuit Breaker

**Scope**: whole provider, e.g. `glm`, `openai`, `anthropic`.

**Purpose**: stop sending traffic to a provider that is repeatedly failing at the
upstream/service level, so one unhealthy provider does not slow down every request.

**Implementation**:

- Core class: `src/shared/utils/circuitBreaker.ts`
- Chat gate/execution wiring: `src/sse/handlers/chatHelpers.ts`, `src/sse/handlers/chat.ts`
- Runtime status API: `src/app/api/monitoring/health/route.ts`
- Shared wrappers: `open-sse/services/accountFallback.ts`
- Persisted state table: `domain_circuit_breakers`

**States**:

- `CLOSED`: normal traffic is allowed.
- `OPEN`: provider is temporarily blocked; callers get a provider-circuit-open response
  or combo routing skips to another target.
- `HALF_OPEN`: reset timeout has elapsed; allow a probe request. Success closes the
  breaker, failure opens it again.

**Defaults** (`open-sse/config/constants.ts`):

- OAuth providers: threshold `3`, reset timeout `60s`.
- API-key providers: threshold `5`, reset timeout `30s`.
- Local providers: threshold `2`, reset timeout `15s`.

Only provider-level failure statuses should trip the provider breaker:

```ts
(408, 500, 502, 503, 504);
```

Do not trip the whole-provider breaker for normal account/key/model errors like most
`401`, `403`, or `429` cases. Those usually belong to connection cooldown or model
lockout. A generic API-key provider `403` should be recoverable unless it is classified
as a terminal provider/account error.

The breaker uses lazy recovery, not a background timer. When `OPEN` expires, reads such
as `getStatus()`, `canExecute()`, and `getRetryAfterMs()` refresh the state to
`HALF_OPEN`, so dashboards and combo candidate builders do not keep excluding an
expired provider forever.

### Connection Cooldown

**Scope**: one provider connection/account/key.

**Purpose**: temporarily skip one bad key/account while allowing other connections for
the same provider to continue serving requests.

**Implementation**:

- Write/update path: `src/sse/services/auth.ts::markAccountUnavailable()`
- Account selection/filtering: `src/sse/services/auth.ts::getProviderCredentials...`
- Cooldown calculation: `open-sse/services/accountFallback.ts::checkFallbackError()`
- Settings: `src/lib/resilience/settings.ts`

Important fields on provider connections:

```ts
rateLimitedUntil;
testStatus: "unavailable";
lastError;
lastErrorType;
errorCode;
backoffLevel;
```

During account selection, a connection is skipped while:

```ts
new Date(rateLimitedUntil).getTime() > Date.now();
```

Cooldowns are also lazy: when `rateLimitedUntil` is in the past, the connection becomes
eligible again. On successful use, `clearAccountError()` clears `testStatus`,
`rateLimitedUntil`, error fields, and `backoffLevel`.

Default connection cooldown behavior:

- OAuth base cooldown: `5s`.
- API-key base cooldown: `3s`.
- API-key `429` should prefer upstream retry hints (`Retry-After`, reset headers, or
  parseable reset text) when available.
- Repeated recoverable failures use exponential backoff:

```ts
baseCooldownMs * 2 ** failureIndex;
```

The anti-thundering-herd guard prevents concurrent failures on the same connection from
repeatedly extending the cooldown or double-incrementing `backoffLevel`.

Terminal states are not cooldowns. `banned`, `expired`, and `credits_exhausted` are
intended to stay unavailable until credentials/settings change or an operator resets
them. Do not overwrite terminal states with transient cooldown state.

### Model Lockout

**Scope**: provider + connection + model.

**Purpose**: avoid disabling a whole connection when only one model is unavailable or
quota-limited for that connection.

Examples:

- Per-model quota providers returning `429`.
- Local providers returning `404` for one missing model.
- Provider-specific mode/model permission failures such as selected Grok modes.

Model lockout lives in `open-sse/services/accountFallback.ts` and lets the same
connection continue serving other models.

### Debugging Guidance

- If all keys for a provider are skipped, inspect both provider breaker state and each
  connection's `rateLimitedUntil`/`testStatus`.
- If a provider appears permanently excluded after the reset window, check whether code
  is reading raw `state` instead of using `getStatus()`/`canExecute()`.
- If one provider key fails but others should work, prefer connection cooldown over
  provider breaker.
- If only one model fails, prefer model lockout over connection cooldown.
- If a state should self-recover, it should have a future timestamp/reset timeout and a
  read path that refreshes expired state. Permanent statuses require manual credential
  or config changes.

---

## Key Conventions

For new providers or provider fixes, check all of those seams before assuming the problem is isolated to one file.

### Database model

SQLite is the main persistence layer. Use `src/lib/db/*` domain modules for all reads/writes.

Important rules:

- `src/lib/localDb.ts` is a re-export layer only; do not add logic there
- do not write raw SQL in routes or handlers
- `src/lib/db/core.ts` owns the singleton DB and WAL setup
- migrations live in `src/lib/db/migrations/*`
- **2 spaces**, semicolons, double quotes, 100 char width, es5 trailing commas (enforced by lint-staged via Prettier)
- **Imports**: external → internal (`@/`, `@omniroute/open-sse`) → relative
- **Naming**: files=camelCase/kebab, components=PascalCase, constants=UPPER_SNAKE
- **ESLint**: `no-eval`, `no-implied-eval`, `no-new-func` = error everywhere; `no-explicit-any` = warn in `open-sse/` and `tests/`
- **TypeScript**: `strict: false`, target ES2022, module esnext, resolution bundler. Prefer explicit types.

### Database

- **Always** go through `src/lib/db/` domain modules — **never** write raw SQL in routes or handlers
- **Never** add logic to `src/lib/localDb.ts` (re-export layer only)
- **Never** barrel-import from `localDb.ts` — import specific `db/` modules instead
- DB singleton: `getDbInstance()` from `src/lib/db/core.ts` (WAL journaling)
- Migrations: `src/lib/db/migrations/` — versioned SQL files, idempotent, run in transactions

If a change touches providers, quotas, combos, logs, memories, or secrets, there is usually already a focused DB module for it.

### Protocol/server subsystems

- try/catch with specific error types, log with pino context
- Never swallow errors in SSE streams — use abort signals for cleanup
- Return proper HTTP status codes (4xx/5xx)

This repo is more than a chat proxy:

- `open-sse/mcp-server/*` — MCP server implementation, transports, tool registry, scope enforcement, audit logging
- `src/lib/a2a/*` — A2A protocol support and skill execution
- `src/lib/memory/*` and `src/lib/skills/*` — persistent memory and skill systems used by the product
- `electron/*` — desktop wrapper around the local server/dashboard
- **Never** use `eval()`, `new Function()`, or implied eval
- Validate all inputs with Zod schemas
- Encrypt credentials at rest (AES-256-GCM)
- Upstream header denylist: `src/shared/constants/upstreamHeaders.ts` — keep sanitize, Zod schemas, and unit tests aligned when editing

For deep subsystem behavior, read the nearest scoped `AGENTS.md` first:

- `AGENTS.md` — repo-wide architecture guidance
- `src/lib/db/AGENTS.md` — DB-specific guidance
- `open-sse/services/AGENTS.md` — service-layer guidance

## Working conventions that matter here

- Formatting: 2 spaces, semicolons, double quotes, trailing commas (`es5`), ~100 char width
- Import order: external → `@/` / `@omniroute/open-sse` → relative
- Validate external inputs with Zod schemas
- Never silently swallow SSE-stream errors; use abort-aware cleanup paths
- Keep upstream header sanitization aligned with `src/shared/constants/upstreamHeaders.ts`, its schemas, and related tests when editing header behavior

## Testing and PR expectations

1. Register in `src/shared/constants/providers.ts` (Zod-validated at load)
2. Add executor in `open-sse/executors/` if custom logic needed (extend `BaseExecutor`)
3. Add translator in `open-sse/translator/` if non-OpenAI format
4. Add OAuth config in `src/lib/oauth/constants/oauth.ts` if OAuth-based
5. Register models in `open-sse/config/providerRegistry.ts`
6. Write tests in `tests/unit/`

From the repo instructions and Copilot guidance:

- If you change production code in `src/`, `open-sse/`, `electron/`, or `bin/`, include automated tests in the same change
- Prefer the smallest test layer that proves the behavior:
  - unit first
  - integration when multiple modules or DB state are involved
  - e2e only for real UI/workflow behavior
- For bug fixes, encode the reproduction as an automated test before or alongside the fix
- Treat `npm run test:coverage` as the PR gate for coverage-sensitive work

## Useful adjacent docs

- `README.md` — product overview, supported capabilities, user-facing workflows
- `AGENTS.md` — deeper architecture walkthrough
- `CONTRIBUTING.md` — contribution and test policy details
- `.github/copilot-instructions.md` — coverage and test-layer expectations used by other coding agents

1. Create `src/lib/db/yourModule.ts` — import `getDbInstance` from `./core.ts`
2. Export CRUD functions for your domain table(s)
3. Add migration in `src/lib/db/migrations/` if new tables needed
4. Re-export from `src/lib/localDb.ts` (add to the re-export list only)
5. Write tests

### Adding a New MCP Tool

1. Add tool definition in `open-sse/mcp-server/tools/` with Zod input schema + async handler
2. Register in tool set (wired by `createMcpServer()`)
3. Assign to appropriate scope(s)
4. Write tests (tool invocation logged to `mcp_audit` table)

### Adding a New A2A Skill

1. Create skill in `src/lib/a2a/skills/`
2. Skill receives task context (messages, metadata) → returns structured result
3. Register in the DB-backed skill registry
4. Write tests

---

## Testing

| What                    | Command                                                |
| ----------------------- | ------------------------------------------------------ |
| Unit tests              | `npm run test:unit`                                    |
| Single file             | `node --import tsx/esm --test tests/unit/file.test.ts` |
| Vitest (MCP, autoCombo) | `npm run test:vitest`                                  |
| E2E (Playwright)        | `npm run test:e2e`                                     |
| Protocol E2E (MCP+A2A)  | `npm run test:protocols:e2e`                           |
| Ecosystem               | `npm run test:ecosystem`                               |
| Coverage gate           | `npm run test:coverage` (60% min all metrics)          |
| Coverage report         | `npm run coverage:report`                              |

**PR rule**: If you change production code in `src/`, `open-sse/`, `electron/`, or `bin/`, you must include or update tests in the same PR.

**Test layer preference**: unit first → integration (multi-module or DB state) → e2e (UI/workflow only). Encode bug reproductions as automated tests before or alongside the fix.

**Copilot coverage policy**: When a PR changes production code and coverage is below 60%, do not just report — add or update tests, rerun the coverage gate, then ask for confirmation. Include commands run, changed test files, and final coverage result in the PR report.

---

## Git Workflow

```bash
# Never commit directly to main
git checkout -b feat/your-feature
git commit -m "feat: describe your change"
git push -u origin feat/your-feature
```

**Branch prefixes**: `feat/`, `fix/`, `refactor/`, `docs/`, `test/`, `chore/`

**Commit format** (Conventional Commits): `feat(db): add circuit breaker` — scopes: `db`, `sse`, `oauth`, `dashboard`, `api`, `cli`, `docker`, `ci`, `mcp`, `a2a`, `memory`, `skills`

**Husky hooks**:

- **pre-commit**: lint-staged + `check-docs-sync` + `check:any-budget:t11`
- **pre-push**: `npm run test:unit`

---

## Environment

- **Runtime**: Node.js ≥20.20.2 <21 || ≥22.22.2 <23 || ≥24 <25, ES Modules
- **TypeScript**: 5.9+, target ES2022, module esnext, resolution bundler
- **Path aliases**: `@/*` → `src/`, `@omniroute/open-sse` → `open-sse/`, `@omniroute/open-sse/*` → `open-sse/*`
- **Default port**: 20128 (API + dashboard on same port)
- **Data directory**: `DATA_DIR` env var, defaults to `~/.omniroute/`
- **Key env vars**: `PORT`, `JWT_SECRET`, `API_KEY_SECRET`, `INITIAL_PASSWORD`, `REQUIRE_API_KEY`, `APP_LOG_LEVEL`
- Setup: `cp .env.example .env` then generate `JWT_SECRET` (`openssl rand -base64 48`) and `API_KEY_SECRET` (`openssl rand -hex 32`)

---

## Hard Rules

1. Never commit secrets or credentials
2. Never add logic to `localDb.ts`
3. Never use `eval()` / `new Function()` / implied eval
4. Never commit directly to `main`
5. Never write raw SQL in routes — use `src/lib/db/` modules
6. Never silently swallow errors in SSE streams
7. Always validate inputs with Zod schemas
8. Always include tests when changing production code
9. Coverage must stay ≥60% (statements, lines, functions, branches)
