import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";

const ROOT = "C:/Users/amine/OmniRoute";
const WINDSURF_EXE = "C:/Users/amine/AppData/Local/Programs/Windsurf/Windsurf.exe";
const HOOK = path.join(ROOT, "scripts/scratch/windsurf-model-runtime-hook.cjs");
const LOG = path.join(ROOT, "windsurf-model-runtime-capture.jsonl");
const NETLOG = path.join(ROOT, "windsurf-netlog.json");
const OUT = path.join(ROOT, "windsurf-model-runtime-launch.json");
if (!fs.existsSync(WINDSURF_EXE)) {
  throw new Error(`Windsurf executable not found: ${WINDSURF_EXE}`);
}
if (!fs.existsSync(HOOK)) {
  throw new Error(`Hook file not found: ${HOOK}`);
}

fs.writeFileSync(LOG, "");
if (fs.existsSync(NETLOG)) {
  fs.unlinkSync(NETLOG);
}

const normalizedHook = HOOK.replace(/\\/g, "/");
const nodeOptions = `${process.env.NODE_OPTIONS ? `${process.env.NODE_OPTIONS} ` : ""}--require=${normalizedHook}`;

const args = [
  `--log-net-log=${NETLOG}`,
  "--net-log-capture-mode=IncludeSensitive",
];
const scenario = process.env.WINDSURF_TRACE_SCENARIO || "unlabeled";

const child = spawn(WINDSURF_EXE, args, {
  cwd: ROOT,
  detached: false,
  windowsHide: false,
  env: {
    ...process.env,
    NODE_OPTIONS: nodeOptions,
  },
  stdio: "ignore",
});

const result = {
  at: new Date().toISOString(),
  pid: child.pid ?? null,
  executable: WINDSURF_EXE,
  args,
  hook: HOOK,
  normalizedHook,
  log: LOG,
  netlog: NETLOG,
  traceMode: "deterministic-runtime-trace",
  scenario,
  reports: path.join(ROOT, "windsurf-model-runtime-report.json"),
  nodeOptions,
  captureMode: "hook-plus-chromium-netlog",
};

fs.writeFileSync(OUT, JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
