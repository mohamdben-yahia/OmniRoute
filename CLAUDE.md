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

- provider metadata / registry: `src/shared/constants/providers.ts`, `open-sse/config/providerRegistry.ts`
- provider-specific executor: `open-sse/executors/*`
- provider validation / setup checks: `src/lib/providers/validation.ts`
- OAuth providers: `src/lib/oauth/*`
- dashboard provider management: `src/app/(dashboard)/dashboard/providers/*`

For new providers or provider fixes, check all of those seams before assuming the problem is isolated to one file.

### Database model

SQLite is the main persistence layer. Use `src/lib/db/*` domain modules for all reads/writes.

Important rules:
- `src/lib/localDb.ts` is a re-export layer only; do not add logic there
- do not write raw SQL in routes or handlers
- `src/lib/db/core.ts` owns the singleton DB and WAL setup
- migrations live in `src/lib/db/migrations/*`

If a change touches providers, quotas, combos, logs, memories, or secrets, there is usually already a focused DB module for it.

### Protocol/server subsystems

This repo is more than a chat proxy:

- `open-sse/mcp-server/*` — MCP server implementation, transports, tool registry, scope enforcement, audit logging
- `src/lib/a2a/*` — A2A protocol support and skill execution
- `src/lib/memory/*` and `src/lib/skills/*` — persistent memory and skill systems used by the product
- `electron/*` — desktop wrapper around the local server/dashboard

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
