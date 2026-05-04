from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
from copy import deepcopy


RELEVANT_UNLINKED_EVENT_TYPES = {
    "START_CASCADE",
    "SEND_USER_CASCADE_MESSAGE",
}


def build_initial_graph(graph_index: int) -> dict[str, object]:
    return {
        "graph_id": f"G_{graph_index}",
        "graph_index": graph_index,
        "node_service": None,
        "language_server": None,
        "extension_host": None,
        "edges": [],
        "unlinked_evidence": [],
        "cascade_flow": {
            "startCascade": False,
            "sendUserCascadeMessage": False,
            "traceCount": 0,
        },
        "session_mapping": {
            "sessionId": None,
            "propagation_path": [],
        },
        "passive_evidence_summary": {},
        "last_start_cascade": None,
        "last_send_user_cascade_message": None,
        "trace_count_events": [],
        "last_ls_pid": None,
        "last_extension_host_pid": None,
        "bound_ports": {},
        "events": [],
        "cdp_network_requests": [],
        "cdp_network_responses": [],
        "cdp_websocket_creations": [],
        "reset_reason": None,
    }


def archive_graph(graph: dict[str, object], reason: str) -> dict[str, object]:
    archived = deepcopy(graph)
    archived["reset_reason"] = reason
    return archived


def normalize_passive_record(raw_record: dict[str, object], *, event_id: str) -> dict[str, object]:
    event_name = raw_record.get("event")
    timestamp = raw_record.get("timestamp")
    params = raw_record.get("params", {})
    metadata = raw_record.get("metadata", {})

    if event_name == "Network.responseReceived":
        response = params.get("response", {}) if isinstance(params, dict) else {}
        session_id = metadata.get("sessionId") if isinstance(metadata, dict) else None
        return {
            "event_id": event_id,
            "event_type": "CDP_NETWORK_RESPONSE_RECEIVED",
            "observed_at": timestamp,
            "source_stream": "cdp_trace",
            "payload": {
                "requestId": raw_record.get("requestId"),
                "url": response.get("url"),
                "status": response.get("status"),
                "sessionId": session_id,
            },
            "evidence": {
                "method": event_name,
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {
                "sessionId": session_id,
            },
        }

    if event_name == "Network.webSocketCreated":
        session_id = metadata.get("sessionId") if isinstance(metadata, dict) else None
        return {
            "event_id": event_id,
            "event_type": "CDP_WEBSOCKET_CREATED",
            "observed_at": timestamp,
            "source_stream": "cdp_trace",
            "payload": {
                "requestId": raw_record.get("requestId"),
                "url": params.get("url") if isinstance(params, dict) else None,
                "sessionId": session_id,
            },
            "evidence": {
                "method": event_name,
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {
                "sessionId": session_id,
            },
        }

    if event_name == "Network.requestWillBeSent":
        request = params.get("request", {}) if isinstance(params, dict) else {}
        session_id = metadata.get("sessionId") if isinstance(metadata, dict) else None
        return {
            "event_id": event_id,
            "event_type": "CDP_NETWORK_REQUEST_WILL_BE_SENT",
            "observed_at": timestamp,
            "source_stream": "cdp_trace",
            "payload": {
                "requestId": raw_record.get("requestId"),
                "url": request.get("url"),
                "sessionId": session_id,
            },
            "evidence": {
                "method": event_name,
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {
                "sessionId": session_id,
            },
        }

    if event_name == "SESSION_ID_PROPAGATION":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        session_id = payload.get("sessionId")
        return {
            "event_id": event_id,
            "event_type": "SESSION_ID_PROPAGATION",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "extension_log",
            "payload": {
                "from": payload.get("from"),
                "to": payload.get("to"),
                "sessionId": session_id,
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {
                "sessionId": session_id,
            },
        }

    if event_name == "CONNECT_HTTP_ESTABLISHED":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        return {
            "event_id": event_id,
            "event_type": "CONNECT_HTTP_ESTABLISHED",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "ls_log",
            "payload": {
                "src": payload.get("src"),
                "dst": payload.get("dst"),
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {},
        }

    if event_name == "START_CASCADE":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        session_id = payload.get("sessionId")
        return {
            "event_id": event_id,
            "event_type": "START_CASCADE",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "runtime_jsonl",
            "payload": {
                "sessionId": session_id,
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {
                "sessionId": session_id,
            },
        }

    if event_name == "SEND_USER_CASCADE_MESSAGE":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        session_id = payload.get("sessionId")
        return {
            "event_id": event_id,
            "event_type": "SEND_USER_CASCADE_MESSAGE",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "runtime_jsonl",
            "payload": {
                "sessionId": session_id,
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {
                "sessionId": session_id,
            },
        }

    if event_name == "TRACE_COUNT_DELTA":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        return {
            "event_id": event_id,
            "event_type": "TRACE_COUNT_DELTA",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "runtime_jsonl",
            "payload": {
                "delta": payload.get("delta"),
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {},
        }

    if event_name == "LS_START":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        session_id = payload.get("sessionId")
        return {
            "event_id": event_id,
            "event_type": "LS_START",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "ls_log",
            "payload": {
                "ls_pid": payload.get("ls_pid"),
                "ports": payload.get("ports"),
                "sessionId": session_id,
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {
                "sessionId": session_id,
            },
        }

    if event_name == "EXTENSION_HOST_START":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        return {
            "event_id": event_id,
            "event_type": "EXTENSION_HOST_START",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "extension_log",
            "payload": {
                "pid": payload.get("pid"),
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {},
        }

    if event_name == "PORT_BOUND":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        return {
            "event_id": event_id,
            "event_type": "PORT_BOUND",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "ls_log",
            "payload": {
                "service": payload.get("service"),
                "port": payload.get("port"),
                "owner_pid": payload.get("owner_pid"),
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {},
        }

    if event_name == "NODE_SERVICE_START":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        return {
            "event_id": event_id,
            "event_type": "NODE_SERVICE_START",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "node_log",
            "payload": {
                "pid": payload.get("pid"),
                "port": payload.get("port"),
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {},
        }

    if event_name == "CDP_NETWORK_REQUEST_WILL_BE_SENT":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        return {
            "event_id": event_id,
            "event_type": "CDP_NETWORK_REQUEST_WILL_BE_SENT",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "cdp_log",
            "payload": {
                "requestId": payload.get("requestId"),
                "url": payload.get("url"),
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {},
        }

    if event_name == "CDP_NETWORK_RESPONSE_RECEIVED":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        return {
            "event_id": event_id,
            "event_type": "CDP_NETWORK_RESPONSE_RECEIVED",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "cdp_log",
            "payload": {
                "requestId": payload.get("requestId"),
                "status": payload.get("status"),
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {},
        }

    if event_name == "CDP_WEBSOCKET_CREATED":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        return {
            "event_id": event_id,
            "event_type": "CDP_WEBSOCKET_CREATED",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "cdp_log",
            "payload": {
                "requestId": payload.get("requestId"),
                "url": payload.get("url"),
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {},
        }

    if event_name == "CDP_WEBSOCKET_FRAME_SENT":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        return {
            "event_id": event_id,
            "event_type": "CDP_WEBSOCKET_FRAME_SENT",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "cdp_log",
            "payload": {
                "requestId": payload.get("requestId"),
                "opcode": payload.get("opcode"),
                "payloadData": payload.get("payloadData"),
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {},
        }

    if event_name == "CDP_WEBSOCKET_FRAME_RECEIVED":
        payload = raw_record.get("payload", {}) if isinstance(raw_record.get("payload"), dict) else {}
        return {
            "event_id": event_id,
            "event_type": "CDP_WEBSOCKET_FRAME_RECEIVED",
            "observed_at": timestamp,
            "source_stream": raw_record.get("source_stream") or "cdp_log",
            "payload": {
                "requestId": payload.get("requestId"),
                "opcode": payload.get("opcode"),
                "payloadData": payload.get("payloadData"),
            },
            "evidence": {
                "renderer_pid": raw_record.get("renderer_pid"),
            },
            "graph_hint": {},
        }

    raise ValueError(f"Unsupported passive record event {event_name}")



def observer_event_to_reducer_event(observer_event: dict[str, object], *, event_id: str) -> dict[str, object]:
    event_name = observer_event.get("type")
    if not isinstance(event_name, str):
        raise ValueError("Observer event is missing a string type")

    payload: dict[str, object] = {}
    for key in ("sessionId", "csrfToken", "traceCount", "traceDelta", "surface", "pid", "ls_pid", "ports", "sourcePath", "evidenceSource"):
        value = observer_event.get(key)
        if value is not None:
            payload[key if key != "traceDelta" else "delta"] = value

    event_type_map = {
        "START_CASCADE": "START_CASCADE",
        "SEND_USER_CASCADE_MESSAGE": "SEND_USER_CASCADE_MESSAGE",
        "TRACE_COUNT_DELTA": "TRACE_COUNT_DELTA",
        "ACP_AGENT_REGISTERED": "ACP_AGENT_REGISTERED",
        "LS_START": "LS_START",
        "EXTENSION_SERVER_CLIENT_CREATED": "EXTENSION_SERVER_CLIENT_CREATED",
    }
    event_type = event_type_map.get(event_name)
    if event_type is None:
        raise ValueError(f"Unsupported observer event type {event_name}")

    graph_hint: dict[str, object] = {}
    session_id = observer_event.get("sessionId")
    if isinstance(session_id, str):
        graph_hint["sessionId"] = session_id

    evidence: dict[str, object] = {}
    source = observer_event.get("source")
    if isinstance(source, str):
        evidence["observer_source"] = source
    preceded_by = observer_event.get("precededBy")
    if isinstance(preceded_by, dict):
        evidence["precededBy"] = deepcopy(preceded_by)

    return {
        "event_id": event_id,
        "event_type": event_type,
        "observed_at": observer_event.get("timestamp"),
        "source_stream": "passive_observer",
        "payload": payload,
        "evidence": evidence,
        "graph_hint": graph_hint,
    }



def observer_snapshot_to_reducer_events(snapshot: dict[str, object], *, event_id_prefix: str = "observer") -> list[dict[str, object]]:
    events = snapshot.get("events")
    if not isinstance(events, list):
        return []

    normalized_events: list[dict[str, object]] = []
    for index, observer_event in enumerate(events, start=1):
        if not isinstance(observer_event, dict):
            continue
        normalized_events.append(
            observer_event_to_reducer_event(
                observer_event,
                event_id=f"{event_id_prefix}-{index}",
            )
        )
    return normalized_events


class RuntimeCorrelationReducer:
    def __init__(self) -> None:
        self._graph_index = 0
        self._active_graph = build_initial_graph(0)
        self._archived_graphs: list[dict[str, object]] = []

    def current_graph(self) -> dict[str, object]:
        return self._active_graph

    def archived_graphs(self) -> list[dict[str, object]]:
        return deepcopy(self._archived_graphs)

    def current_snapshot(self) -> dict[str, object]:
        return build_snapshot(self._active_graph)

    def apply_event(self, event: dict[str, object]) -> dict[str, object]:
        rotate, reason = should_rotate_graph(self._active_graph, event)
        if rotate:
            self._archived_graphs.append(archive_graph(self._active_graph, reason or "unknown"))
            self._graph_index += 1
            self._active_graph = build_initial_graph(self._graph_index)

        apply_event_to_graph(self._active_graph, event)
        return build_snapshot(self._active_graph)


def should_rotate_graph(graph: dict[str, object], event: dict[str, object]) -> tuple[bool, str | None]:
    event_type = event.get("event_type")
    payload = event.get("payload", {})
    session_id = payload.get("sessionId") if isinstance(payload, dict) else None

    if event_type == "LS_START":
        ls_pid = payload.get("ls_pid") if isinstance(payload, dict) else None
        if graph["last_ls_pid"] is not None and ls_pid != graph["last_ls_pid"]:
            return True, "LS PID changed"

    if event_type == "EXTENSION_HOST_START":
        extension_host_pid = payload.get("pid") if isinstance(payload, dict) else None
        if graph["last_extension_host_pid"] is not None and extension_host_pid != graph["last_extension_host_pid"]:
            return True, "Extension Host restart detected"

    if session_id and graph["session_mapping"]["sessionId"] not in {None, session_id}:
        return True, "sessionId changed"

    if event_type == "PORT_BOUND":
        port = payload.get("port") if isinstance(payload, dict) else None
        owner_pid = payload.get("owner_pid") if isinstance(payload, dict) else None
        existing_owner = graph["bound_ports"].get(port)
        if existing_owner is not None and existing_owner != owner_pid:
            return True, "port rebinding occurred"

    return False, None


def merge_evidence_summary(graph: dict[str, object], payload: dict[str, object]) -> None:
    evidence_source = payload.get("evidenceSource")
    if not isinstance(evidence_source, dict):
        return

    evidence_kind = evidence_source.get("kind")
    if not isinstance(evidence_kind, str):
        return

    summary = graph["passive_evidence_summary"].setdefault(
        evidence_kind,
        {
            "count": 0,
            "paths": [],
            "reasons": [],
        },
    )
    summary["count"] += 1

    source_path = payload.get("sourcePath")
    if isinstance(source_path, str) and source_path not in summary["paths"]:
        summary["paths"].append(source_path)

    reason = evidence_source.get("reason")
    if isinstance(reason, str) and reason not in summary["reasons"]:
        summary["reasons"].append(reason)



def apply_event_to_graph(graph: dict[str, object], event: dict[str, object]) -> None:
    graph["events"].append(event.get("event_id"))
    event_type = event.get("event_type")
    payload = event.get("payload", {})
    observed_at = event.get("observed_at")
    event_id = event.get("event_id")

    if event_type == "LS_START":
        graph["last_ls_pid"] = payload.get("ls_pid")
        graph["language_server"] = {
            "pid": payload.get("ls_pid"),
            "ports": payload.get("ports", []),
            "sessionId": payload.get("sessionId"),
        }
        if payload.get("sessionId"):
            graph["session_mapping"]["sessionId"] = payload.get("sessionId")
        return

    if event_type == "EXTENSION_HOST_START":
        graph["last_extension_host_pid"] = payload.get("pid")
        graph["extension_host"] = {"pid": payload.get("pid")}
        return

    if event_type == "NODE_SERVICE_START":
        graph["node_service"] = {"pid": payload.get("pid"), "port": payload.get("port")}
        return

    if event_type == "PORT_BOUND":
        port = payload.get("port")
        owner_pid = payload.get("owner_pid")
        graph["bound_ports"][port] = owner_pid
        return

    if event_type == "START_CASCADE":
        graph["cascade_flow"]["startCascade"] = True
        if payload.get("sessionId"):
            graph["session_mapping"]["sessionId"] = payload.get("sessionId")
        graph["last_start_cascade"] = {
            "event_id": event_id,
            "observed_at": observed_at,
            "payload": deepcopy(payload),
        }
        merge_evidence_summary(graph, payload)
        graph["unlinked_evidence"].append({"event_id": event_id, "event_type": event_type})
        return

    if event_type == "SEND_USER_CASCADE_MESSAGE":
        graph["cascade_flow"]["sendUserCascadeMessage"] = True
        graph["last_send_user_cascade_message_at"] = observed_at
        if payload.get("sessionId"):
            graph["session_mapping"]["sessionId"] = payload.get("sessionId")
        graph["last_send_user_cascade_message"] = {
            "event_id": event_id,
            "observed_at": observed_at,
            "payload": deepcopy(payload),
        }
        merge_evidence_summary(graph, payload)
        graph["unlinked_evidence"].append({"event_id": event_id, "event_type": event_type})
        return

    if event_type == "TRACE_COUNT_DELTA":
        delta = payload.get("delta", 0)
        graph["cascade_flow"]["traceCount"] += int(delta)
        graph["trace_count_events"].append(
            {
                "event_id": event_id,
                "observed_at": observed_at,
                "payload": deepcopy(payload),
                "traceCount": graph["cascade_flow"]["traceCount"],
            }
        )
        merge_evidence_summary(graph, payload)
        return

    if event_type == "SESSION_ID_PROPAGATION":
        if payload.get("sessionId"):
            graph["session_mapping"]["sessionId"] = payload.get("sessionId")
        graph["session_mapping"]["propagation_path"] = [payload.get("from"), payload.get("to")]
        graph["edges"].append(
            {
                "from": payload.get("from"),
                "to": payload.get("to"),
                "kind": "propagates_session_to",
                "evidence_type": "SESSION_ID_PROPAGATION",
                "evidence_event_ids": [event_id],
                "observed_at": observed_at,
            }
        )
        return

    if event_type == "CONNECT_HTTP_ESTABLISHED":
        graph["edges"].append(
            {
                "from": payload.get("src"),
                "to": payload.get("dst"),
                "kind": "connects_to",
                "evidence_type": "CONNECT_HTTP_ESTABLISHED",
                "evidence_event_ids": [event_id],
                "observed_at": observed_at,
            }
        )
        return

    if event_type == "CDP_NETWORK_REQUEST_WILL_BE_SENT":
        if payload.get("sessionId"):
            graph["session_mapping"]["sessionId"] = payload.get("sessionId")
        graph["cdp_network_requests"].append(
            {
                "event_id": event_id,
                "observed_at": observed_at,
                "url": payload.get("url"),
                "requestId": payload.get("requestId"),
            }
        )
        return

    if event_type == "CDP_NETWORK_RESPONSE_RECEIVED":
        if payload.get("sessionId"):
            graph["session_mapping"]["sessionId"] = payload.get("sessionId")
        graph["cdp_network_responses"].append(
            {
                "event_id": event_id,
                "observed_at": observed_at,
                "status": payload.get("status"),
                "url": payload.get("url"),
                "requestId": payload.get("requestId"),
            }
        )
        return

    if event_type == "CDP_WEBSOCKET_CREATED":
        if payload.get("sessionId"):
            graph["session_mapping"]["sessionId"] = payload.get("sessionId")
        graph["cdp_websocket_creations"].append(
            {
                "event_id": event_id,
                "observed_at": observed_at,
                "url": payload.get("url"),
                "requestId": payload.get("requestId"),
            }
        )
        return


def build_forensic_events(graph: dict[str, object]) -> list[dict[str, object]]:
    session_id = graph["session_mapping"].get("sessionId")
    trace_count = graph["cascade_flow"].get("traceCount", 0)
    ls_pid = graph["language_server"].get("pid") if isinstance(graph.get("language_server"), dict) else None
    events: list[dict[str, object]] = []

    for edge in graph["edges"]:
        evidence_type = edge.get("evidence_type")
        if evidence_type == "SESSION_ID_PROPAGATION":
            events.append(
                {
                    "type": "IPC",
                    "name": "SESSION_ID_PROPAGATION",
                    "timestamp": edge.get("observed_at"),
                    "pid": ls_pid,
                    "direction": "upstream",
                    "metadata": {
                        "sessionId": session_id,
                        "traceCount": trace_count,
                    },
                }
            )
        elif evidence_type == "CONNECT_HTTP_ESTABLISHED":
            events.append(
                {
                    "type": "HTTP",
                    "name": "CONNECT_HTTP_ESTABLISHED",
                    "timestamp": edge.get("observed_at"),
                    "pid": ls_pid,
                    "direction": "upstream",
                    "metadata": {
                        "sessionId": session_id,
                        "traceCount": trace_count,
                    },
                }
            )

    for request in graph.get("cdp_network_requests", []):
        events.append(
            {
                "type": "HTTP",
                "name": "CDP_NETWORK_REQUEST_WILL_BE_SENT",
                "timestamp": request.get("observed_at"),
                "pid": ls_pid,
                "direction": "upstream",
                "metadata": {
                    "sessionId": session_id,
                    "traceCount": trace_count,
                    "url": request.get("url"),
                },
            }
        )

    for response in graph.get("cdp_network_responses", []):
        events.append(
            {
                "type": "HTTP",
                "name": "CDP_NETWORK_RESPONSE_RECEIVED",
                "timestamp": response.get("observed_at"),
                "pid": ls_pid,
                "direction": "downstream",
                "metadata": {
                    "sessionId": session_id,
                    "traceCount": trace_count,
                    "status": response.get("status"),
                    "url": response.get("url"),
                },
            }
        )

    for websocket in graph.get("cdp_websocket_creations", []):
        events.append(
            {
                "type": "WS",
                "name": "CDP_WEBSOCKET_CREATED",
                "timestamp": websocket.get("observed_at"),
                "pid": ls_pid,
                "direction": "upstream",
                "metadata": {
                    "sessionId": session_id,
                    "traceCount": trace_count,
                    "url": websocket.get("url"),
                },
            }
        )

    last_start_cascade = graph.get("last_start_cascade")
    if isinstance(last_start_cascade, dict):
        start_payload = last_start_cascade.get("payload")
        if isinstance(start_payload, dict):
            events.append(
                {
                    "type": "IPC",
                    "name": "START_CASCADE",
                    "timestamp": last_start_cascade.get("observed_at"),
                    "pid": ls_pid,
                    "direction": "upstream",
                    "metadata": {
                        "sessionId": session_id,
                        "traceCount": trace_count,
                    },
                    "sourcePath": start_payload.get("sourcePath"),
                    "evidenceSource": deepcopy(start_payload.get("evidenceSource")),
                }
            )

    last_send_user_cascade_message = graph.get("last_send_user_cascade_message")
    if isinstance(last_send_user_cascade_message, dict):
        send_payload = last_send_user_cascade_message.get("payload")
        if isinstance(send_payload, dict):
            events.append(
                {
                    "type": "IPC",
                    "name": "SEND_USER_CASCADE_MESSAGE",
                    "timestamp": last_send_user_cascade_message.get("observed_at"),
                    "pid": ls_pid,
                    "direction": "upstream",
                    "metadata": {
                        "sessionId": session_id,
                        "traceCount": trace_count,
                    },
                    "sourcePath": send_payload.get("sourcePath"),
                    "evidenceSource": deepcopy(send_payload.get("evidenceSource")),
                }
            )

    for trace_event in graph.get("trace_count_events", []):
        payload = trace_event.get("payload")
        if not isinstance(payload, dict):
            continue
        events.append(
            {
                "type": "TRACE",
                "name": "TRACE_COUNT_DELTA",
                "timestamp": trace_event.get("observed_at"),
                "pid": ls_pid,
                "direction": "internal",
                "metadata": {
                    "sessionId": payload.get("sessionId") or session_id,
                    "traceCount": trace_event.get("traceCount"),
                    "traceDelta": payload.get("delta", 0),
                },
                "sourcePath": payload.get("sourcePath"),
                "evidenceSource": deepcopy(payload.get("evidenceSource")),
            }
        )

    return events



def build_forensic_correlation(graph: dict[str, object]) -> dict[str, object]:
    session_id = graph["session_mapping"].get("sessionId")
    propagation_path = graph["session_mapping"].get("propagation_path", [])
    session_clusters = []
    if session_id and propagation_path:
        session_clusters.append([session_id, *propagation_path])
    return {
        "sessionId_clusters": session_clusters,
        "cascade_chain_detected": bool(
            graph["cascade_flow"].get("startCascade")
            and graph["cascade_flow"].get("sendUserCascadeMessage")
        ),
        "evidenceSummary": deepcopy(graph.get("passive_evidence_summary", {})),
    }



def build_snapshot(graph: dict[str, object]) -> dict[str, object]:
    if graph["cascade_flow"]["startCascade"] and graph["edges"]:
        confidence = "medium"
        llm_reason = "StartCascade observed with at least one justified runtime edge"
    elif graph["cascade_flow"]["startCascade"]:
        confidence = "low"
        llm_reason = "StartCascade observed without a justified runtime link"
    else:
        confidence = "low"
        llm_reason = "No accepted runtime activity"

    events = build_forensic_events(graph)
    correlation = build_forensic_correlation(graph)
    if correlation["cascade_chain_detected"] and graph["cascade_flow"].get("traceCount", 0) > 0:
        status = "observing"
        reason = None
    elif events:
        status = "partial_signal"
        reason = None
    else:
        status = "no_activity"
        reason = "no CDP/IPC/WS cascade signals observed"

    return {
        "graph_id": graph["graph_id"],
        "node_service": deepcopy(graph["node_service"]),
        "language_server": deepcopy(graph["language_server"]),
        "extension_host": deepcopy(graph["extension_host"]),
        "edges": deepcopy(graph["edges"]),
        "events": events,
        "correlation": correlation,
        "status": status,
        "reason": reason,
        "cascade_flow": deepcopy(graph["cascade_flow"]),
        "session_mapping": deepcopy(graph["session_mapping"]),
        "llm_state": {
            "active": bool(graph["cascade_flow"]["startCascade"] or graph["cascade_flow"]["sendUserCascadeMessage"]),
            "confidence": confidence,
            "reason": llm_reason,
        },
    }



def load_passive_observer_module() -> object:
    module_path = pathlib.Path(__file__).with_name("windsurf_passive_cascade_observer.py")
    spec = importlib.util.spec_from_file_location("windsurf_passive_cascade_observer", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load passive observer module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



def list_passive_sources(paths: list[str] | None = None) -> dict[str, object]:
    observer_module = load_passive_observer_module()
    discovered_paths = observer_module.discover_live_runtime_paths()
    provided_paths = [pathlib.Path(path) for path in paths] if paths else []
    merged_paths = observer_module.prioritize_observer_paths([*discovered_paths, *provided_paths])

    return {
        "discovered": [str(path) for path in discovered_paths],
        "provided": [str(path) for path in provided_paths],
        "selected": [str(path) for path in merged_paths],
    }



def run_passive_correlation(paths: list[str] | None = None) -> dict[str, object]:
    observer_module = load_passive_observer_module()
    if paths:
        observer_snapshot = observer_module.observe_preferred_passive_cascade(paths)
    else:
        observer_snapshot = observer_module.observe_preferred_passive_cascade()

    reducer = RuntimeCorrelationReducer()
    for event in observer_snapshot_to_reducer_events(observer_snapshot, event_id_prefix="observer"):
        reducer.apply_event(event)

    snapshot = reducer.current_snapshot()
    snapshot["observer"] = {
        "status": observer_snapshot.get("status"),
        "reason": observer_snapshot.get("reason"),
        "evidenceSummary": deepcopy(observer_snapshot.get("evidenceSummary", {})),
        "eventCount": len(observer_snapshot.get("events", [])) if isinstance(observer_snapshot.get("events"), list) else 0,
    }
    snapshot["sources"] = list_passive_sources(paths)
    return snapshot



def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a runtime correlation graph from passive Windsurf observer data.")
    parser.add_argument("paths", nargs="*", help="Optional JSONL paths to include alongside discovered live runtime paths.")
    parser.add_argument("--output", help="Optional path to write the final graph snapshot JSON.")
    parser.add_argument("--list-sources", action="store_true", help="List discovered and selected passive sources without running correlation.")
    return parser.parse_args(argv)



def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list_sources:
        rendered = json.dumps(list_passive_sources(args.paths or None), indent=2)
    else:
        rendered = json.dumps(run_passive_correlation(args.paths or None), indent=2)
    if args.output:
        output_path = pathlib.Path(args.output)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
