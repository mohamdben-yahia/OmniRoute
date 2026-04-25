import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const TEST_DATA_DIR = fs.mkdtempSync(path.join(os.tmpdir(), "omniroute-windsurf-oauth-route-"));
const ORIGINAL_DATA_DIR = process.env.DATA_DIR;
const ORIGINAL_API_KEY_SECRET = process.env.API_KEY_SECRET;
const ORIGINAL_INITIAL_PASSWORD = process.env.INITIAL_PASSWORD;
const ORIGINAL_FETCH = globalThis.fetch;

process.env.DATA_DIR = TEST_DATA_DIR;
process.env.API_KEY_SECRET = process.env.API_KEY_SECRET || "test-windsurf-oauth-route-secret";
process.env.INITIAL_PASSWORD = "windsurf-oauth-route-password";

const core = await import("../../src/lib/db/core.ts");
const localDb = await import("../../src/lib/localDb.ts");
const oauthRoute = await import("../../src/app/api/oauth/[provider]/[action]/route.ts");

function resetDb() {
  core.resetDbInstance();
  fs.rmSync(TEST_DATA_DIR, { recursive: true, force: true });
  fs.mkdirSync(TEST_DATA_DIR, { recursive: true });
}

test.beforeEach(async () => {
  resetDb();
  await localDb.updateSettings({ requireLogin: false, password: "", cloudEnabled: false });
  globalThis.fetch = async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "https://api.codeium.com/register_user/") {
      return new Response(
        JSON.stringify({
          api_key: "windsurf-api-key-route",
          name: "Windsurf Route User",
          api_server_url: "https://server.codeium.com",
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }
      );
    }
    throw new Error(`Unexpected fetch: ${url}`);
  };
});

test.afterEach(() => {
  globalThis.fetch = ORIGINAL_FETCH;
});

test.after(() => {
  core.resetDbInstance();
  fs.rmSync(TEST_DATA_DIR, { recursive: true, force: true });
  globalThis.fetch = ORIGINAL_FETCH;

  if (ORIGINAL_DATA_DIR === undefined) {
    delete process.env.DATA_DIR;
  } else {
    process.env.DATA_DIR = ORIGINAL_DATA_DIR;
  }

  if (ORIGINAL_API_KEY_SECRET === undefined) {
    delete process.env.API_KEY_SECRET;
  } else {
    process.env.API_KEY_SECRET = ORIGINAL_API_KEY_SECRET;
  }

  if (ORIGINAL_INITIAL_PASSWORD === undefined) {
    delete process.env.INITIAL_PASSWORD;
  } else {
    process.env.INITIAL_PASSWORD = ORIGINAL_INITIAL_PASSWORD;
  }
});

test("GET /api/oauth/windsurf/authorize exposes the Windsurf manual auth token URL", async () => {
  const request = new Request(
    "http://localhost/api/oauth/windsurf/authorize?redirect_uri=http%3A%2F%2Flocalhost%2Fcallback"
  );

  const response = await oauthRoute.GET(request, {
    params: Promise.resolve({ provider: "windsurf", action: "authorize" }),
  });

  assert.equal(response.status, 200);
  const payload = await response.json();
  assert.equal(payload.authUrl, "https://windsurf.com/editor/show-auth-token?workflow=");
  assert.equal(payload.supported, true);
});

test("POST /api/oauth/windsurf/exchange creates a Windsurf oauth connection from a manual auth token", async () => {
  const request = new Request("http://localhost/api/oauth/windsurf/exchange", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      code: "firebase-id-token-from-windsurf",
      redirectUri: "http://localhost/callback",
      codeVerifier: "manual-token-flow",
    }),
  });

  const response = await oauthRoute.POST(request, {
    params: Promise.resolve({ provider: "windsurf", action: "exchange" }),
  });

  assert.equal(response.status, 200);
  const payload = await response.json();
  assert.equal(payload.success, true);
  assert.equal(payload.connection.provider, "windsurf");

  const connections = await localDb.getProviderConnections({ provider: "windsurf" });
  assert.equal(connections.length, 1);

  const created = connections[0] as Record<string, any>;
  assert.equal(created.provider, "windsurf");
  assert.equal(created.authType, "oauth");
  assert.equal(created.apiKey, "windsurf-api-key-route");
  assert.equal(created.accessToken, "windsurf-api-key-route");
  assert.equal(created.name, "Windsurf Route User");
  assert.equal(created.testStatus, "active");
  assert.equal(created.isActive, true);
  assert.equal(created.providerSpecificData?.apiServerUrl, "https://server.codeium.com");
  assert.equal(created.providerSpecificData?.authFlow, "windsurf-manual-auth-token");
});

test("POST /api/oauth/windsurf/exchange rejects empty code", async () => {
  const request = new Request("http://localhost/api/oauth/windsurf/exchange", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      code: "   ",
      redirectUri: "http://localhost/callback",
      codeVerifier: "manual-token-flow",
    }),
  });

  const response = await oauthRoute.POST(request, {
    params: Promise.resolve({ provider: "windsurf", action: "exchange" }),
  });

  assert.equal(response.status, 400);
  const payload = await response.json();
  assert.equal(payload.error.message, "Invalid request");
  assert.deepEqual(payload.error.details, [
    { field: "code", message: "Too small: expected string to have >=1 characters" },
  ]);
});

test("POST /api/oauth/windsurf/exchange rejects invalid JSON body", async () => {
  const request = new Request("http://localhost/api/oauth/windsurf/exchange", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: "{invalid-json",
  });

  const response = await oauthRoute.POST(request, {
    params: Promise.resolve({ provider: "windsurf", action: "exchange" }),
  });

  assert.equal(response.status, 400);
  const payload = await response.json();
  assert.equal(payload.error.message, "Invalid request");
  assert.deepEqual(payload.error.details, [{ field: "body", message: "Invalid JSON body" }]);
});
