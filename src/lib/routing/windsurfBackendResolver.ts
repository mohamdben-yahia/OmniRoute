export type WindsurfRuntimeSnapshot = {
  lsOk: boolean;
  availableModels: string[];
  source: "capability_defaults" | "observed_health";
  modelDiscovery: {
    status: "present" | "enriched" | "missing" | "failed" | "pending";
    source: "session/new" | "session/load" | "session/resume" | "none";
    reason?: "auth_failure" | "registry_failure" | "not_provided" | "unknown";
  };
};

export type ResolveWindsurfBackendInput = {
  requestedProvider: string;
  requestedModel: string;
  body: Record<string, unknown> | null | undefined;
  runtime: WindsurfRuntimeSnapshot;
};

export type ResolvedWindsurfBackend = {
  requestedProvider: string;
  requestedModel: string;
  effectiveProvider: string;
  effectiveModel: string;
  reason: string;
};

export function resolveWindsurfBackend({
  requestedProvider,
  requestedModel,
  runtime,
}: ResolveWindsurfBackendInput): ResolvedWindsurfBackend {
  if (requestedProvider !== "windsurf") {
    return {
      requestedProvider,
      requestedModel,
      effectiveProvider: requestedProvider,
      effectiveModel: requestedModel,
      reason: "non-windsurf provider bypasses backend resolver",
    };
  }

  void runtime;

  return {
    requestedProvider,
    requestedModel,
    effectiveProvider: "windsurf",
    effectiveModel: requestedModel,
    reason: "production Windsurf remains on cloud execution even when a local runtime is present",
  };
}
