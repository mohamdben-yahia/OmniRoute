const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const http = require("node:http");
const https = require("node:https");
const net = require("node:net");
const childProcess = require("node:child_process");
const { createTraceContext, TRACE_NOT_OBSERVED } = require("./windsurf-trace-context.cjs");

const ROOT = "C:/Users/amine/OmniRoute";
const LOG_PATH = path.join(ROOT, "windsurf-model-runtime-capture.jsonl");
const STATE_DB = "C:/Users/amine/AppData/Roaming/Windsurf/User/globalStorage/state.vscdb";

const traces = createTraceContext();
const reports = require("./windsurf-trace-report.cjs").createTraceReportBuilder();
const collectedTraceIds = new Set();
let nextTraceId = 1;
const activeTraces = new Map();

function detectProcessSurface(argv = process.argv) {
  const joined = argv.join(" ");
  if (/language_server_windows_x64\.exe/i.test(joined)) {
    return "language_server";
  }
  if (/devin\.exe\s+acp/i.test(joined)) {
    return "acp_agent";
  }
  if (/Windsurf\.exe/i.test(joined) || /extensionHostProcess/i.test(joined)) {
    return "host";
  }
  return "unknown";
}

const PROCESS_SURFACE = detectProcessSurface();

function makeTraceId(prefix) {
  return `${prefix}-${process.pid}-${Date.now()}-${nextTraceId++}`;
}

function redact(value) {
  if (typeof value === "string") {
    return value
      .replace(/devin-session-token\$[A-Za-z0-9._-]+/g, "devin-session-token$...[redacted]")
      .replace(/Bearer\s+[A-Za-z0-9._-]+/g, "Bearer [redacted]")
      .replace(/"api[_-]?key"\s*:\s*"[^"]+"/gi, '"apiKey":"[redacted]"')
      .replace(/"access[_-]?token"\s*:\s*"[^"]+"/gi, '"accessToken":"[redacted]"');
  }
  if (Buffer.isBuffer(value)) {
    return {
      type: "buffer",
      length: value.length,
      utf8Preview: redact(value.toString("utf8").slice(0, 1200)),
      base64Preview: value.toString("base64").slice(0, 1200),
    };
  }
  if (Array.isArray(value)) {
    return value.slice(0, 80).map((entry) => redact(entry));
  }
  if (value && typeof value === "object") {
    const out = {};
    for (const [key, entry] of Object.entries(value)) {
      if (/token|secret|authorization|cookie|api.?key/i.test(key)) {
        out[key] = "[redacted]";
        continue;
      }
      out[key] = redact(entry);
    }
    return out;
  }
  return value;
}

function writeEvent(type, payload) {
  const line = JSON.stringify({
    at: new Date().toISOString(),
    pid: process.pid,
    surface: PROCESS_SURFACE,
    type,
    payload: redact(payload),
  });
  fs.appendFileSync(LOG_PATH, `${line}\n`);
}

function safeOwnKeys(value) {
  try {
    return Reflect.ownKeys(value).map((key) => (typeof key === "symbol" ? key.toString() : String(key)));
  } catch (error) {
    return { error: error.message };
  }
}

function safePrototype(value) {
  try {
    const proto = Object.getPrototypeOf(value);
    if (!proto) return null;
    return {
      constructorName: proto.constructor && typeof proto.constructor === "function" ? proto.constructor.name : null,
      ownKeys: safeOwnKeys(proto),
    };
  } catch (error) {
    return { error: error.message };
  }
}

function summarizeDescriptorMap(value) {
  try {
    const descriptors = Object.getOwnPropertyDescriptors(value);
    const out = {};
    for (const key of Reflect.ownKeys(descriptors)) {
      const source = descriptors[key];
      const targetKey = typeof key === "symbol" ? key.toString() : String(key);
      out[targetKey] = {
        configurable: !!source.configurable,
        enumerable: !!source.enumerable,
        writable: "writable" in source ? !!source.writable : undefined,
        hasValue: "value" in source,
        valueType: "value" in source ? typeof source.value : undefined,
        getterType: typeof source.get,
        setterType: typeof source.set,
      };
    }
    return out;
  } catch (error) {
    return { error: error.message };
  }
}

function inspectFunction(fn) {
  if (typeof fn !== "function") {
    return { observed: false, type: typeof fn };
  }
  let source = null;
  let sourceError = null;
  try {
    source = Function.prototype.toString.call(fn);
  } catch (error) {
    sourceError = error.message;
  }
  return {
    observed: true,
    name: fn.name || null,
    length: fn.length,
    ownKeys: safeOwnKeys(fn),
    descriptors: summarizeDescriptorMap(fn),
    source,
    sourceError,
    isNativeSource: typeof source === "string" && source.includes("[native code]"),
    looksBound: typeof fn.name === "string" && fn.name.startsWith("bound "),
    prototypeType: typeof fn.prototype,
  };
}

function summarizeValue(value, depth = 0) {
  if (depth > 2) {
    return { type: typeof value, truncated: true };
  }
  if (value === null || value === undefined) return value;
  if (typeof value === "string") return value.slice(0, 2000);
  if (typeof value === "number" || typeof value === "boolean" || typeof value === "bigint") return value;
  if (typeof value === "function") return inspectFunction(value);
  if (Buffer.isBuffer(value)) return redact(value);
  if (Array.isArray(value)) return value.slice(0, 20).map((entry) => summarizeValue(entry, depth + 1));
  if (typeof value === "object") {
    const out = {
      type: value.constructor && typeof value.constructor === "function" ? value.constructor.name : "Object",
      ownKeys: safeOwnKeys(value),
      descriptors: summarizeDescriptorMap(value),
      preview: {},
    };
    for (const key of Object.keys(value).slice(0, 20)) {
      try {
        out.preview[key] = summarizeValue(value[key], depth + 1);
      } catch (error) {
        out.preview[key] = { error: error.message };
      }
    }
    return out;
  }
  return { type: typeof value };
}

function inspectProvider(provider) {
  const methodNames = [
    "provideLanguageModelChatResponse",
    "provideLanguageModelChatInformation",
    "provideTokenCount",
  ];
  const methods = {};
  for (const methodName of methodNames) {
    let value;
    let getError = null;
    try {
      value = Reflect.get(provider, methodName, provider);
    } catch (error) {
      getError = error.message;
    }
    methods[methodName] = {
      getError,
      function: inspectFunction(value),
    };
  }
  return {
    typeof: typeof provider,
    constructorName: provider && provider.constructor && typeof provider.constructor === "function"
      ? provider.constructor.name
      : null,
    ownKeys: safeOwnKeys(provider),
    descriptors: summarizeDescriptorMap(provider),
    prototype: safePrototype(provider),
    extensible: provider && typeof provider === "object" ? Object.isExtensible(provider) : null,
    sealed: provider && typeof provider === "object" ? Object.isSealed(provider) : null,
    frozen: provider && typeof provider === "object" ? Object.isFrozen(provider) : null,
    methods,
    proxyDetection: {
      revocablePattern: "NOT OBSERVED",
      accessTrapsViaReflectGet: methodNames.map((methodName) => {
        try {
          Reflect.get(provider, methodName, provider);
          return { methodName, observed: true };
        } catch (error) {
          return { methodName, observed: false, error: error.message };
        }
      }),
    },
  };
}

function captureStack() {
  return new Error().stack || null;
}

function createTrace(kind, payload) {
  const traceId = makeTraceId(kind);
  const trace = {
    traceId,
    kind,
    startedAt: Date.now(),
    firstAsyncBoundaryAt: null,
    payload,
  };
  activeTraces.set(traceId, trace);
  writeEvent("trace-start", trace);
  return trace;
}

function markFirstAsyncBoundary(trace, label) {
  if (!trace || trace.firstAsyncBoundaryAt !== null) return;
  trace.firstAsyncBoundaryAt = Date.now();
  writeEvent("trace-first-async-boundary", {
    traceId: trace.traceId,
    label,
    deltaMs: trace.firstAsyncBoundaryAt - trace.startedAt,
  });
}

function finishTrace(trace, extra) {
  if (!trace) return;
  const finishedAt = Date.now();
  writeEvent("trace-finish", {
    traceId: trace.traceId,
    durationMs: finishedAt - trace.startedAt,
    firstAsyncBoundaryDeltaMs: trace.firstAsyncBoundaryAt === null ? null : trace.firstAsyncBoundaryAt - trace.startedAt,
    ...extra,
  });
  activeTraces.delete(trace.traceId);
}

writeEvent("hook-loaded", {
  argv: process.argv,
  cwd: process.cwd(),
  entry: process.argv[1] || null,
  stateDbExists: fs.existsSync(STATE_DB),
});

process.on("exit", () => {
  const traceIds = Array.from(collectedTraceIds);
  const summary = {
    generatedAt: new Date().toISOString(),
    traceCount: traceIds.length,
    traces: traceIds.map((traceId) => reports.buildTraceReport(traceId)),
    metrics: reports.buildMetrics(traceIds),
  };
  fs.writeFileSync(path.join(ROOT, "windsurf-model-runtime-report.json"), JSON.stringify(summary, null, 2));
});

function previewArgs(args) {
  return args.map((arg) => summarizeValue(arg));
}

function extractPayloadKeys(value) {
  if (!value || typeof value !== "object") return [];
  try {
    return Object.keys(value).slice(0, 40);
  } catch {
    return [];
  }
}

function classifyProviderSource(vendor) {
  if (typeof vendor !== "string") return TRACE_NOT_OBSERVED;
  if (/devin|summary/i.test(vendor)) return "acp_cloud";
  if (/windsurf|codeium/i.test(vendor)) return "local_host";
  return TRACE_NOT_OBSERVED;
}

function parseJsonLikeMessage(value) {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  if (!(trimmed.startsWith("{") || trimmed.startsWith("["))) return null;
  try {
    return JSON.parse(trimmed);
  } catch {
    return null;
  }
}

function inferEvidenceClass(type, payload = {}) {
  if (payload.evidenceClass) return payload.evidenceClass;
  if (type === "provider-binding") return "provider_binding";
  if (type === "acp-outbound") return "acp_outbound";
  if (type === "ls-outbound") return "ls_outbound";
  if (type === "http-response") {
    return payload.isInferenceEndpoint ? "inference_response" : "ls_outbound";
  }
  if (type === "http-request") {
    return payload.isInferenceEndpoint ? "inference_request" : "ls_outbound";
  }
  return "registration";
}

function normalizeTraceEnvelope(type, payload = {}) {
  const traceId = payload.traceId || traces.getActiveTraceId();
  const timestamp = payload.timestamp || new Date().toISOString();
  const normalized = {
    ...payload,
    traceId,
    timestamp,
    surface: payload.surface || PROCESS_SURFACE,
    evidenceClass: inferEvidenceClass(type, payload),
    target: payload.target || payload.url || payload.endpoint || payload.destination || TRACE_NOT_OBSERVED,
  };

  if (Array.isArray(normalized.args)) {
    normalized.args = previewArgs(normalized.args);
  }

  return normalized;
}

function isInferenceTarget(target) {
  return typeof target === "string" && /\/(messages|chat\/completions|completions)(\?|$)/i.test(target);
}

function captureCurrentTrace() {
  const traceList = Array.from(activeTraces.values());
  return traceList.length > 0 ? traceList[traceList.length - 1] : null;
}

function createProviderWrapper({ vendor, provider, traces, writeEvent }) {
  const wrapped = Object.create(Object.getPrototypeOf(provider) || Object.prototype);
  Object.assign(wrapped, provider);

  for (const methodName of [
    "provideLanguageModelChatResponse",
    "provideLanguageModelChatInformation",
    "provideTokenCount",
  ]) {
    const original = provider[methodName];
    if (typeof original !== "function") continue;
    wrapped[methodName] = async (...args) => {
      const started = traces.startProviderTrace({
        vendor,
        method: methodName,
        observedArgs: args,
      });
      const providerBindingEvent = normalizeTraceEnvelope("provider-binding", {
        traceId: started.traceId,
        vendor,
        providerSource: classifyProviderSource(vendor),
        providerMethod: methodName,
        modelHint: typeof args[0]?.model === "string"
          ? args[0].model
          : typeof args[0]?.modelId === "string"
            ? args[0].modelId
            : TRACE_NOT_OBSERVED,
        payloadKeys: extractPayloadKeys(args[0]),
        stack: new Error().stack || null,
      });
      writeEvent("provider-binding", providerBindingEvent);
      reports.recordProviderEntry({
        trace_id: started.traceId,
        method: methodName,
        evidence_class: providerBindingEvent.evidenceClass,
        provider_source: providerBindingEvent.providerSource,
        target: providerBindingEvent.target,
        timestamp: providerBindingEvent.timestamp,
      });
      writeEvent("lm-provider-method-call", {
        traceId: started.traceId,
        vendor,
        methodName,
        args,
        stack: new Error().stack || null,
      });
      return traces.runWithTrace(started.traceId, async () => {
        try {
          const result = await Promise.resolve(original.apply(provider, args));
          writeEvent("lm-provider-method-result", {
            traceId: started.traceId,
            vendor,
            methodName,
            status: "resolved",
          });
          return result;
        } catch (error) {
          writeEvent("lm-provider-method-result", {
            traceId: started.traceId,
            vendor,
            methodName,
            status: "rejected",
            error: { message: error.message },
          });
          throw error;
        }
      });
    };
  }

  return wrapped;
}

function createRpcWrapper({ target, traces, writeEvent }) {
  return new Proxy(target, {
    get(originalTarget, prop, receiver) {
      const value = Reflect.get(originalTarget, prop, receiver);
      if (typeof value !== "function") return value;
      if (!String(prop).startsWith("$try") && !String(prop).startsWith("$start")) return value;
      return async function wrappedRpcMethod(...args) {
        const activeTraceId = traces.getActiveTraceId();
        const callId = typeof args[0] === "string" ? args[0] : null;
        if (callId && activeTraceId !== TRACE_NOT_OBSERVED) {
          traces.bindRpcCall(callId, activeTraceId);
        }
        if (args[1] && typeof args[1] === "object") {
          const metadata =
            args[1].metadata && typeof args[1].metadata === "object" ? args[1].metadata : {};
          args[1] = { ...args[1], metadata: { ...metadata, trace_id: activeTraceId } };
        }
        writeEvent("rpc-call", {
          traceId: activeTraceId,
          methodName: String(prop),
          callId,
        });
        return value.apply(originalTarget, args);
      };
    },
  });
}

function isChatRpcMethodName(methodName) {
  return /getChatMessage|rawGetChatMessage/i.test(methodName);
}

function summarizeChatRequestPayload(value) {
  if (!value || typeof value !== "object") return summarizeValue(value);
  const firstMessage = Array.isArray(value.chatMessages) ? value.chatMessages[0] : undefined;
  return {
    typeName: typeof value.getType === "function" ? value.getType()?.typeName || null : value.constructor?.typeName || null,
    constructorName: value.constructor?.name || null,
    ownKeys: safeOwnKeys(value),
    chatMessagesCount: Array.isArray(value.chatMessages) ? value.chatMessages.length : null,
    firstMessage: firstMessage
      ? {
          ownKeys: safeOwnKeys(firstMessage),
          role: firstMessage.role ?? firstMessage.source ?? null,
          contentPreview: typeof firstMessage.content === "string"
            ? firstMessage.content.slice(0, 500)
            : summarizeValue(firstMessage.content),
        }
      : null,
    chatModel: value.chatModel ?? null,
    chatModelName: value.chatModelName ?? null,
    systemPromptOverride: typeof value.systemPromptOverride === "string"
      ? value.systemPromptOverride.slice(0, 500)
      : summarizeValue(value.systemPromptOverride),
    metadata: summarizeValue(value.metadata),
    activeDocument: summarizeValue(value.activeDocument),
    workspaceUris: Array.isArray(value.workspaceUris) ? value.workspaceUris.slice(0, 20) : null,
  };
}

function wrapPromiseClient(client) {
  if (!client || typeof client !== "object" || client.__windsurfHookedPromiseClient) return client;
  const proxy = new Proxy(client, {
    get(target, prop, receiver) {
      const value = Reflect.get(target, prop, receiver);
      if (typeof value !== "function") return value;
      return function wrappedClientMethod(...args) {
        const methodName = String(prop);
        const trace = captureCurrentTrace();
        const traceId = trace?.traceId || traces.getActiveTraceId();
        const payload = args[0];
        writeEvent("promise-client-call", {
          traceId,
          methodName,
          isChatMethod: isChatRpcMethodName(methodName),
          payload: isChatRpcMethodName(methodName)
            ? summarizeChatRequestPayload(payload)
            : summarizeValue(payload),
          options: summarizeValue(args[1]),
          stack: captureStack(),
        });
        const result = value.apply(target, args);
        if (result && typeof result.then === "function") {
          return result.then((resolved) => {
            writeEvent("promise-client-result", {
              traceId,
              methodName,
              status: "resolved",
              resolved: summarizeValue(resolved),
            });
            return resolved;
          }, (error) => {
            writeEvent("promise-client-result", {
              traceId,
              methodName,
              status: "rejected",
              error: { message: error.message },
            });
            throw error;
          });
        }
        writeEvent("promise-client-result", {
          traceId,
          methodName,
          status: "returned",
          resolved: summarizeValue(result),
        });
        return result;
      };
    },
  });
  Object.defineProperty(proxy, "__windsurfHookedPromiseClient", { value: true });
  return proxy;
}

function emitTransportEvent(type, payload) {
  const event = normalizeTraceEnvelope(type, payload);
  writeEvent(type, event);
  if (event.traceId !== TRACE_NOT_OBSERVED) {
    collectedTraceIds.add(event.traceId);
    reports.recordTransportEvent({
      trace_id: event.traceId,
      type: payload.transportType || type,
      target: event.target,
      timestamp: event.timestamp,
      evidence_class: event.evidenceClass,
      surface: event.surface,
    });
  }
}

function wrapFetch() {
  if (typeof globalThis.fetch !== "function" || globalThis.fetch.__windsurfHooked) return;
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async function patchedFetch(...args) {
    const trace = captureCurrentTrace();
    markFirstAsyncBoundary(trace, "fetch");
    emitTransportEvent("fetch-call", {
      traceId: trace?.traceId || traces.getActiveTraceId(),
      transportType: "FETCH",
      args: previewArgs(args),
      url: typeof args[0] === "string" ? args[0] : null,
      stack: captureStack(),
    });
    const result = await originalFetch.apply(this, args);
    writeEvent("fetch-result", {
      traceId: trace?.traceId || traces.getActiveTraceId(),
      status: result?.status,
      ok: result?.ok,
      url: result?.url || null,
    });
    return result;
  };
  globalThis.fetch.__windsurfHooked = true;
}

function wrapWebSocket() {
  if (typeof globalThis.WebSocket !== "function" || globalThis.WebSocket.__windsurfHooked) return;
  const OriginalWebSocket = globalThis.WebSocket;
  function PatchedWebSocket(...args) {
    const trace = captureCurrentTrace();
    markFirstAsyncBoundary(trace, "WebSocket");
    const socket = Reflect.construct(OriginalWebSocket, args, new.target || PatchedWebSocket);
    emitTransportEvent("websocket-construct", {
      traceId: trace?.traceId || traces.getActiveTraceId(),
      transportType: "WS",
      target: typeof args[0] === "string" ? args[0] : TRACE_NOT_OBSERVED,
      args: previewArgs(args),
      stack: captureStack(),
    });
    if (socket && typeof socket.send === "function" && !socket.send.__windsurfHooked) {
      const originalSend = socket.send;
      socket.send = function patchedWebSocketSend(message, ...rest) {
        const activeTraceId = traces.getActiveTraceId();
        const parsed = parseJsonLikeMessage(typeof message === "string" ? message : null);
        const payloadKeys = extractPayloadKeys(parsed);
        const eventName = PROCESS_SURFACE === "acp_agent" ? "acp-outbound" : "websocket-send";
        const outboundEvent = normalizeTraceEnvelope(eventName, {
          traceId: activeTraceId,
          target: typeof args[0] === "string" ? args[0] : TRACE_NOT_OBSERVED,
          payloadKeys,
          messageKind: parsed && typeof parsed === "object" && typeof parsed.method === "string"
            ? parsed.method
            : TRACE_NOT_OBSERVED,
          rawPreview: typeof message === "string" ? message.slice(0, 400) : summarizeValue(message),
        });
        writeEvent(eventName, outboundEvent);
        if (eventName === "acp-outbound" && outboundEvent.traceId !== TRACE_NOT_OBSERVED) {
          collectedTraceIds.add(outboundEvent.traceId);
          reports.recordTransportEvent({
            trace_id: outboundEvent.traceId,
            type: "WS_OUTBOUND",
            target: outboundEvent.target,
            timestamp: outboundEvent.timestamp,
            evidence_class: outboundEvent.evidenceClass,
            surface: outboundEvent.surface,
          });
        }
        return originalSend.call(this, message, ...rest);
      };
      socket.send.__windsurfHooked = true;
    }
    return socket;
  }
  Object.setPrototypeOf(PatchedWebSocket, OriginalWebSocket);
  PatchedWebSocket.prototype = OriginalWebSocket.prototype;
  PatchedWebSocket.__windsurfHooked = true;
  globalThis.WebSocket = PatchedWebSocket;
}

function wrapRequest(mod, protocol) {
  const originalRequest = mod.request;
  mod.request = function patchedRequest(...args) {
    const trace = captureCurrentTrace();
    try {
      const target = typeof args[0] === "string"
        ? args[0]
        : args[0] && typeof args[0] === "object"
          ? `${protocol}//${args[0].hostname || args[0].host || ""}${args[0].path || ""}`
          : null;
      const inferenceTarget = isInferenceTarget(target);
      markFirstAsyncBoundary(trace, `${protocol}request`);
      const activeTraceId = trace?.traceId || traces.getActiveTraceId();
      emitTransportEvent("http-request", {
        traceId: activeTraceId,
        transportType: inferenceTarget ? "HTTP_INFERENCE_REQUEST" : "HTTP",
        protocol,
        target,
        args: args.slice(0, 2),
        stack: captureStack(),
        isInferenceEndpoint: inferenceTarget,
      });
      if (PROCESS_SURFACE === "language_server") {
        const lsOutboundEvent = normalizeTraceEnvelope("ls-outbound", {
          traceId: activeTraceId,
          transport: "http",
          protocol,
          endpoint: target || TRACE_NOT_OBSERVED,
          target: target || TRACE_NOT_OBSERVED,
          payloadKeys: extractPayloadKeys(args[0]),
          isInferenceEndpoint: inferenceTarget,
          evidenceClass: inferenceTarget ? "inference_request" : "ls_outbound",
        });
        writeEvent("ls-outbound", lsOutboundEvent);
        if (lsOutboundEvent.traceId !== TRACE_NOT_OBSERVED) {
          collectedTraceIds.add(lsOutboundEvent.traceId);
          reports.recordTransportEvent({
            trace_id: lsOutboundEvent.traceId,
            type: inferenceTarget ? "HTTP_INFERENCE_REQUEST" : "LS_OUTBOUND",
            target: lsOutboundEvent.target,
            timestamp: lsOutboundEvent.timestamp,
            evidence_class: lsOutboundEvent.evidenceClass,
            surface: lsOutboundEvent.surface,
          });
        }
      }
    } catch (error) {
      writeEvent("hook-error", { phase: "request", protocol, message: error.message });
    }
    const req = originalRequest.apply(this, args);
    req.on("response", (res) => {
      const chunks = [];
      const capture = /model|cascade|command|chat|status|auth|seat|api_server|language_server/i.test(String(res.req?.path || "")) || /model|cascade|command|chat|status|auth|seat/i.test(String(res.headers[":path"] || ""));
      if (!capture) return;
      res.on("data", (chunk) => {
        if (chunks.reduce((n, b) => n + b.length, 0) < 2_000_000) chunks.push(Buffer.from(chunk));
      });
      res.on("end", () => {
        const body = Buffer.concat(chunks);
        const responseTarget = typeof res.req?.path === "string"
          ? `${protocol}//${res.req?.host || ""}${res.req.path}`
          : null;
        const inferenceTarget = isInferenceTarget(responseTarget);
        const responseEvent = normalizeTraceEnvelope("http-response", {
          traceId: trace?.traceId || traces.getActiveTraceId(),
          protocol,
          statusCode: res.statusCode,
          headers: res.headers,
          path: res.req?.path || null,
          body,
          target: responseTarget,
          isInferenceEndpoint: inferenceTarget,
          evidenceClass: inferenceTarget ? "inference_response" : "ls_outbound",
        });
        writeEvent("http-response", responseEvent);
        if (responseEvent.traceId !== TRACE_NOT_OBSERVED) {
          collectedTraceIds.add(responseEvent.traceId);
          reports.recordTransportEvent({
            trace_id: responseEvent.traceId,
            type: inferenceTarget ? "HTTP_INFERENCE_RESPONSE" : "HTTP_RESPONSE",
            target: responseEvent.target,
            timestamp: responseEvent.timestamp,
            evidence_class: responseEvent.evidenceClass,
            surface: responseEvent.surface,
          });
        }
      });
    });
    return req;
  };
}

wrapFetch();
wrapWebSocket();
wrapRequest(http, "http:");
wrapRequest(https, "https:");

if (net.Socket && net.Socket.prototype && !net.Socket.prototype.connect.__windsurfHooked) {
  const originalConnect = net.Socket.prototype.connect;
  net.Socket.prototype.connect = function patchedConnect(...args) {
    const trace = captureCurrentTrace();
    markFirstAsyncBoundary(trace, "net.Socket.connect");
    emitTransportEvent("net-connect", {
      traceId: trace?.traceId || traces.getActiveTraceId(),
      transportType: "IPC",
      destination: previewArgs(args)[0] || TRACE_NOT_OBSERVED,
      args: previewArgs(args),
      stack: captureStack(),
    });
    return originalConnect.apply(this, args);
  };
  net.Socket.prototype.connect.__windsurfHooked = true;
}

for (const methodName of ["spawn", "exec", "execFile", "fork"]) {
  if (typeof childProcess[methodName] === "function" && !childProcess[methodName].__windsurfHooked) {
    const originalMethod = childProcess[methodName];
    childProcess[methodName] = function patchedChildProcess(...args) {
      const trace = captureCurrentTrace();
      markFirstAsyncBoundary(trace, `child_process.${methodName}`);
      emitTransportEvent("child-process-call", {
        traceId: trace?.traceId || traces.getActiveTraceId(),
        transportType: "PROCESS",
        destination: typeof args[0] === "string" ? args[0] : TRACE_NOT_OBSERVED,
        methodName,
        args: previewArgs(args),
        stack: captureStack(),
      });
      return originalMethod.apply(this, args);
    };
    childProcess[methodName].__windsurfHooked = true;
  }
}

if (typeof process.send === "function" && !process.send.__windsurfHooked) {
  const originalProcessSend = process.send;
  process.send = function patchedProcessSend(...args) {
    const trace = captureCurrentTrace();
    markFirstAsyncBoundary(trace, "process.send");
    writeEvent("process-send", {
      traceId: trace?.traceId || null,
      args: previewArgs(args),
      stack: captureStack(),
    });
    return originalProcessSend.apply(this, args);
  };
  process.send.__windsurfHooked = true;
}

const originalLoad = Module._load;
Module._load = function patchedLoad(request, parent, isMain) {
  const exported = originalLoad.apply(this, arguments);
  try {
    const filename = Module._resolveFilename(request, parent, isMain);
    if (typeof filename === "string" && /windsurf|@exa\\chat-client|extensionHostProcess|workbench\.desktop\.main/i.test(filename)) {
      writeEvent("module-load", { request, filename, parent: parent?.filename || null });
    }

    if (typeof filename === "string" && /better-sqlite3/i.test(filename) && exported?.prototype?.prepare) {
      const Database = exported;
      if (!Database.__windsurfHooked) {
        Database.__windsurfHooked = true;
        const originalPrepare = Database.prototype.prepare;
        Database.prototype.prepare = function patchedPrepare(sql) {
          const stmt = originalPrepare.call(this, sql);
          if (typeof sql === "string" && /ItemTable/i.test(sql) && /INSERT|UPDATE|REPLACE/i.test(sql)) {
            for (const methodName of ["run", "get", "all"]) {
              if (typeof stmt[methodName] !== "function" || stmt[methodName].__windsurfHooked) continue;
              const originalMethod = stmt[methodName];
              stmt[methodName] = function patchedStatementMethod(...methodArgs) {
                if (JSON.stringify(methodArgs).includes("chat.modelsControl")) {
                  writeEvent("state-db-write", { sql, methodName, args: methodArgs });
                }
                return originalMethod.apply(this, methodArgs);
              };
              stmt[methodName].__windsurfHooked = true;
            }
          }
          return stmt;
        };
      }
    }

    if (typeof filename === "string" && /@connectrpc[\\/](connect-web|connect)[\\/].*(connect-transport|promise-client|index)\.js$/i.test(filename) && exported && typeof exported === "object") {
      for (const key of Object.keys(exported)) {
        if (!/createConnectTransport|createPromiseClient/i.test(key)) continue;
        const original = exported[key];
        if (typeof original !== "function" || original.__windsurfHooked) continue;
        exported[key] = function patchedConnectRpcFactory(...args) {
          const trace = captureCurrentTrace();
          markFirstAsyncBoundary(trace, key);
          writeEvent("connectrpc-factory-call", {
            traceId: trace?.traceId || null,
            key,
            args: previewArgs(args),
            stack: captureStack(),
          });
          const result = original.apply(this, args);
          const wrappedResult = /createPromiseClient/i.test(key) ? wrapPromiseClient(result) : result;
          writeEvent("connectrpc-factory-result", {
            traceId: trace?.traceId || null,
            key,
            result: summarizeValue(wrappedResult),
          });
          return wrappedResult;
        };
        exported[key].__windsurfHooked = true;
      }
    }

    if (typeof filename === "string" && /@exa[\\/]chat-client[\\/]index\.js$/i.test(filename) && exported && typeof exported === "object") {
      const wrapMethod = (owner, key) => {
        if (!owner || typeof owner[key] !== "function" || owner[key].__windsurfHooked) return;
        const original = owner[key];
        owner[key] = function patchedMethod(...args) {
          const trace = captureCurrentTrace();
          markFirstAsyncBoundary(trace, `chat-client.${key}`);
          const result = original.apply(this, args);
          writeEvent("chat-client-call", { traceId: trace?.traceId || null, key, args: previewArgs(args), stack: captureStack() });
          if (result && typeof result.then === "function") {
            return result.then((resolved) => {
              writeEvent("chat-client-result", { traceId: trace?.traceId || null, key, resolved: summarizeValue(resolved) });
              return resolved;
            });
          }
          writeEvent("chat-client-result", { traceId: trace?.traceId || null, key, resolved: summarizeValue(result) });
          return result;
        };
        owner[key].__windsurfHooked = true;
      };

      for (const key of Object.keys(exported)) {
        if (/protoToBinaryBase64|fromBinary|fromJsonString|fromJson/i.test(key)) {
          wrapMethod(exported, key);
        }
      }
    }

    if (typeof filename === "string" && /extensionHostProcess\.js$/i.test(filename) && exported && typeof exported === "object") {
      for (const value of Object.values(exported)) {
        if (!value || typeof value !== "function") continue;
        const proto = value.prototype;
        if (!proto || typeof proto.registerLanguageModelChatProvider !== "function" || proto.registerLanguageModelChatProvider.__windsurfHooked) continue;

        const originalRegister = proto.registerLanguageModelChatProvider;
        proto.registerLanguageModelChatProvider = function patchedRegisterLanguageModelChatProvider(t, vendor, provider) {
          const registrationTrace = createTrace("lm-register", {
            vendor,
            extension: summarizeValue(t),
            providerShape: inspectProvider(provider),
            stack: captureStack(),
          });
          writeEvent("lm-provider-registration", {
            traceId: registrationTrace.traceId,
            vendor,
            extension: summarizeValue(t),
            providerShape: inspectProvider(provider),
          });

          for (const methodName of [
            "provideLanguageModelChatResponse",
            "provideLanguageModelChatInformation",
            "provideTokenCount",
          ]) {
            let originalMethod;
            try {
              originalMethod = Reflect.get(provider, methodName, provider);
            } catch (error) {
              writeEvent("lm-provider-method-read-error", {
                traceId: registrationTrace.traceId,
                vendor,
                methodName,
                error: error.message,
              });
              continue;
            }
            if (typeof originalMethod !== "function" || originalMethod.__windsurfHooked) continue;
            writeEvent("lm-provider-method-wrapped", {
              traceId: registrationTrace.traceId,
              vendor,
              methodName,
              original: inspectFunction(originalMethod),
            });
          }

          const wrappedProvider = createProviderWrapper({
            vendor,
            provider,
            traces,
            writeEvent(type, payload) {
              writeEvent(type, {
                ...payload,
                args: Array.isArray(payload.args) ? previewArgs(payload.args) : payload.args,
              });
            },
          });

          for (const methodName of [
            "provideLanguageModelChatResponse",
            "provideLanguageModelChatInformation",
            "provideTokenCount",
          ]) {
            if (typeof wrappedProvider[methodName] !== "function") continue;
            try {
              wrappedProvider[methodName].__windsurfHooked = true;
              provider[methodName] = wrappedProvider[methodName];
            } catch (error) {
              writeEvent("lm-provider-method-wrap-error", {
                traceId: registrationTrace.traceId,
                vendor,
                methodName,
                error: error.message,
              });
            }
          }

          try {
            return originalRegister.apply(this, arguments);
          } finally {
            finishTrace(registrationTrace, { vendor, status: "registered" });
          }
        };
        proto.registerLanguageModelChatProvider.__windsurfHooked = true;
        writeEvent("lm-register-hook-installed", {
          filename,
          exportName: value.name || null,
          prototypeKeys: safeOwnKeys(proto),
        });
      }
    }
  } catch (error) {
    writeEvent("hook-error", { phase: "load", request, message: error.message });
  }
  return exported;
};

module.exports.createProviderWrapper = createProviderWrapper;
module.exports.createRpcWrapper = createRpcWrapper;
