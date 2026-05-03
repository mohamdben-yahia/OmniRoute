import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { createTraceReportBuilder } = require("../../scripts/scratch/windsurf-trace-report.cjs");

test("report builder attributes first sink only when trace ids match", () => {
  const reports = createTraceReportBuilder();

  reports.recordProviderEntry({
    trace_id: "trace-1",
    method: "provideLanguageModelChatResponse",
    observed_args: { model: "claude-sonnet-4.6" },
  });
  reports.recordTransportEvent({
    trace_id: "trace-1",
    type: "HTTP",
    target: "http://127.0.0.1:50341/chat",
    timestamp: "2026-04-29T10:00:00.000Z",
  });

  const report = reports.buildTraceReport("trace-1");
  assert.equal(report.first_sink.type, "HTTP");
  assert.equal(report.first_sink.target, "http://127.0.0.1:50341/chat");
});

test("report builder returns NOT OBSERVED when no matching sink exists", () => {
  const reports = createTraceReportBuilder();

  reports.recordProviderEntry({
    trace_id: "trace-2",
    method: "provideLanguageModelChatResponse",
    observed_args: { model: "claude-sonnet-4.6" },
  });
  reports.recordTransportEvent({
    trace_id: "trace-other",
    type: "HTTP",
    target: "http://127.0.0.1:50341/chat",
    timestamp: "2026-04-29T10:00:01.000Z",
  });

  const report = reports.buildTraceReport("trace-2");
  assert.equal(report.first_sink.type, "NOT OBSERVED");
  assert.equal(report.native_correlation.observed, false);
});

test("report builder computes observability metrics across traces", () => {
  const reports = createTraceReportBuilder();

  reports.recordProviderEntry({ trace_id: "a", method: "provideLanguageModelChatResponse", observed_args: {} });
  reports.recordProviderEntry({ trace_id: "b", method: "provideLanguageModelChatResponse", observed_args: {} });
  reports.recordTransportEvent({ trace_id: "a", type: "IPC", target: "localhost:50341", timestamp: "2026-04-29T10:00:00.000Z" });

  const metrics = reports.buildMetrics(["a", "b"]);
  assert.equal(metrics.first_sink_observability_rate, "1/2");
  assert.equal(metrics.trace_propagation_status_by_trace.a, "COMPLETE");
});

test("report builder marks mixed success as partial observability", () => {
  const reports = createTraceReportBuilder();

  reports.recordProviderEntry({ trace_id: "same-model-small", method: "provideLanguageModelChatResponse", observed_args: { model: "claude-sonnet-4.6" } });
  reports.recordProviderEntry({ trace_id: "different-model", method: "provideLanguageModelChatResponse", observed_args: { model: "gpt-4o" } });
  reports.recordProviderEntry({ trace_id: "tools-on", method: "provideLanguageModelChatResponse", observed_args: { model: "claude-sonnet-4.6", tools: [{}] } });

  reports.recordTransportEvent({ trace_id: "same-model-small", type: "IPC", target: "localhost:50341", timestamp: "2026-04-29T10:00:00.000Z" });
  reports.recordTransportEvent({ trace_id: "tools-on", type: "HTTP", target: "https://example.invalid/chat", timestamp: "2026-04-29T10:00:02.000Z" });

  const metrics = reports.buildMetrics(["same-model-small", "different-model", "tools-on"]);
  assert.equal(metrics.first_sink_observability_rate, "2/3");
  assert.equal(metrics.trace_propagation_status_by_trace["different-model"], "BROKEN");
  assert.deepEqual(metrics.broken_points_by_trace["different-model"], ["transport hook"]);
});
