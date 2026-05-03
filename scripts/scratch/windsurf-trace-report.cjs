const TRACE_NOT_OBSERVED = "NOT OBSERVED";

const EVIDENCE_RANK = {
  registration: 1,
  provider_binding: 2,
  acp_outbound: 3,
  ls_outbound: 4,
  inference_request: 5,
  inference_response: 6,
};

function byTimestampAsc(left, right) {
  return String(left.timestamp).localeCompare(String(right.timestamp));
}

function normalizeEvidenceClass(value, fallback = "registration") {
  if (typeof value !== "string" || value.length === 0) {
    return fallback;
  }
  return value;
}

function strongestEvidence(events) {
  if (!Array.isArray(events) || events.length === 0) {
    return {
      class: TRACE_NOT_OBSERVED,
      rank: 0,
      event: null,
    };
  }

  return events.reduce((best, event) => {
    const evidenceClass = normalizeEvidenceClass(event.evidence_class);
    const rank = EVIDENCE_RANK[evidenceClass] || 0;
    if (rank > best.rank) {
      return {
        class: evidenceClass,
        rank,
        event,
      };
    }
    return best;
  }, {
    class: TRACE_NOT_OBSERVED,
    rank: 0,
    event: null,
  });
}

function inferPathFamily(events) {
  const classes = new Set(events.map((event) => normalizeEvidenceClass(event.evidence_class)));
  const hasAcp = classes.has("acp_outbound");
  const hasLs = classes.has("ls_outbound") || classes.has("inference_request") || classes.has("inference_response");

  if (hasAcp && hasLs) return "hybrid";
  if (hasAcp) return "direct_acp";
  if (hasLs) return "ls_relay";
  return "unclassified";
}

function classifyTrace(providerEntry, chain, strongest) {
  const inferenceObserved = strongest.rank >= EVIDENCE_RANK.inference_request;
  if (inferenceObserved) {
    return {
      final_classification: "inference_observed",
      inference_observed: true,
      rationale: "Explicit inference-boundary evidence was observed for this trace.",
      broken_or_unknown_points: [],
    };
  }

  if (chain.length > 0) {
    return {
      final_classification: "routing_observed_without_inference",
      inference_observed: false,
      rationale: "Routing or transport evidence was observed, but no explicit inference-boundary artifact was captured.",
      broken_or_unknown_points: ["inference_boundary_not_observed"],
    };
  }

  if (providerEntry && providerEntry.method && providerEntry.method !== TRACE_NOT_OBSERVED) {
    return {
      final_classification: "unknown_partial_observability",
      inference_observed: false,
      rationale: "Provider binding was observed, but no downstream transport or inference evidence was captured.",
      broken_or_unknown_points: ["downstream_transport_or_inference"],
    };
  }

  return {
    final_classification: "wrong_process_attachment",
    inference_observed: false,
    rationale: "No provider or downstream execution evidence was captured for this trace.",
    broken_or_unknown_points: ["provider_entry_not_observed"],
  };
}

function createTraceReportBuilder() {
  const providerEntries = new Map();
  const transportEvents = new Map();

  return {
    recordProviderEntry(entry) {
      providerEntries.set(entry.trace_id, {
        evidence_class: normalizeEvidenceClass(entry.evidence_class, "provider_binding"),
        ...entry,
      });
    },
    recordTransportEvent(event) {
      const current = transportEvents.get(event.trace_id) || [];
      current.push({
        evidence_class: normalizeEvidenceClass(event.evidence_class, "ls_outbound"),
        ...event,
      });
      current.sort(byTimestampAsc);
      transportEvents.set(event.trace_id, current);
    },
    buildTraceReport(traceId) {
      const providerEntry = providerEntries.get(traceId) || {
        method: TRACE_NOT_OBSERVED,
        observed_args: TRACE_NOT_OBSERVED,
        evidence_class: TRACE_NOT_OBSERVED,
      };
      const ipcChain = (transportEvents.get(traceId) || []).slice().sort(byTimestampAsc);
      const allEvents = providerEntry.method !== TRACE_NOT_OBSERVED ? [providerEntry, ...ipcChain] : ipcChain;
      const first = ipcChain[0];
      const strongest = strongestEvidence(allEvents);
      const classification = classifyTrace(providerEntry, ipcChain, strongest);

      return {
        trace_id: traceId,
        provider_entry: providerEntry,
        execution_chain: ipcChain,
        ipc_chain: ipcChain,
        first_sink: first
          ? { type: first.type, target: first.target, timestamp: first.timestamp }
          : { type: TRACE_NOT_OBSERVED, target: TRACE_NOT_OBSERVED, timestamp: TRACE_NOT_OBSERVED },
        strongest_evidence: strongest,
        path_family: inferPathFamily(ipcChain),
        native_correlation: {
          observed: Boolean(first),
          evidence: first ? [first] : [],
        },
        routing_inference: classification.final_classification,
        ...classification,
      };
    },
    buildMetrics(traceIds) {
      let transportObserved = 0;
      let inferenceObserved = 0;
      const trace_propagation_status_by_trace = {};
      const broken_points_by_trace = {};

      for (const traceId of traceIds) {
        const report = this.buildTraceReport(traceId);
        if (report.first_sink.type !== TRACE_NOT_OBSERVED) {
          transportObserved += 1;
        }
        if (report.inference_observed) {
          inferenceObserved += 1;
        }
        trace_propagation_status_by_trace[traceId] = report.first_sink.type !== TRACE_NOT_OBSERVED ? "COMPLETE" : "BROKEN";
        broken_points_by_trace[traceId] = report.broken_or_unknown_points;
      }
      return {
        first_sink_observability_rate: `${transportObserved}/${traceIds.length}`,
        inference_observability_rate: `${inferenceObserved}/${traceIds.length}`,
        trace_propagation_status_by_trace,
        broken_points_by_trace,
      };
    },
  };
}

module.exports = {
  createTraceReportBuilder,
};
