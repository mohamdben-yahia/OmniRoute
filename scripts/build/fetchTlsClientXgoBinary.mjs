#!/usr/bin/env node

/**
 * Fallback download for tls-client-node's native binary when the upstream
 * bogdanfinn/tls-client release changes its asset naming convention.
 *
 * The tls-client-node npm package (v0.2.0) expects assets named
 * `tls-client-linux-ubuntu-amd64-{VERSION}.so`, but starting with v1.16.0
 * the upstream project only publishes `tls-client-xgo-{VERSION}-linux-amd64.so`.
 * The package's own postinstall.js silently skips the download when the old-named
 * asset is missing (it never throws — it only console.warn's and exits 0), so
 * bin/ ends up empty.
 *
 * This script:
 *   1. No-ops if bin/ already contains a file (standard postinstall succeeded).
 *   2. Queries the GitHub Releases API for the latest bogdanfinn/tls-client release.
 *   3. Finds the xgo-named asset for the current platform/arch (fallback to old name).
 *   4. Downloads it into node_modules/tls-client-node/bin/.
 *   5. Exits non-zero on failure so the Dockerfile guard can catch it.
 *
 * Usage (from repo root, after npm ci):
 *   node scripts/build/fetchTlsClientXgoBinary.mjs
 *
 * Fixes: the Coolify/Docker build break caused by bogdanfinn/tls-client v1.16.0
 * dropping the `tls-client-linux-ubuntu-amd64-*` asset naming convention.
 */

import { existsSync, mkdirSync, readdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const BIN_DIR = join(process.cwd(), "node_modules", "tls-client-node", "bin");

function hasAnyFile(dir) {
  if (!existsSync(dir)) return false;
  try {
    return readdirSync(dir).length > 0;
  } catch {
    return false;
  }
}

if (hasAnyFile(BIN_DIR)) {
  console.log("tls-client-node bin/ already populated — skipping xgo fallback.");
  process.exit(0);
}

if (!existsSync(join(process.cwd(), "node_modules", "tls-client-node"))) {
  console.log("tls-client-node not installed — skipping xgo fallback.");
  process.exit(0);
}

console.log(
  "tls-client-node: bin/ empty after postinstall — attempting xgo-named fallback download..."
);

// Determine target platform/arch.
const PLATFORM = process.platform === "win32" ? "windows" : process.platform;
const ARCH_MAP = { x64: "amd64", arm64: "arm64", ia32: "386" };
const ARCH = ARCH_MAP[process.arch] || process.arch;
const EXT = PLATFORM === "darwin" ? ".dylib" : PLATFORM === "windows" ? ".dll" : ".so";

const GITHUB_API = "https://api.github.com/repos/bogdanfinn/tls-client/releases/latest";
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 3_000;

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getLegacyAssetName(version) {
  const v = version.replace(/^v/i, "");
  if (process.platform === "darwin" && process.arch === "arm64") return `tls-client-darwin-arm64-${v}.dylib`;
  if (process.platform === "darwin" && process.arch === "x64") return `tls-client-darwin-amd64-${v}.dylib`;
  if (process.platform === "linux" && process.arch === "x64") return `tls-client-linux-ubuntu-amd64-${v}.so`;
  if (process.platform === "linux" && process.arch === "arm64") return `tls-client-linux-arm64-${v}.so`;
  if (process.platform === "win32" && process.arch === "x64") return `tls-client-windows-64-${v}.dll`;
  if (process.platform === "win32" && process.arch === "ia32") return `tls-client-windows-32-${v}.dll`;
  return null;
}

async function attemptDownload() {
  const resp = await fetch(GITHUB_API, {
    headers: { "User-Agent": "omniroute-docker-builder" },
  });
  if (!resp.ok) throw new Error(`GitHub API returned HTTP ${resp.status}`);
  const { assets, tag_name } = await resp.json();

  // Strategy 1: xgo-named asset (v1.16.0+ naming)
  const xgoPattern = new RegExp(
    `tls-client-xgo-.*-${PLATFORM}-${ARCH}\\${EXT}$`
  );
  let asset = assets.find((a) => xgoPattern.test(a.name));

  // Strategy 2: old naming convention (pre-v1.16.0)
  if (!asset) {
    const oldPattern = new RegExp(
      `tls-client-${PLATFORM}-(ubuntu-)?${ARCH}-.*\\${EXT}$`
    );
    asset = assets.find((a) => oldPattern.test(a.name));
  }

  if (!asset) {
    throw new Error(
      `No ${PLATFORM}-${ARCH} ${EXT} asset found in ${tag_name} ` +
        `(${assets.length} assets checked)`
    );
  }

  console.log(`Downloading ${asset.name} from ${tag_name}...`);
  const dl = await fetch(asset.browser_download_url, { redirect: "follow" });
  if (!dl.ok) throw new Error(`Download failed: HTTP ${dl.status}`);

  const buf = Buffer.from(await dl.arrayBuffer());
  mkdirSync(BIN_DIR, { recursive: true });
  writeFileSync(join(BIN_DIR, asset.name), buf);
  console.log(`✅ Saved ${buf.length} bytes to ${BIN_DIR}/${asset.name}`);

  // tls-client-node's runtime (dist/binary.js::findExistingAsset) looks for the
  // legacy prefix (e.g. "tls-client-linux-ubuntu-amd64-"). Also write the legacy
  // alias so runtime findExistingAsset() matches without hitting GitHub.
  const legacyName = getLegacyAssetName(tag_name);
  if (legacyName && legacyName !== asset.name) {
    writeFileSync(join(BIN_DIR, legacyName), buf);
    console.log(`✅ Also saved legacy alias to ${BIN_DIR}/${legacyName}`);
  }
}

for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
  try {
    await attemptDownload();
    process.exit(0);
  } catch (err) {
    console.error(
      `⚠️  xgo fallback attempt ${attempt + 1}/${MAX_RETRIES + 1} failed: ${err.message}`
    );
    if (attempt < MAX_RETRIES) {
      console.log(`   Retrying in ${RETRY_DELAY_MS / 1000}s...`);
      await sleep(RETRY_DELAY_MS);
    }
  }
}

console.error(
  "❌ Could not download tls-client-node native binary via xgo fallback."
);
process.exit(1);
