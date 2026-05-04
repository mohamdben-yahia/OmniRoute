#!/usr/bin/env python3
import base64
import ctypes
import gzip
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import socket
import subprocess
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from ctypes import wintypes
from datetime import datetime, timezone

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    from runtime_ls_state import RuntimeLSRegistry
except ModuleNotFoundError:
    runtime_ls_state_path = pathlib.Path(__file__).with_name("runtime_ls_state.py")
    runtime_ls_state_spec = importlib.util.spec_from_file_location(
        "runtime_ls_state",
        runtime_ls_state_path,
    )
    if runtime_ls_state_spec is None or runtime_ls_state_spec.loader is None:
        raise ModuleNotFoundError("Unable to load runtime_ls_state.py")
    runtime_ls_state_module = importlib.util.module_from_spec(runtime_ls_state_spec)
    runtime_ls_state_spec.loader.exec_module(runtime_ls_state_module)
    RuntimeLSRegistry = runtime_ls_state_module.RuntimeLSRegistry

# Import the full protobuf parser
try:
    from protobuf_parser import parse_trajectory_response, extract_model_router_uid as pb_extract_model_router_uid
except ModuleNotFoundError:
    protobuf_parser_path = pathlib.Path(__file__).with_name("protobuf_parser.py")
    protobuf_parser_spec = importlib.util.spec_from_file_location(
        "protobuf_parser",
        protobuf_parser_path,
    )
    if protobuf_parser_spec is None or protobuf_parser_spec.loader is None:
        print("Warning: Unable to load protobuf_parser.py - using fallback regex extraction")
        parse_trajectory_response = None
        pb_extract_model_router_uid = None
    else:
        protobuf_parser_module = importlib.util.module_from_spec(protobuf_parser_spec)
        protobuf_parser_spec.loader.exec_module(protobuf_parser_module)
        parse_trajectory_response = protobuf_parser_module.parse_trajectory_response
        pb_extract_model_router_uid = protobuf_parser_module.extract_model_router_uid

TOKEN_ENV_VAR = "WINDSURF_DIRECT_KEY"
DEFAULT_IDE_VERSION = "1.108.2"
DEFAULT_EXTENSION_VERSION = "1.108.2"
VALIDATE_BASE_URL = "https://server.self-serve.windsurf.com"
DEFAULT_CHAT_BASE_URL = "https://eu.windsurf.com/_route/api_server"
DEFAULT_LOCAL_LANGUAGE_SERVER_URL = "http://127.0.0.1:53740"
DEFAULT_LS_HOST_HEADER = "q.localhost:53740"
DEFAULT_LOCAL_ORIGIN = "vscode-file://vscode-app"
VALIDATE_URL = f"{VALIDATE_BASE_URL}/exa.seat_management_pb.SeatManagementService/GetUserStatus"
runtime_ls_registry = RuntimeLSRegistry()

LOCAL_LS_HOST_ALIAS_BY_RPC = {
    "StartCascade": "l",
    "SendUserCascadeMessage": "e",
    "GetCascadeTrajectory": "l",
    "CheckUserMessageRateLimit": "l",
    "GetModelStatuses": "b",
    "GetUserStatus": "w",
}

OBSERVATION_LAYER_DIRECT = "direct_probe"
OBSERVATION_LAYER_LS_EMULATOR = "ls_emulator"
OBSERVATION_LAYER_REPLAY = "replay_emulator"
ALLOWED_OBSERVATION_LAYERS = {
    OBSERVATION_LAYER_DIRECT,
    OBSERVATION_LAYER_LS_EMULATOR,
    OBSERVATION_LAYER_REPLAY,
}

_LOCAL_PROBE_ENV_LOADED = False
_LOCAL_PROBE_ENV_LOADED_PATH: pathlib.Path | None = None


def get_local_probe_env_path() -> pathlib.Path:
    configured = os.environ.get("WINDSURF_LOCAL_ENV_PATH", "").strip()
    if configured:
        return pathlib.Path(configured)
    return pathlib.Path(__file__).resolve().parents[1] / ".env.windsurf.local"


def load_local_probe_env_file() -> None:
    global _LOCAL_PROBE_ENV_LOADED
    global _LOCAL_PROBE_ENV_LOADED_PATH

    env_path = get_local_probe_env_path()
    if _LOCAL_PROBE_ENV_LOADED and _LOCAL_PROBE_ENV_LOADED_PATH == env_path:
        return

    if not env_path.exists():
        _LOCAL_PROBE_ENV_LOADED = True
        _LOCAL_PROBE_ENV_LOADED_PATH = env_path
        return

    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key or key in os.environ:
                continue
            os.environ[key] = value.strip()
    finally:
        _LOCAL_PROBE_ENV_LOADED = True
        _LOCAL_PROBE_ENV_LOADED_PATH = env_path


load_local_probe_env_file()


def get_service_url(service_path: str, method_name: str) -> str:
    return f"{get_chat_base_url()}/{service_path}/{method_name}"


def get_chat_base_url() -> str:
    return os.environ.get("WINDSURF_CHAT_BASE_URL", DEFAULT_CHAT_BASE_URL).rstrip("/")


def get_chat_service() -> str:
    return os.environ.get("WINDSURF_CHAT_SERVICE", "api").strip().lower()


def get_chat_method_name() -> str:
    default_method_name = "GetChatMessage" if get_chat_service() == "api" else "RawGetChatMessage"
    return os.environ.get(
        "WINDSURF_CHAT_METHOD_NAME",
        default_method_name,
    ).strip() or default_method_name


def get_chat_url() -> str:
    service_path = (
        "exa.api_server_pb.ApiServerService"
        if get_chat_service() == "api"
        else "exa.language_server_pb.LanguageServerService"
    )
    return get_service_url(service_path, get_chat_method_name())


def get_assign_model_method_name() -> str:
    return os.environ.get("WINDSURF_ASSIGN_MODEL_METHOD_NAME", "AssignModel").strip() or "AssignModel"


def get_assign_model_url() -> str:
    return get_service_url("exa.api_server_pb.ApiServerService", get_assign_model_method_name())


def get_runtime_ls_binding_path() -> pathlib.Path:
    configured = os.environ.get("WINDSURF_RUNTIME_LS_BINDING_PATH", "").strip()
    if configured:
        return pathlib.Path(configured)
    return pathlib.Path(__file__).resolve().parents[1] / "tmp_windsurf_runtime_ls_binding.json"



def load_persisted_runtime_ls_binding() -> None:
    global runtime_ls_registry
    if runtime_ls_registry.get_current() is not None:
        return
    binding_path = get_runtime_ls_binding_path()
    if not binding_path.exists():
        return
    try:
        payload = json.loads(binding_path.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(payload, dict):
        return
    try:
        binding = runtime_ls_registry.on_language_server_started(
            session_id=str(payload["session_id"]),
            window_id=str(payload["window_id"]),
            host=str(payload["host"]),
            port=int(payload["port"]),
            lifecycle_nonce=str(payload["lifecycle_nonce"]),
            timestamp=float(payload["timestamp"]),
            csrf_token=(
                str(payload["csrf_token"]).strip()
                if payload.get("csrf_token") is not None and str(payload.get("csrf_token")).strip()
                else None
            ),
        )
    except Exception:
        return
    if payload.get("state") == "confirmed":
        try:
            runtime_ls_registry.confirm(binding.lifecycle_nonce)
        except Exception:
            return



def persist_runtime_ls_binding(binding) -> None:
    get_runtime_ls_binding_path().write_text(
        json.dumps(serialize_runtime_ls_binding(binding), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )



def build_candidate_runtime_ls_binding(discovery: dict[str, object]) -> dict[str, object] | None:
    if discovery.get("status") != "READY":
        return None
    port = discovery.get("primary_ls_port")
    if not isinstance(port, int) or port <= 0:
        return None
    observed_at = discovery.get("observed_at")
    return {
        "session_id": str(discovery.get("ls_pid") or f"candidate-{port}"),
        "window_id": str(discovery.get("node_service_pid") or "discovered-window"),
        "host": "127.0.0.1",
        "port": port,
        "lifecycle_nonce": f"discovered-{port}",
        "timestamp": time.time(),
        "csrf_token": None,
        "state": "candidate",
        "source": "DISCOVERED",
        "bindingValidated": False,
        "lastValidationAt": observed_at if isinstance(observed_at, str) else datetime.now(timezone.utc).isoformat(),
        "candidateBindings": [
            {
                "port": port,
                "status": discovery.get("status"),
                "lsPid": discovery.get("ls_pid"),
                "observedAt": observed_at,
            }
        ],
    }



def validate_candidate_runtime_ls_binding(candidate: dict[str, object]) -> bool:
    port = candidate.get("port")
    if not isinstance(port, int) or port <= 0:
        return False
    try:
        with socket.create_connection((str(candidate.get("host") or "127.0.0.1"), port), timeout=0.2):
            return True
    except OSError:
        return False



def refresh_runtime_ls_binding_from_live_discovery() -> dict[str, object]:
    load_persisted_runtime_ls_binding()
    current = runtime_ls_registry.get_current()
    discovery = discover_runtime_ls_registry_state()
    candidate = build_candidate_runtime_ls_binding(discovery)
    now = datetime.now(timezone.utc).isoformat()

    if candidate is None:
        return {
            "bindingSource": getattr(current, "source", "PERSISTED") if current is not None else "PERSISTED",
            "bindingValidated": False,
            "lastValidationAt": now,
            "candidateBindings": [],
            "runtimeState": "RESET_CANDIDATE",
        }

    if not validate_candidate_runtime_ls_binding(candidate):
        if current is not None:
            current.source = getattr(current, "source", "PERSISTED")
            current.binding_validated = False
            current.last_validation_at = now
            current.candidate_bindings = candidate.get("candidateBindings", [])
        return {
            "bindingSource": getattr(current, "source", "PERSISTED") if current is not None else "PERSISTED",
            "bindingValidated": False,
            "lastValidationAt": now,
            "candidateBindings": candidate.get("candidateBindings", []),
            "runtimeState": "RESET_CANDIDATE",
        }

    history = []
    if current is not None:
        history.append(serialize_runtime_ls_binding(current))
    binding = runtime_ls_registry.on_language_server_started(
        session_id=str(candidate["session_id"]),
        window_id=str(candidate["window_id"]),
        host=str(candidate["host"]),
        port=int(candidate["port"]),
        lifecycle_nonce=str(candidate["lifecycle_nonce"]),
        timestamp=float(candidate["timestamp"]),
        csrf_token=None,
    )
    binding = runtime_ls_registry.confirm(binding.lifecycle_nonce)
    binding.source = "DISCOVERED"
    binding.binding_validated = True
    binding.last_validation_at = now
    binding.candidate_bindings = candidate.get("candidateBindings", [])
    binding.binding_history = history
    persist_runtime_ls_binding(binding)
    return {
        "bindingSource": "LIVE_DISCOVERY",
        "bindingValidated": True,
        "lastValidationAt": now,
        "candidateBindings": candidate.get("candidateBindings", []),
        "runtimeState": "READY",
    }



def is_runtime_ls_binding_reachable(timeout: float = 0.2) -> bool:
    load_persisted_runtime_ls_binding()
    binding = runtime_ls_registry.get_current()
    if binding is None or getattr(binding, "state", None) != "confirmed":
        return False
    try:
        with socket.create_connection((binding.host, int(binding.port)), timeout=timeout):
            return True
    except OSError:
        return False



def get_live_bootstrap_path() -> pathlib.Path:
    configured = os.environ.get("WINDSURF_LIVE_BOOTSTRAP_PATH", "").strip()
    if configured:
        return pathlib.Path(configured)
    return pathlib.Path(__file__).resolve().parents[1] / "windsurf-live-bootstrap.json"



def read_live_bootstrap_payload() -> dict[str, object]:
    path = get_live_bootstrap_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}



def get_local_language_server_bootstrap_state() -> dict[str, object]:
    load_persisted_runtime_ls_binding()
    binding = runtime_ls_registry.get_current()
    live_bootstrap = read_live_bootstrap_payload()
    env_csrf_token = os.environ.get("WINDSURF_CSRF_TOKEN", "").strip()
    live_csrf_token = live_bootstrap.get("csrfToken") if isinstance(live_bootstrap.get("csrfToken"), str) else None
    live_language_server_url = live_bootstrap.get("languageServerUrl") if isinstance(live_bootstrap.get("languageServerUrl"), str) else None

    return {
        "languageServerUrl": binding.url if binding is not None else live_language_server_url,
        "csrfToken": (
            binding.csrf_token
            or (live_csrf_token.strip() if isinstance(live_csrf_token, str) and live_csrf_token.strip() else None)
            or env_csrf_token
            or None
        ) if binding is not None else (
            (live_csrf_token.strip() if isinstance(live_csrf_token, str) and live_csrf_token.strip() else None)
            or env_csrf_token
            or None
        ),
    }


def discover_runtime_ls_url() -> str | None:
    state = discover_runtime_ls_registry_state()
    if state.get("status") != "READY":
        return None
    port = state.get("primary_ls_port")
    if isinstance(port, int) and port > 0:
        return f"http://127.0.0.1:{port}"
    return None


def get_windsurf_lifecycle_trace_path() -> pathlib.Path:
    configured = os.environ.get("WINDSURF_ELECTRON_LIFECYCLE_TRACE_PATH", "").strip()
    if configured:
        return pathlib.Path(configured)
    return pathlib.Path(__file__).resolve().parents[1] / "windsurf-electron-lifecycle-trace.jsonl"


def read_canonical_lifecycle_flags() -> dict[str, bool]:
    flags = {
        "renderer_pid_changed": False,
        "target_destroyed": False,
        "execution_context_destroyed": False,
    }
    trace_path = get_windsurf_lifecycle_trace_path()
    if not trace_path.exists():
        return flags

    try:
        lines = trace_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return flags

    for line in lines:
        try:
            event = json.loads(line)
        except Exception:
            continue
        event_name = event.get("event")
        if event_name == "Runtime.executionContextDestroyed":
            flags["execution_context_destroyed"] = True
        elif event_name == "Target.targetDestroyed":
            flags["target_destroyed"] = True
    return flags


def derive_active_graph_snapshot() -> dict[str, object]:
    trace_path = get_windsurf_lifecycle_trace_path()
    empty_snapshot = {
        "graph_id": "G1",
        "reset_detected": False,
        "renderer_state": {
            "t0_renderer_start": {"status": "absent", "observed": False},
            "t1_webcontents_proxy_active": {"status": "absent", "observed": False},
            "t2_ipc_bridge_live": {"status": "absent", "observed": False},
            "t3_network_active": {"status": "absent", "observed": False},
        },
    }
    if not trace_path.exists():
        return empty_snapshot

    try:
        lines = trace_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return empty_snapshot

    def new_graph(index: int) -> dict[str, object]:
        return {
            "graph_id": f"G{index}",
            "reset_detected": False,
            "renderer_state": {
                "t0_renderer_start": {"status": "absent", "observed": False},
                "t1_webcontents_proxy_active": {"status": "absent", "observed": False},
                "t2_ipc_bridge_live": {"status": "absent", "observed": False},
                "t3_network_active": {"status": "absent", "observed": False},
            },
        }

    graphs: list[dict[str, object]] = []
    current = new_graph(1)
    graphs.append(current)
    current_renderer_pid = None
    current_target_id = None

    for line in lines:
        try:
            event = json.loads(line)
        except Exception:
            continue
        event_name = event.get("event")
        renderer_pid = event.get("renderer_pid")
        target_id = event.get("target_id")

        if renderer_pid is not None and current_renderer_pid is not None and renderer_pid != current_renderer_pid:
            current = new_graph(len(graphs) + 1)
            graphs.append(current)
            current_target_id = None
        if target_id is not None and current_target_id is not None and target_id != current_target_id:
            current = new_graph(len(graphs) + 1)
            graphs.append(current)
        if renderer_pid is not None:
            current_renderer_pid = renderer_pid
        if target_id is not None:
            current_target_id = target_id

        if event_name in {"renderer-script-executed", "Runtime.executionContextCreated"}:
            current["renderer_state"]["t0_renderer_start"] = {"status": "confirmed", "observed": True}
        elif event_name in {"Page.frameNavigated", "DOMContentLoaded", "loadEventFired", "spa-hydration-start"}:
            current["renderer_state"]["t1_webcontents_proxy_active"] = {"status": "confirmed", "observed": True}
        elif event_name == "bridge-response":
            current["renderer_state"]["t2_ipc_bridge_live"] = {"status": "confirmed", "observed": True}
        elif event_name in {"Network.requestWillBeSent", "Network.webSocketCreated", "fetch-request", "xhr-request", "websocket-open"}:
            current["renderer_state"]["t3_network_active"] = {"status": "confirmed", "observed": True}
        elif event_name in {"Runtime.executionContextDestroyed", "Target.targetDestroyed"}:
            current = new_graph(len(graphs) + 1)
            graphs.append(current)
            current_renderer_pid = None
            current_target_id = None

    return graphs[-1] if graphs else empty_snapshot


def discover_runtime_ls_registry_state() -> dict[str, object]:
    command = (
        "$ls = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'language_server_windows_x64.exe' } | "
        "Sort-Object CreationDate -Descending; "
        "if (-not $ls) { @{ status='NO_LS_RUNTIME'; reason='language_server_windows_x64.exe not found' } | ConvertTo-Json -Compress; return }; "
        "$selected = $ls | Select-Object -First 1; "
        "$cmd = [string]$selected.CommandLine; "
        "$allPorts = @(); "
        "$lsp = [regex]::Match($cmd, '--lsp_port\\s+(\\d+)'); if ($lsp.Success) { $allPorts += [int]$lsp.Groups[1].Value }; "
        "$ext = [regex]::Match($cmd, '--extension_server_port\\s+(\\d+)'); if ($ext.Success) { $allPorts += [int]$ext.Groups[1].Value }; "
        "$nodeServicePid = if ($selected.ParentProcessId) { [int]$selected.ParentProcessId } else { $null }; "
        "$logRoot = Join-Path $env:APPDATA 'Windsurf\\logs'; "
        "$latestExthost = Get-ChildItem -Path $logRoot -Filter exthost.log -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1; "
        "$messageportTerminated = if ($latestExthost) { Select-String -Path $latestExthost.FullName -Pattern 'renderer closed the MessagePort' -Quiet } else { $false }; "
        "$rendererPidChanged = $false; "
        "$targetDestroyed = $false; "
        "$executionContextDestroyed = $false; "
        "$listening = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -eq $selected.ProcessId } | Select-Object -ExpandProperty LocalPort; "
        "$listeningPorts = @($listening | ForEach-Object { [int]$_ }); "
        "$allPorts = @($allPorts + $listeningPorts | Sort-Object -Unique); "
        "if ($allPorts.Count -eq 0) { @{ status='BOOTING'; ls_pid=$selected.ProcessId; active_ports=@(); primary_ls_port=$null; extension_port=if ($ext.Success) { [int]$ext.Groups[1].Value } else { $null }; node_service_pid=$nodeServicePid; messageport_terminated=$messageportTerminated; renderer_pid_changed=$rendererPidChanged; target_destroyed=$targetDestroyed; execution_context_destroyed=$executionContextDestroyed } | ConvertTo-Json -Compress; return }; "
        "$primary = if ($listeningPorts.Count -gt 0) { [int]($listeningPorts | Sort-Object | Select-Object -First 1) } else { $null }; "
        "$status = if ($primary -ne $null) { 'READY' } else { 'STALE_PORT' }; "
        "@{ status=$status; ls_pid=$selected.ProcessId; active_ports=$allPorts; primary_ls_port=$primary; extension_port=if ($ext.Success) { [int]$ext.Groups[1].Value } else { $null }; node_service_pid=$nodeServicePid; messageport_terminated=$messageportTerminated; renderer_pid_changed=$rendererPidChanged; target_destroyed=$targetDestroyed; execution_context_destroyed=$executionContextDestroyed } | ConvertTo-Json -Compress"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return {
            "status": "UNKNOWN",
            "reason": "subprocess failure",
        }

    value = (result.stdout or "").strip()
    if not value:
        return {
            "status": "UNKNOWN",
            "reason": "empty discovery output",
        }

    try:
        payload = json.loads(value.splitlines()[-1].strip())
    except Exception:
        return {
            "status": "UNKNOWN",
            "reason": "invalid discovery payload",
            "raw": value,
        }

    if not isinstance(payload, dict):
        return {
            "status": "UNKNOWN",
            "reason": "discovery payload was not an object",
        }

    payload.update(read_canonical_lifecycle_flags())
    active_graph = derive_active_graph_snapshot()
    renderer_state = active_graph.get("renderer_state", {}) if isinstance(active_graph, dict) else {}
    t1_state = renderer_state.get("t1_webcontents_proxy_active", {}) if isinstance(renderer_state, dict) else {}
    payload["renderer_activity_observed"] = bool(
        isinstance(t1_state, dict) and t1_state.get("observed")
    )
    return payload


def on_language_server_started(
    *,
    session_id: str,
    window_id: str,
    host: str,
    port: int,
    lifecycle_nonce: str,
    timestamp: float,
    csrf_token: str | None,
    confirmed: bool = False,
):
    binding = runtime_ls_registry.on_language_server_started(
        session_id=session_id,
        window_id=window_id,
        host=host,
        port=port,
        lifecycle_nonce=lifecycle_nonce,
        timestamp=timestamp,
        csrf_token=csrf_token,
    )
    if confirmed:
        binding = runtime_ls_registry.confirm(lifecycle_nonce)
    return binding


def on_language_server_stopped(
    *,
    session_id: str,
    window_id: str,
    lifecycle_nonce: str,
    timestamp: float,
):
    return runtime_ls_registry.on_language_server_stopped(
        session_id=session_id,
        window_id=window_id,
        lifecycle_nonce=lifecycle_nonce,
        timestamp=timestamp,
    )


def resolve_live_language_server_url() -> str:
    binding = runtime_ls_registry.get_current()

    if binding is None:
        raise ValueError("No runtime LS binding available")

    if binding.state != "confirmed":
        raise ValueError(f"LS not ready: {binding.state}")

    return binding.url


def get_local_language_server_url() -> str:
    bootstrap_state = get_local_language_server_bootstrap_state()
    language_server_url = bootstrap_state.get("languageServerUrl")
    if isinstance(language_server_url, str) and language_server_url:
        return language_server_url

    discovered = discover_runtime_ls_url()
    if isinstance(discovered, str) and discovered:
        return discovered

    configured = os.environ.get("WINDSURF_LANGUAGE_SERVER_URL", "").strip()
    if configured:
        return configured

    return DEFAULT_LOCAL_LANGUAGE_SERVER_URL


def get_local_language_server_service_url(method_name: str, base_url: str | None = None) -> str:
    resolved_base_url = base_url or get_local_language_server_url()
    return f"{resolved_base_url}/exa.language_server_pb.LanguageServerService/{method_name}"


def get_default_host_header() -> str:
    parsed = urllib.parse.urlparse(get_chat_base_url())
    return parsed.netloc or "server.codeium.com"


def get_local_origin() -> str:
    return os.environ.get("WINDSURF_LOCAL_ORIGIN", DEFAULT_LOCAL_ORIGIN).strip() or DEFAULT_LOCAL_ORIGIN


def get_local_host_header(method_name: str | None = None) -> str:
    configured = os.environ.get("WINDSURF_LS_HOST_HEADER", "").strip()
    if configured:
        return configured

    configured_aliases = os.environ.get("WINDSURF_LS_HOST_ALIAS_MAP", "").strip()
    alias_map = dict(LOCAL_LS_HOST_ALIAS_BY_RPC)
    if configured_aliases:
        for entry in configured_aliases.split(","):
            if ":" not in entry:
                continue
            rpc_name, alias = entry.split(":", 1)
            rpc_name = rpc_name.strip()
            alias = alias.strip()
            if rpc_name and alias:
                alias_map[rpc_name] = alias

    alias = alias_map.get(method_name or "", "q")

    load_persisted_runtime_ls_binding()
    binding = runtime_ls_registry.get_current()
    if binding is not None and getattr(binding, "state", None) == "confirmed":
        return f"{alias}.localhost:{int(binding.port)}"

    if method_name:
        default_port = DEFAULT_LS_HOST_HEADER.rsplit(":", 1)[-1]
        return f"{alias}.localhost:{default_port}"

    return DEFAULT_LS_HOST_HEADER


def build_local_ls_headers(*, method_name: str, csrf_token: str | None = None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/proto",
        "Connect-Protocol-Version": "1",
        "Accept": "application/proto, application/json",
        "User-Agent": os.environ.get(
            "WINDSURF_CONNECT_USER_AGENT",
            "connect-go/1.17.0 (go1.23.4 X:nocoverageredesign)",
        ),
        "Accept-Encoding": "identity",
        "Connect-Accept-Encoding": "gzip",
        "Origin": get_local_origin(),
        "host": get_local_host_header(method_name),
    }

    resolved_csrf_token = csrf_token if csrf_token is not None else get_local_csrf_token()
    if resolved_csrf_token:
        headers["x-codeium-csrf-token"] = resolved_csrf_token
    return headers


def get_local_csrf_token() -> str:
    bootstrap_state = get_local_language_server_bootstrap_state()
    csrf_token = bootstrap_state.get("csrfToken")
    if isinstance(csrf_token, str) and csrf_token.strip():
        return csrf_token.strip()
    return os.environ.get("WINDSURF_CSRF_TOKEN", "").strip()


def classify_runtime_fault_taxonomy(observation: dict[str, object]) -> dict[str, object]:
    canonical_reset = bool(observation.get("canonical_reset")) or bool(observation.get("renderer_pid_changed")) or bool(observation.get("target_destroyed")) or bool(observation.get("execution_context_destroyed"))
    messageport_terminated = bool(observation.get("messageport_terminated"))
    ls_alive = bool(observation.get("ls_alive"))
    node_service_alive = bool(observation.get("node_service_alive"))
    transport_reachable = bool(observation.get("transport_reachable"))
    transport_type = str(observation.get("transport_type") or "unknown")

    state = {
        "t0": "reset" if canonical_reset else "unknown",
        "t1": "unknown",
        "t2": "broken (IPC layer terminated)" if messageport_terminated else "healthy",
        "t3": "confirmed (LS network reachable)" if transport_reachable else "unknown",
    }

    conclusion = {
        "graph_continuity": "RESET" if canonical_reset else "VALID",
        "ipc_layer": "DEGRADED_NOT_RESET" if messageport_terminated and not canonical_reset else ("RESET" if canonical_reset else "HEALTHY"),
        "ls_state": "STABLE" if ls_alive else "DOWN",
        "node_service_state": "STABLE" if node_service_alive else "DOWN",
    }

    return {
        "reset_status": "CANONICAL_RESET" if canonical_reset else "NO_CANONICAL_RESET",
        "transport_type": transport_type,
        "state": state,
        "conclusion": conclusion,
    }


def get_observation_layer(mode: str) -> str:
    if mode in {"validate", "raw-chat", "chat", "api-wrapper", "assign-model", "direct"}:
        return OBSERVATION_LAYER_DIRECT
    if mode in {"cascade", "ls_emulator"}:
        return OBSERVATION_LAYER_LS_EMULATOR
    if mode == "traffic_replay_emulator":
        return OBSERVATION_LAYER_REPLAY
    raise ValueError(f"Unsupported observation layer for mode '{mode}'")


def assert_valid_observation_layer(mode: str) -> str:
    layer = get_observation_layer(mode)
    if layer not in ALLOWED_OBSERVATION_LAYERS:
        raise ValueError(f"invalid observation layer: {layer}")
    return layer


def build_instrumentation_context(mode: str) -> dict[str, object]:
    layer = assert_valid_observation_layer(mode)
    return {
        "instrumentation": {
            "observationLayer": layer,
            "logChannels": {
                "execution": f"{layer}.execution",
                "replay": f"{layer}.replay",
                "transport": f"{layer}.transport",
            },
        }
    }


SYSTEM_NATIVE_TOP_LEVEL_FIELDS = {
    "status",
    "reason",
    "contentType",
    "body",
    "bodyBytes",
    "bodyHex",
    "bodyText",
    "connectDecoded",
    "decodedUnaryProto",
    "cascadeId",
    "assignmentJwt",
    "assignedModelUid",
    "harnessUid",
    "modelRouterUid",
}


def build_field_origin_summary(payload: dict[str, object]) -> dict[str, list[str]]:
    native_fields: list[str] = []
    instrumentation_fields: list[str] = []
    for key in payload.keys():
        if key in SYSTEM_NATIVE_TOP_LEVEL_FIELDS:
            native_fields.append(key)
        else:
            instrumentation_fields.append(key)
    return {
        "system_native": sorted(native_fields),
        "instrumentation_added": sorted(instrumentation_fields),
    }


def assert_instrumentation_not_used_for_routing(payload: dict[str, object]) -> None:
    instrumentation = payload.get("instrumentation")
    if not isinstance(instrumentation, dict):
        return
    forbidden_targets = [
        payload.get("assignedModelUid"),
        payload.get("harnessUid"),
        payload.get("modelRouterUid"),
    ]
    instrumentation_blob = json.dumps(instrumentation, sort_keys=True)
    for value in forbidden_targets:
        if isinstance(value, str) and value and value in instrumentation_blob:
            raise ValueError("instrumentation fields must not influence routing inference")


def build_instrumentation_neutrality_report(a: dict[str, object], b: dict[str, object], c: dict[str, object]) -> dict[str, object]:
    keys = ["assignedModelUid", "harnessUid", "modelRouterUid"]
    values = {
        "A": {key: a.get(key) for key in keys},
        "B": {key: b.get(key) for key in keys},
        "C": {key: c.get(key) for key in keys},
    }
    invariant = all(values["A"].get(key) == values["B"].get(key) == values["C"].get(key) for key in keys)
    return {
        "invariant": invariant,
        "keys": keys,
        "values": values,
    }


def finalize_probe_payload(payload: dict[str, object], *, enforce_native_routing_boundary: bool = True) -> dict[str, object]:
    payload["fieldOrigins"] = build_field_origin_summary(payload)
    if enforce_native_routing_boundary:
        assert_instrumentation_not_used_for_routing(payload)
    return payload


def resolve_session_identity() -> dict[str, str]:
    observed = os.environ.get("WINDSURF_SESSION_ID", "").strip()
    if observed:
        return {
            "value": observed,
            "provenance": "observed",
        }

    synthetic = os.environ.get("WINDSURF_SYNTHETIC_SESSION_ID", "").strip()
    if synthetic:
        return {
            "value": synthetic,
            "provenance": "synthetic",
        }

    load_persisted_runtime_ls_binding()
    binding = runtime_ls_registry.get_current()
    runtime_session_id = binding.session_id.strip() if binding is not None and isinstance(binding.session_id, str) else ""
    if runtime_session_id:
        return {
            "value": runtime_session_id,
            "provenance": "runtime_ls",
        }

    return {
        "value": "",
        "provenance": "missing",
    }


def has_direct_cloud_key() -> bool:
    env_token = os.environ.get(TOKEN_ENV_VAR, "").strip()
    if env_token and not env_token.startswith("devin-session-token"):
        return True

    state_token = get_token_from_windsurf_state()
    if state_token and not state_token.startswith("devin-session-token"):
        return True

    secret_token = get_token_from_windsurf_secret_sessions()
    return bool(secret_token)


def get_windsurf_state_db_path() -> str:
    return os.environ.get(
        "WINDSURF_STATE_DB_PATH",
        "c:/Users/amine/AppData/Roaming/Windsurf/User/globalStorage/state.vscdb",
    )


def get_windsurf_state_value(key: str) -> object:
    try:
        con = sqlite3.connect(get_windsurf_state_db_path())
        try:
            cur = con.cursor()
            cur.execute("select value from ItemTable where key = ?", (key,))
            row = cur.fetchone()
        finally:
            con.close()
    except Exception:
        return None

    if not row:
        return None
    return row[0]


def get_windsurf_local_state_path() -> str:
    return os.environ.get(
        "WINDSURF_LOCAL_STATE_PATH",
        "c:/Users/amine/AppData/Roaming/Windsurf/Local State",
    )


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def dpapi_unprotect(data: bytes) -> bytes:
    if not data:
        return b""

    in_buffer = ctypes.create_string_buffer(data)
    in_blob = DATA_BLOB(len(data), ctypes.cast(in_buffer, ctypes.POINTER(ctypes.c_byte)))
    out_blob = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    if not crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    ):
        raise ctypes.WinError()

    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        if out_blob.pbData:
            kernel32.LocalFree(out_blob.pbData)


def get_windsurf_secret_master_key() -> bytes:
    with open(get_windsurf_local_state_path(), "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    encrypted_key = payload.get("os_crypt", {}).get("encrypted_key")
    if not isinstance(encrypted_key, str) or not encrypted_key:
        return b""

    raw_key = base64.b64decode(encrypted_key)
    if raw_key.startswith(b"DPAPI"):
        raw_key = raw_key[5:]
    return dpapi_unprotect(raw_key)


def read_windsurf_secret(secret_key: str) -> str:
    storage_key = 'secret://{"extensionId":"codeium.windsurf","key":"' + secret_key + '"}'
    raw_value = get_windsurf_state_value(storage_key)
    if not isinstance(raw_value, str):
        return ""

    try:
        payload = json.loads(raw_value)
    except Exception:
        return ""

    encrypted_bytes = payload.get("data")
    if not isinstance(encrypted_bytes, list) or not encrypted_bytes:
        return ""

    ciphertext = bytes(encrypted_bytes)
    if not ciphertext.startswith(b"v10") or len(ciphertext) < 31:
        return ""

    master_key = get_windsurf_secret_master_key()
    if not master_key:
        return ""

    nonce = ciphertext[3:15]
    encrypted_payload = ciphertext[15:]
    plaintext = AESGCM(master_key).decrypt(nonce, encrypted_payload, None)
    return plaintext.decode("utf-8")


def get_token_from_windsurf_state() -> str:
    raw_value = get_windsurf_state_value("windsurfAuthStatus")
    if not isinstance(raw_value, str):
        return ""

    try:
        payload = json.loads(raw_value)
    except Exception:
        return ""

    api_key = payload.get("apiKey")
    if not isinstance(api_key, str):
        return ""

    return api_key.strip()


def get_token_from_windsurf_secret_sessions() -> str:
    raw_value = read_windsurf_secret("windsurf_auth.sessions")
    if not raw_value:
        return ""

    try:
        payload = json.loads(raw_value)
    except Exception:
        return ""

    sessions = payload if isinstance(payload, list) else [payload]
    for session in sessions:
        if not isinstance(session, dict):
            continue
        access_token = session.get("accessToken")
        if not isinstance(access_token, str):
            continue
        token = access_token.strip()
        if not token or token.startswith("devin-session-token"):
            continue
        return token

    return ""


def get_token() -> str:
    token = os.environ.get(TOKEN_ENV_VAR, "").strip()
    if token:
        return token

    token = get_token_from_windsurf_state()
    if token and not token.startswith("devin-session-token"):
        return token

    return get_token_from_windsurf_secret_sessions()



def resolve_auth_context_for_mode(mode: str) -> dict[str, str]:
    env_token = os.environ.get(TOKEN_ENV_VAR, "").strip()
    state_token = get_token_from_windsurf_state()
    session_hint = has_windsurf_session_token_in_state()

    if mode in {"cascade", "ls_emulator", "traffic_replay_emulator"}:
        if env_token:
            return {"token": env_token, "authType": "direct", "hint": ""}
        if state_token:
            return {"token": state_token, "authType": "session", "hint": ""}
        secret_token = get_token_from_windsurf_secret_sessions()
        if secret_token:
            return {"token": secret_token, "authType": "direct", "hint": ""}
        return {
            "token": "",
            "authType": "session",
            "hint": "Set WINDSURF_DIRECT_KEY or provide a Windsurf session token for local cascade mode.",
        }

    token = get_token()
    if token:
        return {"token": token, "authType": "direct", "hint": ""}

    hint = f"Set {TOKEN_ENV_VAR} in your shell before running this script."
    if session_hint:
        hint = (
            f"Set {TOKEN_ENV_VAR} in your shell before running this script. "
            "SQLite only contains a devin-session-token session value, which this probe rejects "
            "because it is not a direct cloud API key."
        )
    return {
        "token": "",
        "authType": "direct",
        "hint": hint,
    }



def has_windsurf_session_token_in_state() -> bool:
    raw_value = get_windsurf_state_value("windsurfAuthStatus")
    if not isinstance(raw_value, str):
        return False

    try:
        payload = json.loads(raw_value)
    except Exception:
        return False

    api_key = payload.get("apiKey")
    return isinstance(api_key, str) and api_key.strip().startswith("devin-session-token")


def get_probe_mode() -> str:
    explicit_mode = os.environ.get("WINDSURF_PROBE_MODE")
    if explicit_mode is None or not explicit_mode.strip():
        return "direct" if has_direct_cloud_key() else "ls_emulator"

    mode = explicit_mode.strip().lower()
    if mode not in {
        "validate",
        "raw-chat",
        "chat",
        "api-wrapper",
        "assign-model",
        "cascade",
        "direct",
        "ls_emulator",
        "traffic_replay_emulator",
    }:
        raise ValueError(
            "WINDSURF_PROBE_MODE must be 'validate', 'raw-chat', 'chat', 'api-wrapper', 'assign-model', 'cascade', 'direct', 'ls_emulator', or 'traffic_replay_emulator'"
        )
    return mode


def get_runtime_session_id() -> str:
    identity = resolve_session_identity()
    if identity["provenance"] == "observed":
        return identity["value"]
    raise ValueError("observed WINDSURF_SESSION_ID is required from runtime snapshot or replay capture")


def build_ls_envelope_validation_summary(*, rpc_name: str, cascade_id: str | None = None) -> dict[str, object]:
    metadata = get_metadata_payload(resolve_auth_context_for_mode("ls_emulator")["token"])
    csrf_token = get_local_csrf_token()
    validation = {
        "rpcName": rpc_name,
        "valid": True,
        "errors": [],
        "host": get_local_host_header(rpc_name),
        "csrfPresent": bool(csrf_token),
        "metadataSessionIdPresent": isinstance(metadata.get("sessionId"), str) and bool(metadata.get("sessionId")),
        "cascadeIdPresent": bool(cascade_id),
    }
    if not csrf_token:
        validation["valid"] = False
        validation["errors"].append("csrf token missing")
    if not validation["metadataSessionIdPresent"]:
        validation["valid"] = False
        validation["errors"].append("metadata.sessionId missing")
    if rpc_name != "StartCascade" and not cascade_id:
        validation["valid"] = False
        validation["errors"].append("cascadeId missing")
    return validation


def assert_real_envelope_valid(*, rpc_name: str, cascade_id: str | None = None) -> None:
    summary = build_ls_envelope_validation_summary(rpc_name=rpc_name, cascade_id=cascade_id)
    if not summary["valid"]:
        raise ValueError(f"invalid LS envelope for {rpc_name}: {', '.join(summary['errors'])}")


def get_assign_model_variant() -> str:
    variant = os.environ.get(
        "WINDSURF_ASSIGN_MODEL_VARIANT",
        "router-cascade-prompt",
    ).strip().lower()
    if variant not in {"router-cascade-prompt", "prompt-only", "metadata-only"}:
        raise ValueError(
            "WINDSURF_ASSIGN_MODEL_VARIANT must be 'router-cascade-prompt', 'prompt-only', "
            "or 'metadata-only'"
        )
    return variant


def get_env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value in (None, ""):
        return default
    return int(value)


def get_metadata_payload(token: str) -> dict[str, object]:
    session_identity = resolve_session_identity()
    session_id = session_identity["value"]

    payload: dict[str, object] = {
        "apiKey": token,
        "ideName": os.environ.get("WINDSURF_IDE_NAME", "windsurf"),
        "ideVersion": os.environ.get("WINDSURF_IDE_VERSION", DEFAULT_IDE_VERSION),
        "extensionName": os.environ.get("WINDSURF_EXTENSION_NAME", "windsurf"),
        "extensionVersion": os.environ.get("WINDSURF_EXTENSION_VERSION", DEFAULT_EXTENSION_VERSION),
        "locale": os.environ.get("WINDSURF_LOCALE", "en"),
        "sessionId": session_id,
    }

    payload["sessionIdProvenance"] = session_identity["provenance"]

    optional_fields = {
        "os": os.environ.get("WINDSURF_OS"),
        "hardware": os.environ.get("WINDSURF_HARDWARE"),
        "requestId": os.environ.get("WINDSURF_REQUEST_ID"),
        "sourceAddress": os.environ.get("WINDSURF_SOURCE_ADDRESS"),
        "userAgent": os.environ.get("WINDSURF_USER_AGENT"),
        "url": os.environ.get("WINDSURF_METADATA_URL"),
        "extensionPath": os.environ.get("WINDSURF_EXTENSION_PATH"),
        "userId": os.environ.get("WINDSURF_USER_ID"),
        "userJwt": os.environ.get("WINDSURF_USER_JWT"),
        "forceTeamId": os.environ.get("WINDSURF_FORCE_TEAM_ID"),
        "deviceFingerprint": os.environ.get("WINDSURF_DEVICE_FINGERPRINT"),
        "triggerId": os.environ.get("WINDSURF_TRIGGER_ID"),
        "planName": os.environ.get("WINDSURF_PLAN_NAME"),
        "id": os.environ.get("WINDSURF_METADATA_ID"),
        "ideType": os.environ.get("WINDSURF_IDE_TYPE"),
        "impersonateTier": os.environ.get("WINDSURF_IMPERSONATE_TIER"),
        "teamId": os.environ.get("WINDSURF_TEAM_ID"),
        "sweVersion": os.environ.get("WINDSURF_SWE_VERSION"),
    }

    # Handle f field specially - accept as hex string to avoid null byte issues
    f_hex = os.environ.get("WINDSURF_METADATA_F")
    if f_hex:
        try:
            # Try to decode as hex first
            optional_fields["f"] = bytes.fromhex(f_hex.replace('\\x', '').replace(' ', ''))
        except (ValueError, AttributeError):
            # Fall back to treating as raw string
            optional_fields["f"] = f_hex

    for key, value in optional_fields.items():
        if value not in (None, ""):
            payload[key] = value

    disable_telemetry = os.environ.get("WINDSURF_DISABLE_TELEMETRY")
    if disable_telemetry:
        payload["disableTelemetry"] = disable_telemetry.strip().lower() in {"1", "true", "yes"}

    return payload


def build_validate_request(token: str) -> urllib.request.Request:
    payload = {"metadata": get_metadata_payload(token)}

    return urllib.request.Request(
        VALIDATE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Connect-Protocol-Version": "1",
            "Accept": "application/json",
            },
        method="POST",
    )


def encode_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint encoder only supports non-negative integers")
    out = bytearray()
    while True:
        to_write = value & 0x7F
        value >>= 7
        if value:
            out.append(to_write | 0x80)
        else:
            out.append(to_write)
            return bytes(out)


def encode_key(field_number: int, wire_type: int) -> bytes:
    return encode_varint((field_number << 3) | wire_type)


def encode_length_delimited(field_number: int, payload: bytes) -> bytes:
    return encode_key(field_number, 2) + encode_varint(len(payload)) + payload


def encode_string(field_number: int, value: str) -> bytes:
    return encode_length_delimited(field_number, value.encode("utf-8"))


def encode_bool(field_number: int, value: bool) -> bytes:
    return encode_key(field_number, 0) + encode_varint(1 if value else 0)


def encode_int64(field_number: int, value: int) -> bytes:
    return encode_key(field_number, 0) + encode_varint(value)


def encode_message(field_number: int, payload: bytes) -> bytes:
    return encode_length_delimited(field_number, payload)


def decode_varint(buffer: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        byte = buffer[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, offset
        shift += 7


def parse_proto_fields(payload: bytes) -> list[dict[str, object]]:
    fields: list[dict[str, object]] = []
    offset = 0

    while offset < len(payload):
        key, offset = decode_varint(payload, offset)
        field_number = key >> 3
        wire_type = key & 0x07

        if wire_type == 0:
            value, offset = decode_varint(payload, offset)
            fields.append({"fieldNumber": field_number, "wireType": wire_type, "value": value})
            continue

        if wire_type == 2:
            length, offset = decode_varint(payload, offset)
            value = payload[offset : offset + length]
            offset += length
            fields.append({"fieldNumber": field_number, "wireType": wire_type, "value": value})
            continue

        raise ValueError(f"unsupported wire type {wire_type}")

    return fields


def get_proto_length_delimited_values(payload: bytes, field_number: int) -> list[bytes]:
    return [
        field["value"]
        for field in parse_proto_fields(payload)
        if field["fieldNumber"] == field_number and field["wireType"] == 2
    ]


def decode_utf8_if_possible(payload: bytes) -> str | None:
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        return None


def is_probable_uuid_text(text: str) -> bool:
    try:
        uuid.UUID(text)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def deep_extract_strings(payload: bytes) -> list[str]:
    try:
        fields = parse_proto_fields(payload)
    except Exception:
        utf8 = decode_utf8_if_possible(payload)
        if isinstance(utf8, str) and utf8 and not is_binary_like_text(utf8):
            return [utf8]
        return []

    strings: list[str] = []
    for field in fields:
        if field["wireType"] != 2:
            continue
        value = field["value"]
        utf8 = decode_utf8_if_possible(value)
        if isinstance(utf8, str) and utf8 and not is_binary_like_text(utf8):
            strings.append(utf8)
        nested_strings = deep_extract_strings(value)
        for nested in nested_strings:
            if nested not in strings:
                strings.append(nested)
    return strings


def decode_assign_model_response(body: bytes) -> dict[str, object]:
    top_fields = parse_proto_fields(body)
    assignment_payloads = get_proto_length_delimited_values(body, 1)
    assignment = None

    if assignment_payloads:
        assignment_payload = assignment_payloads[0]
        assignment_fields = parse_proto_fields(assignment_payload)
        assignment = {
            "fieldNumbers": [field["fieldNumber"] for field in assignment_fields],
            "assignmentJwt": None,
            "assignedModelUid": None,
            "harnessUid": None,
            "modelRouterUid": None,
        }
        for number, name in [
            (1, "assignmentJwt"),
            (2, "assignedModelUid"),
            (3, "harnessUid"),
            (4, "modelRouterUid"),
        ]:
            values = get_proto_length_delimited_values(assignment_payload, number)
            if values:
                assignment[name] = decode_utf8_if_possible(values[0])

    return {
        "fieldNumbers": [field["fieldNumber"] for field in top_fields],
        "assignment": assignment,
    }


def decode_start_cascade_response(body: bytes) -> dict[str, object]:
    fields = parse_proto_fields(body)
    string_fields: list[dict[str, object]] = []
    for field in fields:
        if field["wireType"] == 2:
            utf8 = decode_utf8_if_possible(field["value"])
            if utf8 is not None:
                string_fields.append({
                    "fieldNumber": field["fieldNumber"],
                    "utf8": utf8,
                })
    return {
        "fieldNumbers": [field["fieldNumber"] for field in fields],
        "stringFields": string_fields,
        "cascadeId": string_fields[0]["utf8"] if string_fields and string_fields[0]["fieldNumber"] == 1 else None,
    }


def decode_send_user_cascade_message_response(body: bytes) -> dict[str, object]:
    fields = parse_proto_fields(body)
    string_fields: list[dict[str, object]] = []
    for field in fields:
        if field["wireType"] == 2:
            utf8 = decode_utf8_if_possible(field["value"])
            if utf8 is not None:
                string_fields.append({
                    "fieldNumber": field["fieldNumber"],
                    "utf8": utf8,
                })
    return {
        "fieldNumbers": [field["fieldNumber"] for field in fields],
        "stringFields": string_fields,
    }


def extract_chat_message(payload: bytes) -> dict[str, object] | None:
    try:
        fields = parse_proto_fields(payload)
    except Exception:
        return None

    role = None
    text = None
    for field in fields:
        if field["fieldNumber"] == 1 and field["wireType"] == 0:
            role = field["value"]
        elif field["fieldNumber"] == 3 and field["wireType"] == 2:
            text = decode_utf8_if_possible(field["value"])

    if role in {1, 2} and isinstance(text, str) and text:
        return {"role": role, "text": text}
    return None


def build_classified_node(
    classifier: str,
    *,
    chat: dict[str, object] | None = None,
    strings: list[str] | None = None,
    field_numbers: list[int] | None = None,
    container_field_number: int | None = None,
    model_assignment_info: dict[str, object] | None = None,
    candidate_texts: list[str] | None = None,
    raw_fields: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "classifier": classifier,
        "chat": chat,
        "strings": strings or [],
        "fieldNumbers": field_numbers or [],
        "containerFieldNumber": container_field_number,
        "modelAssignmentInfo": model_assignment_info,
        "candidateTexts": candidate_texts or [],
        "rawFields": raw_fields or [],
    }



def classify_trajectory_node(payload: bytes) -> dict[str, object]:
    direct_chat = extract_chat_message(payload)
    if direct_chat is not None:
        fields = parse_proto_fields(payload)
        classifier = "assistant_emit" if direct_chat["role"] == 2 else "user_message"
        if direct_chat["role"] == 2 and is_system_policy_text(direct_chat["text"]):
            classifier = "policy_or_system"
        elif direct_chat["role"] == 2 and is_tool_definition_text(direct_chat["text"]):
            classifier = "tool"
        return build_classified_node(
            classifier,
            chat=direct_chat,
            strings=[direct_chat["text"]],
            field_numbers=[field["fieldNumber"] for field in fields],
            raw_fields=fields,
        )

    try:
        fields = parse_proto_fields(payload)
    except Exception:
        return build_classified_node("unknown")

    for field in fields:
        if field["wireType"] != 2:
            continue

        nested_chat = extract_chat_message(field["value"])
        if nested_chat is not None:
            return build_classified_node(
                "assistant_emit" if nested_chat["role"] == 2 else "user_message",
                chat=nested_chat,
                strings=[nested_chat["text"]],
                field_numbers=[candidate["fieldNumber"] for candidate in fields],
                container_field_number=field["fieldNumber"],
                raw_fields=fields,
            )

    string_values = deep_extract_strings(payload)
    has_policy_like_text = any(is_system_policy_text(value) for value in string_values)
    has_tool_like_text = any(is_tool_definition_text(value) for value in string_values)
    has_non_uuid_text = any(not is_probable_uuid_text(value) for value in string_values)

    if has_policy_like_text:
        classifier = "policy_or_system"
    elif has_tool_like_text:
        classifier = "tool"
    elif has_non_uuid_text:
        classifier = "policy_or_system"
    else:
        classifier = "unknown"

    return build_classified_node(
        classifier,
        strings=string_values,
        field_numbers=[field["fieldNumber"] for field in fields],
        raw_fields=fields,
    )


def decode_raw_trajectory_nodes(trajectory_payload: bytes) -> list[dict[str, object]]:
    nodes: list[dict[str, object]] = []
    index = 0
    for field in parse_proto_fields(trajectory_payload):
        if field["wireType"] != 2:
            continue
        value = field["value"]
        if not isinstance(value, bytes):
            continue
        try:
            parse_proto_fields(value)
        except Exception:
            continue
        nodes.append({
            "index": index,
            "fieldNumber": field["fieldNumber"],
            "wireType": field["wireType"],
            "bytes": value,
        })
        index += 1
    return nodes



def build_cascade_step(step_index: int, classified_node: dict[str, object]) -> dict[str, object]:
    classifier = classified_node["classifier"]
    chat = classified_node.get("chat")
    strings = classified_node.get("strings") or []

    if classifier == "user_message" and isinstance(chat, dict):
        step_type = "user_message"
        inputs = {"text": chat["text"]}
        outputs = {}
    elif classifier == "assistant_emit" and isinstance(chat, dict):
        step_type = "assistant_emit"
        inputs = {}
        outputs = {"text": chat["text"]}
    elif classifier == "policy_or_system":
        step_type = "policy_or_system"
        inputs = {"strings": strings}
        outputs = {}
    else:
        step_type = "unknown"
        inputs = {}
        outputs = {}

    return {
        "stepIndex": step_index,
        "sourceNodeIndex": step_index,
        "type": step_type,
        "inputs": inputs,
        "outputs": outputs,
        "candidates": list(classified_node.get("candidateTexts") or []),
        "trajectoryState": {
            "modelAssignmentInfo": classified_node.get("modelAssignmentInfo"),
        },
        "rawSummary": {
            "classifier": classifier,
            "fieldNumbers": list(classified_node.get("fieldNumbers") or []),
            "containerFieldNumber": classified_node.get("containerFieldNumber"),
        },
    }



def build_cascade_steps(classified_nodes: list[dict[str, object]]) -> list[dict[str, object]]:
    steps: list[dict[str, object]] = []
    for index, classified_node in enumerate(classified_nodes):
        has_evidence = bool(
            classified_node.get("fieldNumbers")
            or classified_node.get("strings")
            or classified_node.get("chat")
        )
        if classified_node.get("classifier") == "unknown" and not has_evidence:
            continue
        steps.append(build_cascade_step(index, classified_node))
    return steps


def parse_trajectory_node(raw_node: dict[str, object]) -> dict[str, object]:
    payload = raw_node["bytes"]
    field_numbers: list[int] = []
    role = None
    text = None
    confidence = "low"

    try:
        fields = parse_proto_fields(payload)
    except Exception:
        return {
            "index": raw_node["index"],
            "detectedType": "unknown",
            "role": None,
            "text": None,
            "raw": True,
            "fieldNumbers": [],
            "rawPreview": payload.hex()[:120],
            "extractionConfidence": confidence,
        }

    for field in fields:
        field_numbers.append(field["fieldNumber"])
        if field["fieldNumber"] == 1 and field["wireType"] == 0:
            role = field["value"]
        elif field["fieldNumber"] == 3 and field["wireType"] == 2:
            value = field["value"]
            if isinstance(value, bytes):
                text = decode_utf8_if_possible(value)

    if role in (1, 2) and isinstance(text, str) and text:
        confidence = "high"
        detected_type = "chat_message"
        is_raw = False
    else:
        detected_type = "unknown"
        is_raw = True

    return {
        "index": raw_node["index"],
        "detectedType": detected_type,
        "role": role if role in (1, 2) else None,
        "text": text,
        "raw": is_raw,
        "fieldNumbers": field_numbers,
        "rawPreview": None if not is_raw else payload.hex()[:120],
        "extractionConfidence": confidence,
    }


def parse_trajectory_nodes(raw_nodes: list[dict[str, object]]) -> list[dict[str, object]]:
    return [parse_trajectory_node(node) for node in raw_nodes]


def is_system_policy_text(text: str) -> bool:
    markers = [
        "Use only the available tools",
        "Prefer minimal edits",
        "Planning cadence",
    ]
    return any(marker in text for marker in markers)


def is_tool_definition_text(text: str) -> bool:
    markers = [
        "kubectl",
        "powershell",
        "bash",
        "terraform",
    ]
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def is_binary_like_text(text: str | None) -> bool:
    if not isinstance(text, str) or not text:
        return True
    control_chars = sum(1 for char in text if ord(char) < 32 and char not in "\n\r\t")
    return control_chars > 0


def build_derived_assistant_summary(steps: list[dict[str, object]]) -> dict[str, object]:
    assistant_responses: list[str] = []
    for step in steps:
        if step["type"] != "assistant_emit":
            continue
        text = step["outputs"].get("text")
        if not isinstance(text, str) or not text:
            continue
        if assistant_responses and text.startswith(assistant_responses[-1]):
            assistant_responses[-1] = text
        else:
            assistant_responses.append(text)
    return {
        "assistantResponses": assistant_responses,
        "assistantFinal": assistant_responses[-1] if assistant_responses else None,
    }



def decode_cascade_trajectory_response(body: bytes) -> dict[str, object]:
    fields = parse_proto_fields(body)
    trajectory_payloads = get_proto_length_delimited_values(body, 1)
    trajectory = None

    status = next(
        (
            field["value"]
            for field in fields
            if field["fieldNumber"] == 2 and field["wireType"] == 0
        ),
        None,
    )
    num_total_steps = next(
        (
            field["value"]
            for field in fields
            if field["fieldNumber"] == 3 and field["wireType"] == 0
        ),
        None,
    )
    num_total_generator_metadata = next(
        (
            field["value"]
            for field in fields
            if field["fieldNumber"] == 4 and field["wireType"] == 0
        ),
        None,
    )

    if trajectory_payloads:
        trajectory_payload = trajectory_payloads[0]
        trajectory_fields = parse_proto_fields(trajectory_payload)
        raw_nodes = decode_raw_trajectory_nodes(trajectory_payload)
        classified_nodes = [classify_trajectory_node(node["bytes"]) for node in raw_nodes]
        steps = build_cascade_steps(classified_nodes)
        derived = build_derived_assistant_summary(steps)
        trajectory = {
            "fieldNumbers": [field["fieldNumber"] for field in trajectory_fields],
            "trajectoryId": None,
            "cascadeId": None,
            "modelAssignmentInfo": None,
            "nodesRaw": raw_nodes,
            "steps": steps,
            "derived": derived,
        }

        trajectory_id_values = get_proto_length_delimited_values(trajectory_payload, 1)
        if trajectory_id_values:
            trajectory["trajectoryId"] = decode_utf8_if_possible(trajectory_id_values[0])

        cascade_id_values = get_proto_length_delimited_values(trajectory_payload, 6)
        if cascade_id_values:
            trajectory["cascadeId"] = decode_utf8_if_possible(cascade_id_values[0])

        assignment_payloads = get_proto_length_delimited_values(trajectory_payload, 24)
        if assignment_payloads:
            assignment_payload = assignment_payloads[0]
            assignment = {
                "assignmentJwt": None,
                "assignedModelUid": None,
                "harnessUid": None,
                "modelRouterUid": None,
            }
            for number, name in [
                (1, "assignmentJwt"),
                (2, "assignedModelUid"),
                (3, "harnessUid"),
                (4, "modelRouterUid"),
            ]:
                values = get_proto_length_delimited_values(assignment_payload, number)
                if values:
                    assignment[name] = decode_utf8_if_possible(values[0])
            trajectory["modelAssignmentInfo"] = assignment

    return {
        "fieldNumbers": [field["fieldNumber"] for field in fields],
        "status": status,
        "numTotalSteps": num_total_steps,
        "numTotalGeneratorMetadata": num_total_generator_metadata,
        "trajectory": trajectory,
    }


def build_timestamp_message(epoch_seconds: int, nanos: int = 0) -> bytes:
    payload = bytearray()
    payload.extend(encode_int64(1, epoch_seconds))
    if nanos:
        payload.extend(encode_int64(2, nanos))
    return bytes(payload)


def build_metadata_message(token: str) -> bytes:
    metadata = get_metadata_payload(token)
    payload = bytearray()

    field_numbers = {
        "ideName": 1,
        "extensionVersion": 2,
        "apiKey": 3,
        "locale": 4,
        "os": 5,
        "disableTelemetry": 6,
        "ideVersion": 7,
        "hardware": 8,
        "requestId": 9,
        "sessionId": 10,
        "sourceAddress": 11,
        "extensionName": 12,
        "userAgent": 13,
        "url": 14,
        "extensionPath": 17,
        "userId": 20,
        "userJwt": 21,
        "forceTeamId": 22,
        "deviceFingerprint": 24,
        "triggerId": 25,
        "planName": 26,
        "id": 27,
        "ideType": 28,
        "impersonateTier": 29,
        "f": 30,
        "teamId": 32,
        "sweVersion": 822,
    }

    for key in [
        "ideName",
        "extensionVersion",
        "apiKey",
        "locale",
        "os",
        "ideVersion",
        "hardware",
        "sessionId",
        "sourceAddress",
        "extensionName",
        "userAgent",
        "url",
        "extensionPath",
        "userId",
        "userJwt",
        "forceTeamId",
        "deviceFingerprint",
        "triggerId",
        "planName",
        "id",
        "ideType",
        "impersonateTier",
        "f",
        "teamId",
        "sweVersion",
    ]:
        value = metadata.get(key)
        if isinstance(value, str) and value:
            payload.extend(encode_string(field_numbers[key], value))

    request_id = metadata.get("requestId")
    if request_id not in (None, ""):
        payload.extend(encode_int64(9, int(request_id)))

    if metadata.get("disableTelemetry") is True:
        payload.extend(encode_bool(6, True))

    # Handle binary f field (field 30)
    f_value = metadata.get("f")
    if f_value:
        if isinstance(f_value, str):
            f_bytes = f_value.encode('latin1')
        elif isinstance(f_value, bytes):
            f_bytes = f_value
        else:
            f_bytes = bytes(f_value)
        payload.extend(encode_length_delimited(30, f_bytes))

    return bytes(payload)


def build_chat_message_intent(text: str) -> bytes:
    generic = bytearray()
    generic.extend(encode_string(1, text))

    intent = bytearray()
    intent.extend(encode_message(1, bytes(generic)))
    return bytes(intent)


def build_chat_message(text: str, conversation_id: str, message_id: str) -> bytes:
    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 1_000_000_000)

    payload = bytearray()
    payload.extend(encode_string(1, message_id))
    payload.extend(encode_int64(2, 1))
    payload.extend(encode_message(3, build_timestamp_message(seconds, nanos)))
    payload.extend(encode_string(4, conversation_id))
    payload.extend(encode_message(5, build_chat_message_intent(text)))
    return bytes(payload)


def build_formatted_chat_message(text: str, role: int = 1) -> bytes:
    payload = bytearray()
    payload.extend(encode_int64(1, role))
    payload.extend(encode_string(3, text))
    return bytes(payload)


def build_chat_message_prompt(text: str, message_id: str, source: int = 1) -> bytes:
    payload = bytearray()
    payload.extend(encode_string(1, message_id))
    payload.extend(encode_int64(2, source))
    payload.extend(encode_string(3, text))

    prompt_phase = os.environ.get("WINDSURF_ASSIGN_MODEL_PROMPT_PHASE", "").strip()
    if prompt_phase:
        payload.extend(encode_string(19, prompt_phase))

    if get_env_flag("WINDSURF_ASSIGN_MODEL_SAFE_FOR_CODE_TELEMETRY"):
        payload.extend(encode_bool(5, True))

    return bytes(payload)


def build_cascade_conversational_planner_config() -> bytes:
    return b""


def build_cascade_planner_config(requested_model_uid: str) -> bytes:
    payload = bytearray()
    payload.extend(encode_message(1, build_cascade_conversational_planner_config()))
    payload.extend(encode_string(35, requested_model_uid))
    return bytes(payload)


def build_cascade_config(requested_model_uid: str) -> bytes:
    payload = bytearray()
    payload.extend(encode_message(1, build_cascade_planner_config(requested_model_uid)))
    return bytes(payload)


def get_last_selected_cascade_model_uids() -> list[str]:
    raw_value = os.environ.get("WINDSURF_LAST_SELECTED_CASCADE_MODEL_UIDS", "")
    return [value.strip() for value in raw_value.split(",") if value.strip()]


def get_requested_model_uid() -> str:
    override = os.environ.get("WINDSURF_CASCADE_REQUESTED_MODEL_UID")
    if override and override.strip():
        return override.strip()

    last_selected = get_last_selected_cascade_model_uids()
    if last_selected:
        return last_selected[0]

    assign_override = os.environ.get("WINDSURF_ASSIGN_MODEL_ROUTER_UID")
    if assign_override and assign_override.strip():
        return assign_override.strip()

    chat_override = os.environ.get("WINDSURF_CHAT_MODEL_NAME")
    if chat_override and chat_override.strip():
        return chat_override.strip()

    return "kimi-k2-6"


def get_chat_model_enum_value() -> int:
    value = os.environ.get("WINDSURF_CHAT_MODEL_ENUM", "57").strip()
    parsed = int(value)
    if parsed <= 0:
        raise ValueError("WINDSURF_CHAT_MODEL_ENUM must be a positive integer")
    return parsed


def build_active_document_message() -> tuple[bytes | None, dict[str, object] | None]:
    absolute_uri = os.environ.get("WINDSURF_ACTIVE_DOCUMENT_URI", "").strip()
    workspace_uri = os.environ.get("WINDSURF_ACTIVE_DOCUMENT_WORKSPACE_URI", "").strip()
    text = os.environ.get("WINDSURF_ACTIVE_DOCUMENT_TEXT")
    editor_language = os.environ.get("WINDSURF_ACTIVE_DOCUMENT_EDITOR_LANGUAGE", "").strip()

    if not any([absolute_uri, workspace_uri, text not in (None, ""), editor_language]):
        return None, None

    payload = bytearray()
    preview: dict[str, object] = {}

    if absolute_uri:
        payload.extend(encode_string(12, absolute_uri))
        preview["absoluteUri"] = absolute_uri
    if workspace_uri:
        payload.extend(encode_string(13, workspace_uri))
        preview["workspaceUri"] = workspace_uri
    if text not in (None, ""):
        payload.extend(encode_string(3, text))
        preview["text"] = text
    if editor_language:
        payload.extend(encode_string(4, editor_language))
        preview["editorLanguage"] = editor_language

    return bytes(payload), preview


def wrap_connect_envelope(message: bytes) -> bytes:
    return bytes([0]) + len(message).to_bytes(4, "big") + message


def build_raw_chat_request(token: str) -> tuple[bytes, dict[str, object]]:
    chat_text = os.environ.get("WINDSURF_CHAT_TEXT", "hello")
    chat_model_name = os.environ.get("WINDSURF_CHAT_MODEL_NAME", "kimi-k2-6")
    nonce = os.environ.get("WINDSURF_CONVERSATION_ID") or f"direct-{int(time.time() * 1000)}"
    message_id = os.environ.get("WINDSURF_MESSAGE_ID") or f"user-{nonce}"

    payload = bytearray()
    payload.extend(encode_message(1, build_metadata_message(token)))
    payload.extend(encode_message(2, build_chat_message(chat_text, nonce, message_id)))
    payload.extend(encode_string(5, chat_model_name))

    request_message = bytes(payload)
    envelope = wrap_connect_envelope(request_message)
    preview = {
        "url": get_chat_url(),
        "conversationId": nonce,
        "messageId": message_id,
        "chatModelName": chat_model_name,
        "chatText": chat_text,
        "metadata": get_metadata_payload(token),
        "protobufMessageBytes": len(request_message),
        "connectEnvelopeBytes": len(envelope),
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
        "requestType": "raw-chat",
    }
    return envelope, preview


def build_cloud_chat_request(token: str) -> tuple[bytes, dict[str, object]]:
    chat_text = os.environ.get("WINDSURF_CHAT_TEXT", "hello")
    chat_model_name = os.environ.get("WINDSURF_CHAT_MODEL_NAME", "kimi-k2-6")
    nonce = os.environ.get("WINDSURF_CONVERSATION_ID") or f"direct-{int(time.time() * 1000)}"
    message_id = os.environ.get("WINDSURF_MESSAGE_ID") or f"user-{nonce}"

    payload = bytearray()
    payload.extend(encode_message(1, build_metadata_message(token)))
    payload.extend(encode_message(3, build_formatted_chat_message(chat_text)))

    active_document_message, active_document_preview = build_active_document_message()
    if active_document_message is not None:
        payload.extend(encode_message(5, active_document_message))

    context_inclusion_type = os.environ.get("WINDSURF_CONTEXT_INCLUSION_TYPE", "").strip()
    if context_inclusion_type:
        payload.extend(encode_int64(8, int(context_inclusion_type)))

    active_selection = os.environ.get("WINDSURF_ACTIVE_SELECTION")
    if active_selection is not None:
        payload.extend(encode_string(11, active_selection))

    open_document_uris = [
        value.strip()
        for value in os.environ.get("WINDSURF_OPEN_DOCUMENT_URIS", "").split(",")
        if value.strip()
    ]
    for uri in open_document_uris:
        payload.extend(encode_string(12, uri))

    workspace_uris = [
        value.strip()
        for value in os.environ.get("WINDSURF_WORKSPACE_URIS", "").split(",")
        if value.strip()
    ]
    for uri in workspace_uris:
        payload.extend(encode_string(13, uri))

    chat_model_enum = get_chat_model_enum_value()
    payload.extend(encode_int64(9, chat_model_enum))
    payload.extend(encode_string(14, chat_model_name))

    assignment_jwt = os.environ.get("WINDSURF_ASSIGNMENT_JWT", "").strip()
    assignment_jwt_location = os.environ.get("WINDSURF_ASSIGNMENT_JWT_LOCATION", "").strip().lower()
    if assignment_jwt and assignment_jwt_location == "top-level-wrapper":
        payload.extend(encode_string(2, assignment_jwt))

    request_message = bytes(payload)
    envelope = wrap_connect_envelope(request_message)
    preview = {
        "url": get_chat_url(),
        "conversationId": nonce,
        "messageId": message_id,
        "chatModelName": chat_model_name,
        "chatModelEnum": chat_model_enum,
        "chatModelFieldNumber": 9,
        "chatModelNameFieldNumber": 14,
        "chatModelEncoding": "enum-varint",
        "bundleMappingChain": [
            "model_router_uid",
            "model_uid",
            "model_id",
            "chat_model_name",
        ],
        "chatText": chat_text,
        "assignmentJwtLocation": assignment_jwt_location or None,
        "metadata": get_metadata_payload(token),
        "activeDocument": active_document_preview,
        "contextInclusionType": context_inclusion_type or None,
        "activeSelection": active_selection,
        "openDocumentUris": open_document_uris,
        "workspaceUris": workspace_uris,
        "protobufMessageBytes": len(request_message),
        "connectEnvelopeBytes": len(envelope),
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
        "requestType": "cloud-chat",
    }
    return envelope, preview


def build_api_wrapper_request(token: str) -> tuple[bytes, dict[str, object]]:
    chat_text = os.environ.get("WINDSURF_CHAT_TEXT", "hello")
    chat_model_name = os.environ.get("WINDSURF_CHAT_MODEL_NAME", "kimi-k2-6")

    raw_request = bytearray()
    raw_request.extend(encode_message(2, build_formatted_chat_message(chat_text)))
    raw_request.extend(encode_string(5, chat_model_name))

    request_message = encode_message(1, bytes(raw_request))
    envelope = wrap_connect_envelope(request_message)
    preview = {
        "url": get_chat_url(),
        "chatModelName": chat_model_name,
        "chatText": chat_text,
        "protobufMessageBytes": len(request_message),
        "connectEnvelopeBytes": len(envelope),
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
        "requestType": "api-wrapper",
    }
    return envelope, preview


def build_assign_model_request(token: str) -> tuple[bytes, dict[str, object]]:
    chat_text = os.environ.get("WINDSURF_ASSIGN_MODEL_PROMPT_TEXT")
    if chat_text is None:
        chat_text = os.environ.get("WINDSURF_CHAT_TEXT", "hello")

    nonce = os.environ.get("WINDSURF_CONVERSATION_ID") or f"direct-{int(time.time() * 1000)}"
    message_id = os.environ.get("WINDSURF_ASSIGN_MODEL_MESSAGE_ID") or f"assign-{nonce}"
    model_router_uid = (
        os.environ.get("WINDSURF_ASSIGN_MODEL_ROUTER_UID")
        or os.environ.get("WINDSURF_ASSIGNMENT_MODEL_ROUTER_UID")
        or ""
    )
    cascade_id = os.environ.get("WINDSURF_ASSIGN_MODEL_CASCADE_ID", nonce)
    variant = get_assign_model_variant()

    field_numbers = {
        "metadata": get_env_int("WINDSURF_ASSIGN_MODEL_METADATA_FIELD", 1),
        "modelRouterUid": get_env_int("WINDSURF_ASSIGN_MODEL_ROUTER_FIELD", 2),
        "cascadeId": get_env_int("WINDSURF_ASSIGN_MODEL_CASCADE_FIELD", 3),
        "chatMessagePrompt": get_env_int("WINDSURF_ASSIGN_MODEL_PROMPT_FIELD", 4),
    }

    payload = bytearray()
    payload.extend(encode_message(field_numbers["metadata"], build_metadata_message(token)))

    if variant == "router-cascade-prompt":
        if get_env_flag("WINDSURF_ASSIGN_MODEL_INCLUDE_ROUTER_UID", True):
            payload.extend(encode_string(field_numbers["modelRouterUid"], model_router_uid))
        if get_env_flag("WINDSURF_ASSIGN_MODEL_INCLUDE_CASCADE_ID", True):
            payload.extend(encode_string(field_numbers["cascadeId"], cascade_id))

    if variant != "metadata-only":
        prompt_message = build_chat_message_prompt(chat_text, message_id)
        payload.extend(encode_message(field_numbers["chatMessagePrompt"], prompt_message))
    else:
        prompt_message = b""

    request_message = bytes(payload)

    # Create JSON-safe metadata for preview (convert bytes to hex)
    metadata_preview = get_metadata_payload(token).copy()
    if "f" in metadata_preview and isinstance(metadata_preview["f"], bytes):
        metadata_preview["f"] = metadata_preview["f"].hex()

    preview = {
        "url": get_assign_model_url(),
        "assignModelVariant": variant,
        "conversationId": nonce,
        "messageId": message_id,
        "promptText": chat_text,
        "modelRouterUid": model_router_uid,
        "cascadeId": cascade_id,
        "fieldNumbers": field_numbers,
        "metadata": metadata_preview,
        "chatMessagePromptBytes": len(prompt_message),
        "protobufMessageBytes": len(request_message),
        "httpBodyBytes": len(request_message),
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
        "requestType": "assign-model",
    }
    return request_message, preview


def build_raw_chat_probe_request(token: str) -> tuple[urllib.request.Request, dict[str, object]]:
    body, preview = build_raw_chat_request(token)
    headers = {
        "Content-Type": "application/connect+proto",
        "Connect-Protocol-Version": "1",
        "Accept": "application/json",
        "User-Agent": os.environ.get("WINDSURF_CONNECT_USER_AGENT", "connect-es/1.7.0"),
    }

    csrf_token = os.environ.get("WINDSURF_CSRF_TOKEN", "").strip()
    if csrf_token:
        headers["x-codeium-csrf-token"] = csrf_token

    return (
        urllib.request.Request(get_chat_url(), data=body, headers=headers, method="POST"),
        preview,
    )


def build_chat_probe_request(token: str) -> tuple[urllib.request.Request, dict[str, object]]:
    body, preview = build_cloud_chat_request(token)
    auth_token = os.environ.get("WINDSURF_CHAT_AUTHORIZATION_TOKEN", token).strip() or token
    headers = {
        "Content-Type": "application/connect+proto",
        "Connect-Protocol-Version": "1",
        "Accept": "application/json",
        "Authorization": f"Bearer {auth_token}",
        "User-Agent": os.environ.get("WINDSURF_CONNECT_USER_AGENT", "connect-es/1.7.0"),
    }

    csrf_token = os.environ.get("WINDSURF_CSRF_TOKEN", "").strip()
    if csrf_token:
        headers["x-codeium-csrf-token"] = csrf_token

    return (
        urllib.request.Request(get_chat_url(), data=body, headers=headers, method="POST"),
        preview,
    )


def build_api_wrapper_probe_request(token: str) -> tuple[urllib.request.Request, dict[str, object]]:
    body, preview = build_api_wrapper_request(token)
    headers = {
        "Content-Type": "application/connect+proto",
        "Connect-Protocol-Version": "1",
        "User-Agent": os.environ.get(
            "WINDSURF_CONNECT_USER_AGENT",
            "connect-go/1.17.0 (go1.23.4 X:nocoverageredesign)",
        ),
        "Accept-Encoding": "identity",
        "Connect-Accept-Encoding": "gzip",
        "host": os.environ.get("WINDSURF_CHAT_HOST_HEADER", "server.codeium.com"),
    }

    return (
        urllib.request.Request(get_chat_url(), data=body, headers=headers, method="POST"),
        preview,
    )


def build_assign_model_probe_request(token: str) -> tuple[urllib.request.Request, dict[str, object]]:
    body, preview = build_assign_model_request(token)
    headers = {
        "Content-Type": "application/proto",
        "Connect-Protocol-Version": "1",
        "Accept": "application/proto, application/json",
        "User-Agent": os.environ.get(
            "WINDSURF_CONNECT_USER_AGENT",
            "connect-go/1.17.0 (go1.23.4 X:nocoverageredesign)",
        ),
        "Accept-Encoding": "identity",
        "Connect-Accept-Encoding": "gzip",
        "host": os.environ.get("WINDSURF_CHAT_HOST_HEADER", get_default_host_header()),
    }

    return (
        urllib.request.Request(get_assign_model_url(), data=body, headers=headers, method="POST"),
        preview,
    )


def build_start_cascade_request(token: str, base_url: str | None = None) -> tuple[bytes, dict[str, object]]:
    field_numbers = {
        "metadata": 1,
        "source": 4,
    }
    source = get_env_int("WINDSURF_START_CASCADE_SOURCE", 1)

    payload = bytearray()
    payload.extend(encode_message(field_numbers["metadata"], build_metadata_message(token)))
    payload.extend(encode_int64(field_numbers["source"], source))

    request_message = bytes(payload)

    # Create JSON-safe metadata for preview (convert bytes to hex)
    metadata_preview = get_metadata_payload(token).copy()
    if "f" in metadata_preview and isinstance(metadata_preview["f"], bytes):
        metadata_preview["f"] = metadata_preview["f"].hex()

    preview = {
        "url": get_local_language_server_service_url("StartCascade", base_url),
        "source": source,
        "fieldNumbers": field_numbers,
        "metadata": metadata_preview,
        "protobufMessageBytes": len(request_message),
        "httpBodyBytes": len(request_message),
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
        "requestType": "start-cascade",
    }
    return request_message, preview


def build_start_cascade_probe_request(token: str, base_url: str | None = None) -> tuple[urllib.request.Request, dict[str, object]]:
    body, preview = build_start_cascade_request(token, base_url)
    resolved_base_url = base_url or get_local_language_server_url()
    assert_real_envelope_valid(rpc_name="StartCascade")
    headers = build_local_ls_headers(method_name="StartCascade")

    return (
        urllib.request.Request(preview["url"], data=body, headers=headers, method="POST"),
        preview,
    )


def build_send_user_cascade_message_request(
    token: str,
    cascade_id: str,
) -> tuple[bytes, dict[str, object]]:
    chat_text = os.environ.get("WINDSURF_CHAT_TEXT", "hello")
    requested_model_uid = get_requested_model_uid()
    field_numbers = {
        "metadata": 3,
        "cascadeId": 1,
        "items": 2,
        "cascadeConfig": 5,
    }

    text_item_payload = encode_string(1, chat_text)
    cascade_config_payload = build_cascade_config(requested_model_uid)

    payload = bytearray()
    payload.extend(encode_string(field_numbers["cascadeId"], cascade_id))
    payload.extend(encode_message(field_numbers["items"], text_item_payload))
    payload.extend(encode_message(field_numbers["metadata"], build_metadata_message(token)))
    payload.extend(encode_message(field_numbers["cascadeConfig"], cascade_config_payload))

    request_message = bytes(payload)

    # Create JSON-safe metadata for preview (convert bytes to hex)
    metadata_preview = get_metadata_payload(token).copy()
    if "f" in metadata_preview and isinstance(metadata_preview["f"], bytes):
        metadata_preview["f"] = metadata_preview["f"].hex()

    preview = {
        "url": get_local_language_server_service_url("SendUserCascadeMessage"),
        "cascadeId": cascade_id,
        "chatText": chat_text,
        "requestedModelUid": requested_model_uid,
        "fieldNumbers": field_numbers,
        "metadata": metadata_preview,
        "protobufMessageBytes": len(request_message),
        "httpBodyBytes": len(request_message),
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
        "requestType": "send-user-cascade-message",
    }
    return request_message, preview



def build_send_user_cascade_message_probe_request(
    token: str,
    cascade_id: str,
) -> tuple[urllib.request.Request, dict[str, object]]:
    body, preview = build_send_user_cascade_message_request(token, cascade_id)
    resolved_base_url = get_local_language_server_url()
    assert_real_envelope_valid(rpc_name="SendUserCascadeMessage", cascade_id=cascade_id)
    headers = build_local_ls_headers(method_name="SendUserCascadeMessage")

    return (
        urllib.request.Request(preview["url"], data=body, headers=headers, method="POST"),
        preview,
    )



def build_get_cascade_trajectory_request(
    token: str,
    cascade_id: str,
) -> tuple[bytes, dict[str, object]]:
    field_numbers = {
        "cascadeId": 1,
    }

    payload = bytearray()
    payload.extend(encode_string(field_numbers["cascadeId"], cascade_id))

    request_message = bytes(payload)
    preview = {
        "url": get_local_language_server_service_url("GetCascadeTrajectory"),
        "cascadeId": cascade_id,
        "fieldNumbers": field_numbers,
        "protobufMessageBytes": len(request_message),
        "httpBodyBytes": len(request_message),
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
        "requestType": "get-cascade-trajectory",
    }
    return request_message, preview



def build_get_cascade_trajectory_probe_request(
    token: str,
    cascade_id: str,
) -> tuple[urllib.request.Request, dict[str, object]]:
    body, preview = build_get_cascade_trajectory_request(token, cascade_id)
    resolved_base_url = get_local_language_server_url()
    assert_real_envelope_valid(rpc_name="GetCascadeTrajectory", cascade_id=cascade_id)
    headers = build_local_ls_headers(method_name="GetCascadeTrajectory")

    return (
        urllib.request.Request(preview["url"], data=body, headers=headers, method="POST"),
        preview,
    )



def get_cascade_poll_attempts() -> int:
    return max(1, get_env_int("WINDSURF_CASCADE_POLL_ATTEMPTS", 5))



def is_terminal_cascade_trajectory(trajectory: dict[str, object] | None) -> bool:
    if not isinstance(trajectory, dict):
        return False

    for key in ("trajectoryStatus", "completion_state"):
        value = trajectory.get(key)
        if not isinstance(value, str):
            continue
        normalized = value.strip().lower()
        if normalized in {
            "trajectory_status_complete",
            "trajectory_status_completed",
            "complete",
            "completed",
            "done",
            "finished",
        }:
            return True
    return False



def extract_cascade_final_assistant_message(result: dict[str, object]) -> str | None:
    decoded_trajectory = result.get("decodedUnaryProto")
    if not isinstance(decoded_trajectory, dict):
        return None
    trajectory = decoded_trajectory.get("trajectory")
    if not isinstance(trajectory, dict):
        return None
    derived = trajectory.get("derived")
    if not isinstance(derived, dict):
        return None
    final_response = derived.get("assistantFinal")
    return final_response.strip() if isinstance(final_response, str) and final_response.strip() else None



def run_local_cascade_flow(token: str, live_language_server_url: str) -> tuple[int, dict[str, object], dict[str, object]]:
    start_request, _start_preview = build_start_cascade_probe_request(token, live_language_server_url)
    exit_code, start_result = run_request(start_request)
    cascade_id = extract_cascade_id_from_start_result(start_result)
    if exit_code != 0 or not cascade_id:
        return exit_code, {"requestType": "start-cascade"}, start_result

    os.environ["WINDSURF_LANGUAGE_SERVER_URL"] = live_language_server_url

    send_request, _send_preview = build_send_user_cascade_message_probe_request(token, cascade_id)
    exit_code, send_result = run_request(send_request)
    if exit_code != 0:
        return exit_code, {"requestType": "send-user-cascade-message", "cascadeId": cascade_id}, send_result

    trajectory_preview: dict[str, object] = {
        "requestType": "get-cascade-trajectory",
        "cascadeId": cascade_id,
    }
    trajectory_result: dict[str, object] = {
        "error": "cascade trajectory unavailable",
        "cascadeId": cascade_id,
    }

    for _ in range(get_cascade_poll_attempts()):
        trajectory_request, trajectory_preview = build_get_cascade_trajectory_probe_request(token, cascade_id)
        exit_code, trajectory_result = run_request(trajectory_request)
        if exit_code != 0:
            return exit_code, trajectory_preview, trajectory_result
        if is_terminal_cascade_trajectory(trajectory_result.get("decodedUnaryProto", {}).get("trajectory")):
            break

    return exit_code, trajectory_preview, trajectory_result



def parse_body(raw: str):
    try:
        return json.loads(raw)
    except Exception:
        return raw


def resolve_cascade_model_selection(capture: dict[str, object]) -> dict[str, object]:
    default_override = capture.get("default_override_model_config")
    if not isinstance(default_override, dict):
        raise ValueError("capture is missing default_override_model_config")

    selected_model_uid = default_override.get("model_uid")
    if not isinstance(selected_model_uid, str) or not selected_model_uid.strip():
        raise ValueError("default_override_model_config.model_uid is missing")
    selected_model_uid = selected_model_uid.strip()

    selected_version_id = default_override.get("version_id")
    if isinstance(selected_version_id, str):
        selected_version_id = selected_version_id.strip() or None
    else:
        selected_version_id = None

    client_model_configs = capture.get("client_model_configs")
    if not isinstance(client_model_configs, list):
        raise ValueError("capture is missing client_model_configs")

    selected_config = None
    for candidate in client_model_configs:
        if not isinstance(candidate, dict):
            continue
        model_uid = candidate.get("model_uid")
        if isinstance(model_uid, str) and model_uid.strip() == selected_model_uid:
            selected_config = candidate
            break

    if not isinstance(selected_config, dict):
        raise ValueError(f"no client_model_config matched model_uid '{selected_model_uid}'")

    model_info = selected_config.get("model_info")
    if not isinstance(model_info, dict):
        raise ValueError(f"client_model_config '{selected_model_uid}' is missing model_info")

    chat_model_name = model_info.get("chat_model_name")
    if not isinstance(chat_model_name, str) or not chat_model_name.strip():
        raise ValueError(f"model_info.chat_model_name is missing for model_uid '{selected_model_uid}'")

    result: dict[str, object] = {
        "selectedModelUid": selected_model_uid,
        "selectedVersionId": selected_version_id,
        "chatModelName": chat_model_name.strip(),
        "modelInfo": model_info,
        "selectedClientModelConfig": selected_config,
    }

    inference_server_url = model_info.get("inference_server_url")
    if isinstance(inference_server_url, str) and inference_server_url.strip():
        result["inferenceServerUrl"] = inference_server_url.strip()

    base_url = model_info.get("base_url")
    if isinstance(base_url, str) and base_url.strip():
        result["baseUrl"] = base_url.strip()

    api_provider = model_info.get("api_provider")
    if api_provider not in (None, ""):
        result["apiProvider"] = api_provider

    return result


def load_capture_json(capture_path: str) -> dict[str, object]:
    with open(capture_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("capture JSON root must be an object")
    return payload


def is_cascade_capture(candidate: object) -> bool:
    return isinstance(candidate, dict) and isinstance(
        candidate.get("default_override_model_config"), dict
    ) and isinstance(candidate.get("client_model_configs"), list)



def normalize_camel_case_capture(candidate: object) -> object:
    if isinstance(candidate, list):
        return [normalize_camel_case_capture(item) for item in candidate]
    if not isinstance(candidate, dict):
        return candidate

    key_map = {
        "userStatus": "user_status",
        "cascadeModelConfigData": "cascade_model_config_data",
        "defaultOverrideModelConfig": "default_override_model_config",
        "clientModelConfigs": "client_model_configs",
        "modelUid": "model_uid",
        "versionId": "version_id",
        "modelInfo": "model_info",
        "chatModelName": "chat_model_name",
        "inferenceServerUrl": "inference_server_url",
        "baseUrl": "base_url",
        "apiProvider": "api_provider",
    }

    normalized: dict[str, object] = {}
    for key, value in candidate.items():
        normalized[key_map.get(key, key)] = normalize_camel_case_capture(value)
    return normalized



def scan_cascade_capture_candidates(payload: dict[str, object]) -> list[str]:
    candidates: set[str] = set()

    def visit(node: object, path: str) -> None:
        if isinstance(node, dict):
            if isinstance(node.get("default_override_model_config"), dict):
                candidates.add(path or ".")
            if isinstance(node.get("cascade_model_config_data"), dict):
                if path:
                    candidates.add(path)
                child_path = f"{path}.cascade_model_config_data" if path else "cascade_model_config_data"
                candidates.add(child_path)
            for key, value in node.items():
                next_path = f"{path}.{key}" if path else key
                visit(value, next_path)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                next_path = f"{path}[{index}]" if path else f"[{index}]"
                visit(value, next_path)

    visit(payload, "")
    return sorted(candidates)



def extract_cascade_capture(payload: dict[str, object]) -> dict[str, object]:
    if is_cascade_capture(payload):
        return payload

    nested = payload.get("cascade_model_config_data")
    if is_cascade_capture(nested):
        return nested

    user_status = payload.get("user_status")
    if isinstance(user_status, dict):
        nested = user_status.get("cascade_model_config_data")
        if is_cascade_capture(nested):
            return nested

    queue: list[object] = [payload]
    seen: set[int] = set()

    while queue:
        current = queue.pop(0)
        current_id = id(current)
        if current_id in seen:
            continue
        seen.add(current_id)

        if is_cascade_capture(current):
            return current

        if isinstance(current, dict):
            queue.extend(current.values())
        elif isinstance(current, list):
            queue.extend(current)

    raise ValueError("could not find cascade model config capture in payload")


def build_cascade_capture_summary(capture_path: str) -> dict[str, object]:
    payload = normalize_camel_case_capture(load_capture_json(capture_path))
    if not isinstance(payload, dict):
        raise ValueError("normalized capture JSON root must be an object")
    capture = extract_cascade_capture(payload)
    resolved = resolve_cascade_model_selection(capture)
    return {
        "capturePath": capture_path,
        **resolved,
    }


def build_bridge_artifact_validation_summary(capture_path: str) -> dict[str, object]:
    payload = normalize_camel_case_capture(load_capture_json(capture_path))
    if not isinstance(payload, dict):
        raise ValueError("normalized capture JSON root must be an object")

    candidates = scan_cascade_capture_candidates(payload)
    capture = extract_cascade_capture(payload)
    resolved = resolve_cascade_model_selection(capture)
    return {
        "capturePath": capture_path,
        "valid": True,
        "candidateCount": len(candidates),
        "candidates": candidates,
        "resolved": resolved,
    }


def build_windsurf_hook_env_payload(hook_path: str) -> dict[str, object]:
    normalized_hook_path = hook_path.replace("\\", "/")
    hook_require = f"--require={normalized_hook_path}"
    return {
        "hookPath": hook_path,
        "normalizedHookPath": normalized_hook_path,
        "nodeOptions": hook_require,
        "vscodeNodeOptions": hook_require,
        "launchArgs": ["--new-window"],
    }


def serialize_runtime_ls_binding(binding) -> dict[str, object]:
    return {
        "session_id": binding.session_id,
        "window_id": binding.window_id,
        "host": binding.host,
        "port": binding.port,
        "lifecycle_nonce": binding.lifecycle_nonce,
        "timestamp": binding.timestamp,
        "csrf_token": binding.csrf_token,
        "state": binding.state,
        "url": binding.url,
        "source": getattr(binding, "source", "PERSISTED"),
        "bindingValidated": bool(getattr(binding, "binding_validated", False)),
        "lastValidationAt": getattr(binding, "last_validation_at", None),
        "candidateBindings": list(getattr(binding, "candidate_bindings", [])),
        "bindingHistory": list(getattr(binding, "binding_history", [])),
    }


def build_ls_event_payload(raw_event: str) -> dict[str, object]:
    payload = parse_body(raw_event)
    if not isinstance(payload, dict):
        raise ValueError("LS event payload must be a JSON object")

    event_name = payload.get("event")
    if not isinstance(event_name, str) or not event_name.strip():
        raise ValueError("LS event payload must include event")
    event_name = event_name.strip()

    if event_name == "LanguageServerStarted":
        binding = on_language_server_started(
            session_id=str(payload["session_id"]),
            window_id=str(payload["window_id"]),
            host=str(payload["host"]),
            port=int(payload["port"]),
            lifecycle_nonce=str(payload["lifecycle_nonce"]),
            timestamp=float(payload["timestamp"]),
            csrf_token=(
                str(payload["csrf_token"]).strip()
                if payload.get("csrf_token") is not None and str(payload.get("csrf_token")).strip()
                else None
            ),
            confirmed=bool(payload.get("confirmed", False)),
        )
        persist_runtime_ls_binding(binding)
        return {
            "event": event_name,
            "binding": serialize_runtime_ls_binding(binding),
        }

    if event_name == "LanguageServerStopped":
        binding = on_language_server_stopped(
            session_id=str(payload["session_id"]),
            window_id=str(payload["window_id"]),
            lifecycle_nonce=str(payload["lifecycle_nonce"]),
            timestamp=float(payload["timestamp"]),
        )
        persist_runtime_ls_binding(binding)
        return {
            "event": event_name,
            "binding": serialize_runtime_ls_binding(binding),
        }

    raise ValueError(f"Unsupported LS event {event_name}")


def build_capture_cli_payload(args: list[str]) -> dict[str, object] | None:
    if len(args) == 1 and args[0] == "--run-abc-experiment":
        return run_instrumentation_abc_experiment()

    if len(args) == 1 and args[0] == "--passive-observer-once":
        graph = derive_active_graph_snapshot()
        runtime_inputs = {
            "ls_port": None,
            "extension_port": None,
            "ls_alive": False,
            "transport_reachable": False,
            "node_service_alive": False,
            "extension_host_alive": False,
        }
        runtime_path = get_runtime_liveness_status_path()
        if runtime_path is not None:
            runtime_inputs = read_runtime_liveness_graph_inputs(runtime_path)
        graph_with_runtime = {**graph, **runtime_inputs}
        passive_semantics = build_passive_semantics_snapshot(str(graph.get("graph_id") or "G_n"))
        return build_passive_observer_snapshot(
            graph=graph_with_runtime,
            runtime_inputs=runtime_inputs,
            passive_semantics=passive_semantics,
        )

    if len(args) > 0 and args[0] == "--audit-local-auth":
        ports = [int(arg) for arg in args[1:]] if len(args) > 1 else [59568]
        csrf_token = get_local_csrf_token()
        if not csrf_token:
            csrf_token = os.environ.get("WINDSURF_CSRF_TOKEN", "").strip()
        session_id = os.environ.get("WINDSURF_SESSION_ID", "").strip() or "observed-session-abc"
        return run_local_rpc_auth_audit(ports=ports, csrf_token=csrf_token, session_id=session_id)

    if len(args) > 0 and args[0] == "--map-port-surfaces":
        ports = [int(arg) for arg in args[1:]] if len(args) > 1 else [65049, 65053]
        csrf_token = get_local_csrf_token()
        if not csrf_token:
            csrf_token = os.environ.get("WINDSURF_CSRF_TOKEN", "").strip()
        session_id = os.environ.get("WINDSURF_SESSION_ID", "").strip() or "observed-session-abc"
        return run_port_surface_mapping(ports=ports, csrf_token=csrf_token, session_id=session_id)

    if len(args) > 1 and args[0] == "--scan" and args[1].lower().endswith(".json"):
        payload = load_capture_json(args[1])
        return {
            "capturePath": args[1],
            "candidates": scan_cascade_capture_candidates(payload),
        }

    if len(args) > 1 and args[0] == "--validate-bridge" and args[1].lower().endswith(".json"):
        return build_bridge_artifact_validation_summary(args[1])

    if len(args) > 1 and args[0] == "--windsurf-hook-env":
        return build_windsurf_hook_env_payload(args[1])

    if len(args) > 1 and args[0] == "--ls-event":
        return build_ls_event_payload(args[1])

    if len(args) > 0 and args[0].lower().endswith(".json"):
        return build_cascade_capture_summary(args[0])

    return None



def serialize_output(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=True)


def emit_output(payload: dict[str, object]) -> None:
    sys.stdout.write(serialize_output(payload))
    sys.stdout.write("\n")


def extract_final_model_response(result: dict[str, object]) -> str | None:
    body = result.get("body")
    if isinstance(body, str) and body.strip() and not body.strip().startswith("{"):
        return body.strip()

    if isinstance(body, dict):
        for key in ["output_text", "response", "text", "message"]:
            value = body.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        choices = body.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                if not isinstance(choice, dict):
                    continue
                message = choice.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
                content = choice.get("text")
                if isinstance(content, str) and content.strip():
                    return content.strip()
                delta = choice.get("delta")
                if isinstance(delta, dict):
                    content = delta.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()

        data = body.get("data")
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                content = item.get("text") or item.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()

    connect_decoded = result.get("connectDecoded")
    if isinstance(connect_decoded, dict):
        frames = connect_decoded.get("frames")
        if isinstance(frames, list):
            for frame in reversed(frames):
                if not isinstance(frame, dict):
                    continue
                payload = frame.get("payload")
                if isinstance(payload, dict):
                    for key in ["output_text", "response", "text", "content"]:
                        value = payload.get(key)
                        if isinstance(value, str) and value.strip():
                            return value.strip()
                    message = payload.get("message")
                    if isinstance(message, dict):
                        content = message.get("content")
                        if isinstance(content, str) and content.strip():
                            return content.strip()
                    choices = payload.get("choices")
                    if isinstance(choices, list):
                        for choice in choices:
                            if not isinstance(choice, dict):
                                continue
                            message = choice.get("message")
                            if isinstance(message, dict):
                                content = message.get("content")
                                if isinstance(content, str) and content.strip():
                                    return content.strip()
                            content = choice.get("text")
                            if isinstance(content, str) and content.strip():
                                return content.strip()
                    content = payload.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
                elif isinstance(payload, str) and payload.strip() and not payload.strip().startswith("{"):
                    return payload.strip()

    body_hex = result.get("bodyHex")
    content_type = result.get("contentType")
    if isinstance(content_type, str) and content_type.startswith("application/proto") and isinstance(body_hex, str):
        try:
            decoded_connect = decode_connect_response(bytes.fromhex(body_hex))
        except Exception:
            decoded_connect = None
        if isinstance(decoded_connect, dict):
            frames = decoded_connect.get("frames")
            if isinstance(frames, list):
                for frame in reversed(frames):
                    if not isinstance(frame, dict):
                        continue
                    payload = frame.get("payload")
                    if isinstance(payload, dict):
                        for key in ["output_text", "response", "text", "content"]:
                            value = payload.get(key)
                            if isinstance(value, str) and value.strip() and "invalid api key" not in value.lower():
                                return value.strip()
                    elif isinstance(payload, str) and payload.strip() and "invalid api key" not in payload.lower():
                        return payload.strip()

    return None


def emit_final_response_only(mode: str, request_preview: dict[str, object], result: dict[str, object]) -> None:
    final_response = extract_final_model_response(result)
    if mode == "cascade":
        cascade_final = extract_cascade_final_assistant_message(result)
        if cascade_final is not None:
            final_response = cascade_final
    emit_output(
        {
            "mode": mode,
            "requestType": request_preview.get("requestType"),
            "status": result.get("status"),
            "finalResponse": final_response,
        }
    )


def maybe_decompress_connect_payload(payload: bytes, compressed: bool) -> tuple[bytes, str | None]:
    if not compressed:
        return payload, None

    try:
        return gzip.decompress(payload), "gzip"
    except Exception:
        return payload, None


def decode_connect_response(body: bytes) -> dict[str, object]:
    frames: list[dict[str, object]] = []
    offset = 0

    while offset + 5 <= len(body):
        flags = body[offset]
        length = int.from_bytes(body[offset + 1 : offset + 5], "big")
        offset += 5

        if offset + length > len(body):
            frames.append(
                {
                    "kind": "truncated",
                    "flags": flags,
                    "expectedLength": length,
                    "remainingBytes": len(body) - offset,
                }
            )
            break

        payload = body[offset : offset + length]
        offset += length
        compressed = bool(flags & 0x01)
        end_stream = bool(flags & 0x02)
        decoded_payload, compression_encoding = maybe_decompress_connect_payload(payload, compressed)

        if end_stream:
            text = decoded_payload.decode("utf-8", errors="replace")
            parsed = parse_body(text)
            frame: dict[str, object] = {
                "kind": "end_stream",
                "flags": flags,
                "compressed": compressed,
                "payload": parsed,
            }
            if compression_encoding:
                frame["compressionEncoding"] = compression_encoding
                frame["compressedBytes"] = len(payload)
                frame["decompressedBytes"] = len(decoded_payload)
            if isinstance(parsed, dict):
                if isinstance(parsed.get("metadata"), dict):
                    frame["metadata"] = parsed["metadata"]
                if isinstance(parsed.get("error"), dict):
                    frame["error"] = parsed["error"]
            frames.append(frame)
            continue

        frame: dict[str, object] = {
            "kind": "message",
            "flags": flags,
            "compressed": compressed,
            "payloadBase64": decoded_payload.hex(),
            "payloadBytes": len(decoded_payload),
        }
        if compression_encoding:
            frame["compressionEncoding"] = compression_encoding
            frame["compressedBytes"] = len(payload)
            frame["decompressedBytes"] = len(decoded_payload)
        frames.append(frame)

    result: dict[str, object] = {
        "frames": frames,
        "trailingBytes": len(body) - offset,
    }
    if frames:
        result["hasEndStream"] = any(frame.get("kind") == "end_stream" for frame in frames)
        result["messageFrameCount"] = sum(1 for frame in frames if frame.get("kind") == "message")
    return result


def maybe_decode_connect_body(content_type: str | None, body: bytes) -> dict[str, object] | None:
    if content_type and content_type.startswith("application/connect+proto"):
        return decode_connect_response(body)
    return None


def maybe_decode_unary_proto_body(content_type: str | None, body: bytes) -> dict[str, object] | None:
    if content_type and content_type.startswith("application/proto"):
        result = {
            "bodyBytes": len(body),
            "bodyHex": body.hex(),
            "bodyText": body.decode("utf-8", errors="replace"),
        }
        return result
    return None


CASCADE_ID_REGEX = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


def extract_model_router_uid_from_trajectory_body(body_bytes: bytes) -> str | None:
    """
    Extract modelRouterUid from GetCascadeTrajectory response body.

    The trajectory response contains a protobuf structure where modelRouterUid
    appears as a UUID string (field 12) before the assignedModelUid field.

    Strategy: 
    1. Try full protobuf parser first (if available)
    2. Fall back to regex-based extraction if parser unavailable or fails
    """
    if not body_bytes:
        return None

    # Try full protobuf parser first
    if pb_extract_model_router_uid is not None:
        try:
            uid = pb_extract_model_router_uid(body_bytes)
            if uid:
                return uid
        except Exception as e:
            print(f"Warning: Protobuf parser failed, falling back to regex: {e}")

    # Fallback: regex-based extraction
    # Find all UUID patterns in the response
    uuid_pattern = rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    uuid_matches = list(re.finditer(uuid_pattern, body_bytes))

    if not uuid_matches:
        return None

    # Look for model identifier patterns (e.g., "kimi-k2-6", "claude-", "gpt-")
    model_patterns = [
        rb'kimi-[a-z0-9-]+',
        rb'claude-[a-z0-9-]+',
        rb'gpt-[a-z0-9-]+',
        rb'gemini-[a-z0-9-]+',
    ]

    model_match = None
    for pattern in model_patterns:
        match = re.search(pattern, body_bytes)
        if match:
            model_match = match
            break

    if not model_match:
        # No model identifier found, return first UUID
        return uuid_matches[0].group(0).decode('utf-8')

    # Find the UUID that appears closest before the model identifier
    model_offset = model_match.start()
    candidate_uuids = [m for m in uuid_matches if m.start() < model_offset]

    if not candidate_uuids:
        # No UUID before model identifier, return first UUID
        return uuid_matches[0].group(0).decode('utf-8')

    # Return the UUID closest to (but before) the model identifier
    closest_uuid = max(candidate_uuids, key=lambda m: m.start())
    return closest_uuid.group(0).decode('utf-8')



def extract_cascade_id_details_from_start_result(start_result: dict[str, object]) -> dict[str, str | None]:
    decoded_start = start_result.get("decodedUnaryProto")
    if isinstance(decoded_start, dict):
        cascade_id = decoded_start.get("cascadeId")
        if isinstance(cascade_id, str) and cascade_id:
            return {
                "cascadeId": cascade_id,
                "cascadeIdSource": "protobuf",
            }

        string_fields = decoded_start.get("stringFields")
        if isinstance(string_fields, list):
            for field in string_fields:
                if not isinstance(field, dict):
                    continue
                field_number = field.get("fieldNumber")
                utf8_value = field.get("utf8")
                if field_number == 1 and isinstance(utf8_value, str) and utf8_value:
                    return {
                        "cascadeId": utf8_value,
                        "cascadeIdSource": "protobuf",
                    }

    body_text = start_result.get("bodyText")
    if isinstance(body_text, str) and body_text:
        match = CASCADE_ID_REGEX.search(body_text)
        if match is not None:
            return {
                "cascadeId": match.group(0),
                "cascadeIdSource": "bodyText-regex",
            }

    return {
        "cascadeId": None,
        "cascadeIdSource": None,
    }


def extract_cascade_id_from_start_result(start_result: dict[str, object]) -> str | None:
    return extract_cascade_id_details_from_start_result(start_result)["cascadeId"]


def parse_trajectory_with_full_parser(body_bytes: bytes) -> dict[str, object] | None:
    """
    Parse GetCascadeTrajectory response using the full protobuf parser.
    
    Returns a detailed parse result with all extracted fields, or None if parser unavailable.
    """
    if parse_trajectory_response is None:
        return None
    
    try:
        result = parse_trajectory_response(body_bytes)
        return result
    except Exception as e:
        print(f"Warning: Full protobuf parser failed: {e}")
        return None


def build_cascade_assignment_correlation_summary(
    start_result: dict[str, object],
    send_result: dict[str, object],
    trajectory_result: dict[str, object] | None = None,
) -> dict[str, object]:
    decoded_send = send_result.get("decodedUnaryProto")
    model_assignment_info = (
        decoded_send.get("modelAssignmentInfo") if isinstance(decoded_send, dict) else None
    )
    if not isinstance(model_assignment_info, dict):
        model_assignment_info = {}

    if isinstance(trajectory_result, dict):
        decoded_trajectory = trajectory_result.get("decodedUnaryProto")
        trajectory = decoded_trajectory.get("trajectory") if isinstance(decoded_trajectory, dict) else None
        trajectory_assignment = trajectory.get("modelAssignmentInfo") if isinstance(trajectory, dict) else None
        if isinstance(trajectory_assignment, dict):
            model_assignment_info = trajectory_assignment

        # If modelRouterUid not found in parsed structure, try extracting from raw body
        if not model_assignment_info.get("modelRouterUid"):
            body_hex = trajectory_result.get("bodyHex")
            if isinstance(body_hex, str) and body_hex:
                try:
                    body_bytes = bytes.fromhex(body_hex)
                    extracted_uid = extract_model_router_uid_from_trajectory_body(body_bytes)
                    if extracted_uid:
                        model_assignment_info = dict(model_assignment_info)
                        model_assignment_info["modelRouterUid"] = extracted_uid
                except (ValueError, AttributeError):
                    pass

    return {
        "cascadeId": extract_cascade_id_from_start_result(start_result),
        "assignmentJwt": model_assignment_info.get("assignmentJwt"),
        "assignedModelUid": model_assignment_info.get("assignedModelUid"),
        "harnessUid": model_assignment_info.get("harnessUid"),
        "modelRouterUid": model_assignment_info.get("modelRouterUid"),
    }


def build_active_graph_correlation_summary(graph: dict[str, object]) -> dict[str, object]:
    renderer_state = graph.get("renderer_state") if isinstance(graph.get("renderer_state"), dict) else {}
    t0 = renderer_state.get("t0_renderer_start") if isinstance(renderer_state.get("t0_renderer_start"), dict) else {}
    t1 = renderer_state.get("t1_webcontents_proxy_active") if isinstance(renderer_state.get("t1_webcontents_proxy_active"), dict) else {}
    t2 = renderer_state.get("t2_ipc_bridge_live") if isinstance(renderer_state.get("t2_ipc_bridge_live"), dict) else {}
    t3 = renderer_state.get("t3_network_active") if isinstance(renderer_state.get("t3_network_active"), dict) else {}

    renderer_stage = "unknown"
    if t0.get("observed"):
        renderer_stage = "t0"
    if t1.get("observed"):
        renderer_stage = "t1"
    if t2.get("observed"):
        renderer_stage = "t2"
    if t3.get("observed"):
        renderer_stage = "t3"

    ipc_state = "absent"
    if t2.get("observed"):
        ipc_state = "present"
    if t2.get("observed") and t3.get("observed"):
        ipc_state = "active"

    has_extension_port = isinstance(graph.get("extension_port"), int) and graph.get("extension_port") > 0
    has_ls_port = isinstance(graph.get("ls_port"), int) and graph.get("ls_port") > 0
    ls_alive = bool(graph.get("ls_alive"))
    transport_reachable = bool(graph.get("transport_reachable"))
    reset_detected = bool(graph.get("reset_detected"))

    extension_server_state = "unknown"
    if has_extension_port and ipc_state in {"present", "active"}:
        extension_server_state = "validating"
    if has_extension_port and ipc_state == "active" and ls_alive:
        extension_server_state = "active"

    ls_state = "started" if ls_alive else "orphaned"
    if has_ls_port and not transport_reachable:
        ls_state = "connected" if ipc_state in {"present", "active"} and ls_alive else ls_state
    if has_ls_port and transport_reachable and ipc_state == "active" and ls_alive:
        ls_state = "active"

    classification = "ls_orphan"
    if reset_detected:
        classification = "extensionserver_control_plane"
    elif ls_state == "active" and extension_server_state == "active":
        classification = "ls_backend"
    elif extension_server_state in {"validating", "active"}:
        classification = "extensionserver_control_plane"

    confidence = "low"
    if ipc_state == "active" and has_extension_port:
        confidence = "medium"
    if classification == "ls_orphan" and not has_extension_port:
        confidence = "medium"

    final_conclusion = (
        "Graph-local evidence shows renderer, IPC, extension server, and LS alignment in the active graph."
        if classification == "ls_backend"
        else "Graph-local evidence stops before confirmed LS backend consumption in the active graph."
    )

    return {
        "graph_id": graph.get("graph_id") or "G_n",
        "renderer_state": renderer_stage,
        "ipc_state": ipc_state,
        "ls_state": ls_state,
        "extension_server_state": extension_server_state,
        "causal_chain": [
            "renderer → ipc",
            "ipc → extension server",
            "extension server → ls",
        ],
        "classification": classification,
        "reset_detected": reset_detected,
        "final_conclusion": final_conclusion,
        "confidence": confidence,
    }


def read_runtime_liveness_graph_inputs(path: pathlib.Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "ls_port": None,
            "extension_port": None,
            "ls_alive": False,
            "transport_reachable": False,
            "node_service_alive": False,
            "extension_host_alive": False,
        }

    selected_ports = payload.get("selected_ports") if isinstance(payload.get("selected_ports"), dict) else {}
    selected_pid_tuple = payload.get("selected_pid_tuple") if isinstance(payload.get("selected_pid_tuple"), dict) else {}

    node_service_pids = selected_pid_tuple.get("node_service_pids") if isinstance(selected_pid_tuple.get("node_service_pids"), list) else []
    extension_host_pids = selected_pid_tuple.get("extension_host_pids") if isinstance(selected_pid_tuple.get("extension_host_pids"), list) else []

    return {
        "ls_port": selected_ports.get("ls_port"),
        "extension_port": selected_ports.get("extension_server_port"),
        "ls_alive": bool(payload.get("ls_reachable")),
        "transport_reachable": bool(payload.get("ls_reachable")),
        "node_service_alive": len(node_service_pids) > 0,
        "extension_host_alive": len(extension_host_pids) > 0,
    }


def normalize_passive_semantic_observation(
    *,
    current_graph_id: str,
    field_name: str,
    candidates: list[dict[str, object]] | None,
) -> dict[str, object]:
    del field_name
    normalized_candidates = [candidate for candidate in (candidates or []) if isinstance(candidate, dict)]
    if not normalized_candidates:
        return {
            "value": None,
            "state": "not-observed",
            "provenance": None,
            "graphId": None,
        }

    current_graph_candidates = [
        candidate for candidate in normalized_candidates if candidate.get("graphId") == current_graph_id
    ]
    preferred = current_graph_candidates[-1] if current_graph_candidates else normalized_candidates[-1]
    state = "observed-current-graph" if preferred.get("graphId") == current_graph_id else "observed-historical"

    return {
        **preferred,
        "state": state,
    }


def build_passive_semantics_snapshot(current_graph_id: str) -> dict[str, object]:
    return {
        "sessionId": normalize_passive_semantic_observation(
            current_graph_id=current_graph_id,
            field_name="sessionId",
            candidates=[],
        ),
        "traceCount": {
            "value": None,
            "state": "not-observed",
            "provenance": None,
            "graphId": None,
            "deltaState": None,
        },
        "cascadeObserved": {
            "value": False,
            "state": "not-observed",
            "provenance": None,
            "graphId": None,
        },
    }


def build_passive_observer_snapshot(
    *,
    graph: dict[str, object],
    runtime_inputs: dict[str, object],
    passive_semantics: dict[str, object],
) -> dict[str, object]:
    current_graph_id = str(graph.get("graph_id") or "G_n")
    graph_summary = build_active_graph_correlation_summary({**graph, **runtime_inputs})

    session_observation = passive_semantics.get("sessionId") if isinstance(passive_semantics.get("sessionId"), dict) else {
        "value": None,
        "state": "not-observed",
        "provenance": None,
        "graphId": None,
    }
    trace_count_observation = passive_semantics.get("traceCount") if isinstance(passive_semantics.get("traceCount"), dict) else {
        "value": None,
        "state": "not-observed",
        "provenance": None,
        "graphId": None,
    }
    cascade_observation = passive_semantics.get("cascadeObserved") if isinstance(passive_semantics.get("cascadeObserved"), dict) else {
        "value": False,
        "state": "not-observed",
        "provenance": None,
        "graphId": None,
    }

    runtime_alive = bool(runtime_inputs.get("ls_alive") or runtime_inputs.get("node_service_alive") or runtime_inputs.get("extension_host_alive"))

    if session_observation.get("state") == "observed-current-graph":
        session_id_present: bool | str = True
    elif session_observation.get("state") == "observed-historical":
        session_id_present = "historical-only"
    else:
        session_id_present = False

    trace_delta_state = trace_count_observation.get("deltaState") if isinstance(trace_count_observation.get("deltaState"), str) else None
    if trace_count_observation.get("state") != "observed-current-graph":
        trace_count_increasing: bool | str = "unknown"
    elif trace_delta_state == "increasing":
        trace_count_increasing = True
    elif trace_delta_state in {"unchanged", "decreasing"}:
        trace_count_increasing = False
    else:
        trace_count_increasing = "unknown"

    cascade_observed = bool(cascade_observation.get("value")) if cascade_observation.get("state") == "observed-current-graph" else False

    final_conclusion = graph_summary["final_conclusion"]
    if session_observation.get("state") == "observed-historical":
        final_conclusion += " Historical session evidence exists, but no live sessionId was observed in the active graph."

    return {
        "graphId": current_graph_id,
        "answers": {
            "runtimeAlive": runtime_alive,
            "cascadeObserved": cascade_observed,
            "sessionIdPresent": session_id_present,
            "traceCountIncreasing": trace_count_increasing,
        },
        "graphSummary": graph_summary,
        "sessionId": session_observation,
        "traceCount": trace_count_observation,
        "cascadeObserved": cascade_observation,
        "finalConclusion": final_conclusion,
    }


def get_runtime_liveness_status_path() -> pathlib.Path | None:
    configured = os.environ.get("WINDSURF_RUNTIME_LIVENESS_STATUS_PATH", "").strip()
    if not configured:
        return None
    return pathlib.Path(configured)


def sha256_16(value: str | None) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def build_routing_fingerprint(assigned_model_uid: str | None, harness_uid: str | None) -> str:
    return f"{assigned_model_uid or ''}|{harness_uid or ''}"


def build_run_observation(
    *,
    run_id: str,
    prompt_text: str,
    cascade_id: str | None,
    metadata: dict[str, object],
    assignment: dict[str, object] | None,
) -> dict[str, object]:
    assignment = assignment if isinstance(assignment, dict) else {}
    assignment_jwt = assignment.get("assignmentJwt")
    return {
        "run": run_id,
        "sessionProvenance": metadata.get("sessionIdProvenance"),
        "cascadeId": cascade_id,
        "assignedModelUid": assignment.get("assignedModelUid"),
        "harnessUid": assignment.get("harnessUid"),
        "jwtHash16": sha256_16(assignment_jwt),
    }


def run_assignment_followup_variants(token: str, assignment: dict[str, object] | None) -> list[dict[str, object]]:
    if not isinstance(assignment, dict):
        return []

    assignment_jwt = assignment.get("assignmentJwt")
    assigned_model_uid = assignment.get("assignedModelUid")
    harness_uid = assignment.get("harnessUid")
    model_router_uid = assignment.get("modelRouterUid")

    if not isinstance(assignment_jwt, str) or not assignment_jwt:
        return []

    variants = [
        {
            "name": "metadata.userJwt",
            "env": {
                "WINDSURF_USER_JWT": assignment_jwt,
                "WINDSURF_ASSIGNMENT_JWT": "",
                "WINDSURF_ASSIGNMENT_JWT_LOCATION": "",
            },
        },
        {
            "name": "top-level-wrapper",
            "env": {
                "WINDSURF_ASSIGNMENT_JWT": assignment_jwt,
                "WINDSURF_ASSIGNMENT_JWT_LOCATION": "top-level-wrapper",
                "WINDSURF_USER_JWT": "",
            },
        },
    ]

    saved = {
        key: os.environ.get(key)
        for key in [
            "WINDSURF_USER_JWT",
            "WINDSURF_ASSIGNMENT_JWT",
            "WINDSURF_ASSIGNMENT_JWT_LOCATION",
            "WINDSURF_CHAT_MODEL_NAME",
            "WINDSURF_ASSIGNMENT_HARNESS_UID",
            "WINDSURF_ASSIGNMENT_MODEL_ROUTER_UID",
        ]
    }

    if isinstance(assigned_model_uid, str) and assigned_model_uid:
        saved["WINDSURF_CHAT_MODEL_NAME"] = os.environ.get("WINDSURF_CHAT_MODEL_NAME")

    results: list[dict[str, object]] = []
    try:
        if isinstance(assigned_model_uid, str) and assigned_model_uid:
            os.environ["WINDSURF_CHAT_MODEL_NAME"] = assigned_model_uid
        if isinstance(harness_uid, str) and harness_uid:
            os.environ["WINDSURF_ASSIGNMENT_HARNESS_UID"] = harness_uid
        if isinstance(model_router_uid, str) and model_router_uid:
            os.environ["WINDSURF_ASSIGNMENT_MODEL_ROUTER_UID"] = model_router_uid

        for variant in variants:
            for key, value in variant["env"].items():
                if value:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)
            request, preview = build_chat_probe_request(token)
            exit_code, result = run_request(request)
            results.append({
                "variant": variant["name"],
                "exitCode": exit_code,
                "requestPreview": preview,
                **result,
            })
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    return results


def normalize_response_headers(headers) -> dict[str, str]:
    normalized: dict[str, str] = {}
    if headers is None:
        return normalized
    for key, value in headers.items():
        if isinstance(key, str) and isinstance(value, str):
            normalized[key.lower()] = value
    return normalized


def extract_instance_hints(response_headers: dict[str, str]) -> dict[str, str | None]:
    return {
        "x-request-id": response_headers.get("x-request-id"),
        "trace-id": response_headers.get("trace-id") or response_headers.get("x-trace-id"),
        "server-timing": response_headers.get("server-timing"),
        "alt-svc": response_headers.get("alt-svc"),
        "server": response_headers.get("server"),
    }


def run_request(request: urllib.request.Request, timeout: int = 120) -> tuple[int, dict[str, object]]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            content_type = response.headers.get("content-type")
            response_headers = normalize_response_headers(response.headers)
            decoded_connect = maybe_decode_connect_body(content_type, body)
            decoded_unary_proto = maybe_decode_unary_proto_body(content_type, body)
            result = {
                "status": response.status,
                "contentType": content_type,
                "body": body.decode("utf-8", errors="replace"),
                "responseObservability": {
                    "responseHeaders": response_headers,
                    "instanceHints": extract_instance_hints(response_headers),
                },
            }
            if decoded_connect is not None:
                result["connectDecoded"] = decoded_connect
            elif decoded_unary_proto is not None:
                result.update(decoded_unary_proto)
            else:
                result["body"] = parse_body(result["body"])
            return 0, result
    except urllib.error.HTTPError as error:
        body = error.read()
        content_type = error.headers.get("content-type")
        response_headers = normalize_response_headers(error.headers)
        decoded_connect = maybe_decode_connect_body(content_type, body)
        decoded_unary_proto = maybe_decode_unary_proto_body(content_type, body)
        result = {
            "status": error.code,
            "reason": error.reason,
            "contentType": content_type,
            "body": body.decode("utf-8", errors="replace"),
            "responseObservability": {
                "responseHeaders": response_headers,
                "instanceHints": extract_instance_hints(response_headers),
            },
        }
        if decoded_connect is not None:
            result["connectDecoded"] = decoded_connect
        elif decoded_unary_proto is not None:
            result.update(decoded_unary_proto)
        else:
            result["body"] = parse_body(result["body"])
        return 1, result
    except Exception as error:
        return 1, {
            "error": error.__class__.__name__,
            "message": str(error),
        }


def build_structured_rpc_log(rpc_name: str, request: urllib.request.Request, result: dict[str, object], request_preview: dict[str, object]) -> dict[str, object]:
    host_header = None
    for key, value in request.header_items():
        if key.lower() == "host":
            host_header = value
            break

    protobuf_fields_detected = []
    decoded_unary = result.get("decodedUnaryProto")
    if isinstance(decoded_unary, dict):
        protobuf_fields_detected = decoded_unary.get("fieldNumbers", []) or []
    connect_decoded = result.get("connectDecoded")
    if isinstance(connect_decoded, dict) and not protobuf_fields_detected:
        frames = connect_decoded.get("frames", [])
        for frame in frames:
            if isinstance(frame, dict) and frame.get("kind") == "message":
                protobuf_fields_detected.append("connect_message")

    response_observability = result.get("responseObservability")
    instance_hints = {}
    if isinstance(response_observability, dict):
        maybe_hints = response_observability.get("instanceHints")
        if isinstance(maybe_hints, dict):
            instance_hints = dict(maybe_hints)

    cascade_id_details = extract_cascade_id_details_from_start_result(result) if rpc_name == "StartCascade" else {
        "cascadeId": request_preview.get("cascadeId"),
        "cascadeIdSource": None,
    }
    raw_body_preview = result.get("bodyText")
    if isinstance(raw_body_preview, str):
        raw_body_preview = raw_body_preview[:200]
    else:
        raw_body_preview = None

    return {
        "rpc_name": rpc_name,
        "url": request.full_url,
        "host": host_header,
        "status": result.get("status"),
        "cascadeId": request_preview.get("cascadeId"),
        "sessionId": request_preview.get("metadata", {}).get("sessionId"),
        "payload_size": len(request.data or b""),
        "protobuf_fields_detected": protobuf_fields_detected,
        "instanceHints": instance_hints,
        "rawBodyPreview": raw_body_preview,
        "extractedCascadeId": cascade_id_details.get("cascadeId"),
        "cascadeIdSource": cascade_id_details.get("cascadeIdSource"),
    }


def capture_forensic_rpc_exchange(
    rpc_name: str,
    request: urllib.request.Request,
    result: dict[str, object],
) -> dict[str, object]:
    headers = {key: value for key, value in request.header_items()}
    body_bytes = request.data or b""
    body_text = body_bytes.decode("utf-8", errors="replace") if isinstance(body_bytes, (bytes, bytearray)) else None
    return {
        "rpc": rpc_name,
        "url": request.full_url,
        "method": request.get_method(),
        "headers": headers,
        "body": body_text,
        "response_status": result.get("status"),
        "response_body": result.get("bodyText") or result.get("body") or result.get("message"),
    }


def classify_401_root_cause(forensic_exchange: dict[str, object]) -> dict[str, object]:
    headers = forensic_exchange.get("headers", {}) if isinstance(forensic_exchange, dict) else {}
    body = forensic_exchange.get("body") if isinstance(forensic_exchange, dict) else None
    response_status = forensic_exchange.get("response_status") if isinstance(forensic_exchange, dict) else None
    evidence = []

    csrf = headers.get("x-codeium-csrf-token") or headers.get("X-Codeium-Csrf-Token")
    if not csrf:
        csrf = next(
            (
                value
                for key, value in headers.items()
                if isinstance(key, str) and key.lower() == "x-codeium-csrf-token"
            ),
            None,
        )
    if not isinstance(csrf, str) or not csrf.strip():
        evidence.append("csrf header missing")
        return {
            "status": "FAIL",
            "failure_layer": "csrf",
            "root_cause": "missing csrf header",
            "evidence": evidence,
        }

    if not isinstance(body, str) or "devin-session-token" not in body:
        evidence.append("session token missing from protobuf metadata body")
        return {
            "status": "FAIL",
            "failure_layer": "session",
            "root_cause": "metadata apiKey/session token missing from request body",
            "evidence": evidence,
        }

    if response_status == 401:
        evidence.append("csrf present")
        evidence.append("session token present in body")
        evidence.append("401 persists despite per-call envelope")
        return {
            "status": "FAIL",
            "failure_layer": "interceptor",
            "root_cause": "auth likely expected at client/interceptor layer rather than request body alone",
            "evidence": evidence,
        }

    return {
        "status": "PASS",
        "failure_layer": None,
        "root_cause": "none",
        "evidence": ["rpc succeeded"],
    }


def run_local_rpc_auth_audit(ports: list[int], csrf_token: str, session_id: str) -> dict[str, object]:
    saved_csrf = os.environ.get("WINDSURF_CSRF_TOKEN")
    saved_session = os.environ.get("WINDSURF_SESSION_ID")
    saved_host = os.environ.get("WINDSURF_LS_HOST_HEADER")
    saved_url = os.environ.get("WINDSURF_LANGUAGE_SERVER_URL")
    token = resolve_auth_context_for_mode("ls_emulator")["token"]
    methods = [
        ("GetModelStatuses", "GetModelStatuses"),
        ("CheckChatCapacity", "CheckChatCapacity"),
        ("CheckUserMessageRateLimit", "CheckUserMessageRateLimit"),
        ("StartCascade", "StartCascade"),
        ("SendUserCascadeMessage", "SendUserCascadeMessage"),
    ]

    def build_probe_request(method_name: str, port: int):
        os.environ["WINDSURF_LANGUAGE_SERVER_URL"] = f"http://127.0.0.1:{port}"
        os.environ.pop("WINDSURF_LS_HOST_HEADER", None)
        if method_name == "StartCascade":
            return build_start_cascade_probe_request(token)
        if method_name == "SendUserCascadeMessage":
            return build_send_user_cascade_message_probe_request(token, "probe-cascade-id")
        body, preview = build_start_cascade_request(token)
        preview = {**preview, "url": get_local_language_server_service_url(method_name)}
        request = urllib.request.Request(
            preview["url"],
            data=body,
            headers=build_local_ls_headers(method_name=method_name),
            method="POST",
        )
        return request, preview

    try:
        os.environ["WINDSURF_CSRF_TOKEN"] = csrf_token
        os.environ["WINDSURF_SESSION_ID"] = session_id
        registry_state = discover_runtime_ls_registry_state()
        resolved_ports = ports
        if registry_state.get("status") == "READY":
            primary_port = registry_state.get("primary_ls_port")
            if isinstance(primary_port, int) and primary_port > 0:
                resolved_ports = [primary_port]
        report = {}
        for port in resolved_ports:
            port_report = []
            for rpc_name, method_name in methods:
                request, _preview = build_probe_request(method_name, port)
                exit_code, result = run_request(request)
                forensic = capture_forensic_rpc_exchange(rpc_name, request, result)
                classification = classify_401_root_cause(forensic)
                port_report.append(
                    {
                        "rpc": rpc_name,
                        "exitCode": exit_code,
                        "forensic": forensic,
                        "classification": classification,
                    }
                )
            report[str(port)] = port_report
        return {"registry": registry_state, "audit": report}
    finally:
        if saved_csrf is None:
            os.environ.pop("WINDSURF_CSRF_TOKEN", None)
        else:
            os.environ["WINDSURF_CSRF_TOKEN"] = saved_csrf
        if saved_session is None:
            os.environ.pop("WINDSURF_SESSION_ID", None)
        else:
            os.environ["WINDSURF_SESSION_ID"] = saved_session
        if saved_host is None:
            os.environ.pop("WINDSURF_LS_HOST_HEADER", None)
        else:
            os.environ["WINDSURF_LS_HOST_HEADER"] = saved_host
        if saved_url is None:
            os.environ.pop("WINDSURF_LANGUAGE_SERVER_URL", None)
        else:
            os.environ["WINDSURF_LANGUAGE_SERVER_URL"] = saved_url


class DirectExecutor:
    layer = OBSERVATION_LAYER_DIRECT

    @staticmethod
    def execute(request: urllib.request.Request, timeout: int = 120) -> tuple[int, dict[str, object]]:
        return run_request(request, timeout=timeout)


class LSEmulatorExecutor:
    layer = OBSERVATION_LAYER_LS_EMULATOR

    @staticmethod
    def execute(request: urllib.request.Request, timeout: int = 120) -> tuple[int, dict[str, object]]:
        return run_request(request, timeout=timeout)


class ReplayExecutor:
    layer = OBSERVATION_LAYER_REPLAY

    @staticmethod
    def execute(*_args, **_kwargs):
        raise RuntimeError("no execution allowed in replay mode")


def start_cascade(token: str, base_url: str | None = None) -> tuple[int, urllib.request.Request, dict[str, object], dict[str, object]]:
    request, preview = build_start_cascade_probe_request(token, base_url)
    exit_code, result = run_request(request)
    result["structuredLog"] = build_structured_rpc_log("StartCascade", request, result, preview)
    cascade_id = extract_cascade_id_from_start_result(result)
    if cascade_id:
        result["cascadeId"] = cascade_id
    return exit_code, request, preview, result


def send_user_cascade_message(token: str, cascade_id: str) -> tuple[int, urllib.request.Request, dict[str, object], dict[str, object]]:
    request, preview = build_send_user_cascade_message_probe_request(token, cascade_id)
    exit_code, result = run_request(request)
    result["structuredLog"] = build_structured_rpc_log("SendUserCascadeMessage", request, result, preview)
    return exit_code, request, preview, result


def assign_model_probe(token: str) -> tuple[int, urllib.request.Request, dict[str, object], dict[str, object]]:
    request, preview = build_assign_model_probe_request(token)
    exit_code, result = run_request(request)
    result["structuredLog"] = build_structured_rpc_log("AssignModel", request, result, preview)
    return exit_code, request, preview, result


def build_traffic_replay_request_from_event(event: dict[str, object]) -> urllib.request.Request:
    request_payload = event.get("request", {})
    url = request_payload.get("url")
    headers = request_payload.get("headers", {})
    method = request_payload.get("method", "POST")
    body = request_payload.get("body")
    if not isinstance(url, str) or not url:
        raise ValueError("replay event is missing request.url")
    data = body.encode("utf-8") if isinstance(body, str) else None
    filtered_headers = {key: value for key, value in headers.items() if isinstance(key, str) and isinstance(value, str)}
    return urllib.request.Request(url, data=data, headers=filtered_headers, method=method)


def replay_from_capture(capture_path: str) -> dict[str, object]:
    with open(capture_path, "r", encoding="utf-8") as handle:
        events = [json.loads(line) for line in handle if line.strip()]

    flows = []
    for event in events:
        request_payload = event.get("request", {})
        url = request_payload.get("url", "")
        metadata = request_payload.get("metadata", {}) if isinstance(request_payload, dict) else {}
        session_id = metadata.get("sessionId") if isinstance(metadata, dict) else None
        if "startcascade" in url.lower():
            flow_type = "StartCascade"
        elif "sendusercascademessage" in url.lower():
            flow_type = "SendUserCascadeMessage"
        elif "assignmodel" in url.lower():
            flow_type = "AssignModel"
        elif "getcascadetrajectory" in url.lower():
            flow_type = "GetCascadeTrajectory"
        else:
            continue
        flows.append(
            {
                "rpc": flow_type,
                "url": url,
                "classification": event.get("classification"),
                "response": event.get("response", {}).get("protobufSummary"),
                "sessionId": session_id,
            }
        )

    return {
        "capturePath": capture_path,
        "flowCount": len(flows),
        "flows": flows,
    }


def run_ls_emulator_cycle(token: str, *, prompt_text: str, run_id: str) -> tuple[int, dict[str, object]]:
    saved_chat_text = os.environ.get("WINDSURF_CHAT_TEXT")
    try:
        os.environ["WINDSURF_CHAT_TEXT"] = prompt_text
        preconditions = build_ls_envelope_validation_summary(rpc_name="StartCascade")
        if not preconditions["valid"]:
            observation = build_run_observation(
                run_id=run_id,
                prompt_text=prompt_text,
                cascade_id=None,
                metadata={},
                assignment={},
            )
            return 0, {
                "runObservation": {
                    **observation,
                    "waitingForCascadePreconditions": True,
                    "cascadeAllowed": False,
                    "preconditionErrors": list(preconditions.get("errors", [])),
                },
                "startCascade": None,
                "sendUserCascadeMessage": None,
                "assignModel": None,
            }

        if not is_runtime_ls_binding_reachable():
            refresh = refresh_runtime_ls_binding_from_live_discovery()
            if not is_runtime_ls_binding_reachable():
                observation = build_run_observation(
                    run_id=run_id,
                    prompt_text=prompt_text,
                    cascade_id=None,
                    metadata={},
                    assignment={},
                )
                return 0, {
                    "runObservation": {
                        **observation,
                        "waitingForCascadePreconditions": True,
                        "cascadeAllowed": False,
                        "preconditionErrors": ["runtime binding unreachable"],
                        "runtimeState": refresh.get("runtimeState", "RESET_CANDIDATE"),
                        "bindingSource": refresh.get("bindingSource"),
                        "bindingValidated": bool(refresh.get("bindingValidated", False)),
                        "lastValidationAt": refresh.get("lastValidationAt"),
                        "candidateBindings": list(refresh.get("candidateBindings", [])),
                    },
                    "startCascade": None,
                    "sendUserCascadeMessage": None,
                    "assignModel": None,
                }

        start_exit_code, _start_request, start_preview, start_result = start_cascade(token)
        cascade_id = start_result.get("cascadeId") or extract_cascade_id_from_start_result(start_result)

        send_preview = None
        send_result: dict[str, object] | None = None
        assign_preview = None
        assign_result: dict[str, object] | None = None
        correlation = None

        run_precondition_errors: list[str] = []
        if start_exit_code == 0 and isinstance(cascade_id, str) and cascade_id:
            send_exit_code, _send_request, send_preview, send_result = send_user_cascade_message(token, cascade_id)
            os.environ["WINDSURF_ASSIGN_MODEL_CASCADE_ID"] = cascade_id

            trajectory_result = None
            model_router_uid = os.environ.get("WINDSURF_ASSIGNMENT_MODEL_ROUTER_UID", "").strip()
            if not model_router_uid:
                live_language_server_url = get_local_language_server_url()
                if isinstance(live_language_server_url, str) and live_language_server_url:
                    _trajectory_exit_code, _trajectory_preview, trajectory_result = run_local_cascade_flow(
                        token,
                        live_language_server_url,
                    )
                    correlation = build_cascade_assignment_correlation_summary(
                        start_result,
                        send_result if isinstance(send_result, dict) else {},
                        trajectory_result if isinstance(trajectory_result, dict) else None,
                    )
                    model_router_uid = str(correlation.get("modelRouterUid") or "").strip()
                    if model_router_uid:
                        os.environ["WINDSURF_ASSIGNMENT_MODEL_ROUTER_UID"] = model_router_uid
                else:
                    correlation = build_cascade_assignment_correlation_summary(
                        start_result,
                        send_result if isinstance(send_result, dict) else {},
                    )
            else:
                correlation = build_cascade_assignment_correlation_summary(
                    start_result,
                    send_result if isinstance(send_result, dict) else {},
                )

            if model_router_uid:
                assign_exit_code, _assign_request, assign_preview, assign_result = assign_model_probe(token)
                correlation = build_cascade_assignment_correlation_summary(
                    start_result,
                    send_result if isinstance(send_result, dict) else {},
                    trajectory_result if isinstance(trajectory_result, dict) else None,
                )
                exit_code = start_exit_code or send_exit_code or assign_exit_code
            else:
                run_precondition_errors.append("missing live model router uid")
                exit_code = start_exit_code or send_exit_code
        else:
            exit_code = start_exit_code

        metadata = start_preview.get("metadata", {}) if isinstance(start_preview, dict) else {}
        observation = build_run_observation(
            run_id=run_id,
            prompt_text=prompt_text,
            cascade_id=cascade_id if isinstance(cascade_id, str) else None,
            metadata=metadata if isinstance(metadata, dict) else {},
            assignment=correlation if isinstance(correlation, dict) else {},
        )
        return exit_code, {
            "runObservation": {
                **observation,
                "waitingForCascadePreconditions": False,
                "cascadeAllowed": True,
                "preconditionErrors": run_precondition_errors,
            },
            "startCascade": {
                "requestPreview": start_preview,
                **start_result,
            },
            "sendUserCascadeMessage": None if send_result is None else {
                "requestPreview": send_preview,
                **send_result,
            },
            "assignModel": None if assign_result is None else {
                "requestPreview": assign_preview,
                **assign_result,
            },
        }
    finally:
        os.environ.pop("WINDSURF_ASSIGN_MODEL_CASCADE_ID", None)
        if saved_chat_text is None:
            os.environ.pop("WINDSURF_CHAT_TEXT", None)
        else:
            os.environ["WINDSURF_CHAT_TEXT"] = saved_chat_text


def run_instrumentation_abc_experiment() -> dict[str, object]:
    token = resolve_auth_context_for_mode("ls_emulator")["token"]
    if not token:
        raise ValueError("ls_emulator requires a session-capable token")

    saved_observed = os.environ.get("WINDSURF_SESSION_ID")
    saved_synthetic = os.environ.get("WINDSURF_SYNTHETIC_SESSION_ID")

    try:
        os.environ["WINDSURF_SESSION_ID"] = "observed-session-abc"
        os.environ.pop("WINDSURF_SYNTHETIC_SESSION_ID", None)
        exit_a, run_a = run_ls_emulator_cycle(token, prompt_text="hello isolate baseline", run_id="P1-C1-Sobs-T0")

        os.environ.pop("WINDSURF_SESSION_ID", None)
        os.environ["WINDSURF_SYNTHETIC_SESSION_ID"] = "synthetic-session-xyz"
        exit_b, run_b = run_ls_emulator_cycle(token, prompt_text="hello isolate baseline", run_id="P1-C1-Ssyn-T0")

        os.environ["WINDSURF_SESSION_ID"] = "observed-session-abc"
        os.environ["WINDSURF_SYNTHETIC_SESSION_ID"] = "synthetic-session-xyz"
        exit_c, run_c = run_ls_emulator_cycle(token, prompt_text="hello isolate baseline", run_id="P1-C1-Smix-T0")

        neutrality = build_instrumentation_neutrality_report(
            run_a["runObservation"],
            run_b["runObservation"],
            run_c["runObservation"],
        )
        return {
            "runs": {
                "A": run_a,
                "B": run_b,
                "C": run_c,
            },
            "exitCodes": {
                "A": exit_a,
                "B": exit_b,
                "C": exit_c,
            },
            "neutralityReport": neutrality,
        }
    finally:
        if saved_observed is None:
            os.environ.pop("WINDSURF_SESSION_ID", None)
        else:
            os.environ["WINDSURF_SESSION_ID"] = saved_observed

        if saved_synthetic is None:
            os.environ.pop("WINDSURF_SYNTHETIC_SESSION_ID", None)
        else:
            os.environ["WINDSURF_SYNTHETIC_SESSION_ID"] = saved_synthetic


def run_port_surface_mapping(*, ports: list[int], csrf_token: str, session_id: str) -> dict[str, object]:
    saved_mode = os.environ.get("WINDSURF_PROBE_MODE")
    saved_csrf = os.environ.get("WINDSURF_CSRF_TOKEN")
    saved_session = os.environ.get("WINDSURF_SESSION_ID")
    saved_synthetic = os.environ.get("WINDSURF_SYNTHETIC_SESSION_ID")
    saved_host = os.environ.get("WINDSURF_LS_HOST_HEADER")
    saved_url = os.environ.get("WINDSURF_LANGUAGE_SERVER_URL")
    token = resolve_auth_context_for_mode("ls_emulator")["token"]

    methods = [
        "GetModelStatuses",
        "CheckChatCapacity",
        "CheckUserMessageRateLimit",
        "StartCascade",
        "SendUserCascadeMessage",
        "GetChatMessage",
    ]

    def build_request_for_method(method_name: str, port: int):
        base_url = f"http://127.0.0.1:{port}"
        os.environ["WINDSURF_LANGUAGE_SERVER_URL"] = base_url
        os.environ.pop("WINDSURF_LS_HOST_HEADER", None)
        if method_name == "StartCascade":
            return build_start_cascade_probe_request(token, base_url)
        if method_name == "SendUserCascadeMessage":
            return build_send_user_cascade_message_probe_request(token, "probe-cascade-id")
        if method_name == "GetChatMessage":
            body, preview = build_cloud_chat_request(token)
            preview = {**preview, "url": get_local_language_server_service_url("GetChatMessage", base_url)}
            auth_token = os.environ.get("WINDSURF_CHAT_AUTHORIZATION_TOKEN", token).strip() or token
            headers = {
                "Content-Type": "application/connect+proto",
                "Connect-Protocol-Version": "1",
                "Accept": "application/json",
                "Authorization": f"Bearer {auth_token}",
                "User-Agent": os.environ.get("WINDSURF_CONNECT_USER_AGENT", "connect-es/1.7.0"),
                "Origin": get_local_origin(),
                "host": get_local_host_header(method_name),
            }
            csrf_token = get_local_csrf_token()
            if csrf_token:
                headers["x-codeium-csrf-token"] = csrf_token
            request = urllib.request.Request(preview["url"], data=body, headers=headers, method="POST")
            return request, preview
        if method_name == "CheckChatCapacity":
            body, preview = build_start_cascade_request(token, base_url)
            preview = {**preview, "url": get_local_language_server_service_url("CheckChatCapacity", base_url)}
            request = urllib.request.Request(
                preview["url"],
                data=body,
                headers=build_local_ls_headers(method_name="CheckChatCapacity"),
                method="POST",
            )
            return request, preview
        if method_name == "CheckUserMessageRateLimit":
            body, preview = build_start_cascade_request(token, base_url)
            preview = {**preview, "url": get_local_language_server_service_url("CheckUserMessageRateLimit", base_url)}
            request = urllib.request.Request(
                preview["url"],
                data=body,
                headers=build_local_ls_headers(method_name="CheckUserMessageRateLimit"),
                method="POST",
            )
            return request, preview
        if method_name == "GetModelStatuses":
            body, preview = build_start_cascade_request(token, base_url)
            preview = {**preview, "url": get_local_language_server_service_url("GetModelStatuses", base_url)}
            request = urllib.request.Request(
                preview["url"],
                data=body,
                headers=build_local_ls_headers(method_name="GetModelStatuses"),
                method="POST",
            )
            return request, preview
        raise ValueError(f"Unsupported method {method_name}")

    try:
        os.environ["WINDSURF_PROBE_MODE"] = "ls_emulator"
        os.environ["WINDSURF_CSRF_TOKEN"] = csrf_token
        os.environ["WINDSURF_SESSION_ID"] = session_id
        os.environ.pop("WINDSURF_SYNTHETIC_SESSION_ID", None)

        registry_state = discover_runtime_ls_registry_state()
        mapping = {}
        successful_ports: list[int] = []
        for port in ports:
            results = []
            for method_name in methods:
                request, preview = build_request_for_method(method_name, port)
                exit_code, result = run_request(request)
                if exit_code == 0:
                    successful_ports.append(port)
                results.append(
                    {
                        "rpc": method_name,
                        "exitCode": exit_code,
                        "status": result.get("status"),
                        "error": result.get("error"),
                        "reason": result.get("reason"),
                        "url": preview.get("url"),
                    }
                )
            mapping[str(port)] = results

        runtime_fault_taxonomy = classify_runtime_fault_taxonomy(
            {
                "canonical_reset": False,
                "renderer_pid_changed": bool(registry_state.get("renderer_pid_changed")),
                "target_destroyed": bool(registry_state.get("target_destroyed")),
                "execution_context_destroyed": bool(registry_state.get("execution_context_destroyed")),
                "messageport_terminated": bool(registry_state.get("messageport_terminated")),
                "ls_alive": registry_state.get("status") == "READY",
                "node_service_alive": bool(registry_state.get("node_service_pid")),
                "transport_reachable": bool(successful_ports),
                "transport_type": "connect_http" if successful_ports else "unknown",
            }
        )
        active_graph_snapshot = derive_active_graph_snapshot()
        active_graph_snapshot["reset_detected"] = bool(registry_state.get("renderer_pid_changed")) or bool(registry_state.get("target_destroyed")) or bool(registry_state.get("execution_context_destroyed"))
        if bool(registry_state.get("messageport_terminated")):
            active_graph_snapshot["renderer_state"]["t2_ipc_bridge_live"] = {"status": "absent", "observed": False}
        if not bool(successful_ports):
            active_graph_snapshot["renderer_state"]["t3_network_active"] = {"status": "absent", "observed": False}

        runtime_liveness_path = get_runtime_liveness_status_path()
        runtime_liveness = read_runtime_liveness_graph_inputs(runtime_liveness_path) if runtime_liveness_path is not None else None

        active_graph_correlation = build_active_graph_correlation_summary(
            {
                "graph_id": active_graph_snapshot.get("graph_id") or "G_runtime",
                "reset_detected": bool(active_graph_snapshot.get("reset_detected")),
                "renderer_state": active_graph_snapshot.get("renderer_state") or {},
                "extension_port": (runtime_liveness or {}).get("extension_port", registry_state.get("extension_port")),
                "ls_port": (runtime_liveness or {}).get("ls_port", registry_state.get("primary_ls_port")),
                "ls_alive": (runtime_liveness or {}).get("ls_alive", registry_state.get("status") == "READY"),
                "transport_reachable": (runtime_liveness or {}).get("transport_reachable", bool(successful_ports)),
            }
        )
        return {
            "surfaceMapping": mapping,
            "registry": registry_state,
            "runtimeFaultTaxonomy": runtime_fault_taxonomy,
            "activeGraphCorrelation": active_graph_correlation,
            "runtimeLiveness": runtime_liveness,
        }
    finally:
        if saved_mode is None:
            os.environ.pop("WINDSURF_PROBE_MODE", None)
        else:
            os.environ["WINDSURF_PROBE_MODE"] = saved_mode
        if saved_csrf is None:
            os.environ.pop("WINDSURF_CSRF_TOKEN", None)
        else:
            os.environ["WINDSURF_CSRF_TOKEN"] = saved_csrf
        if saved_session is None:
            os.environ.pop("WINDSURF_SESSION_ID", None)
        else:
            os.environ["WINDSURF_SESSION_ID"] = saved_session
        if saved_synthetic is None:
            os.environ.pop("WINDSURF_SYNTHETIC_SESSION_ID", None)
        else:
            os.environ["WINDSURF_SYNTHETIC_SESSION_ID"] = saved_synthetic
        if saved_host is None:
            os.environ.pop("WINDSURF_LS_HOST_HEADER", None)
        else:
            os.environ["WINDSURF_LS_HOST_HEADER"] = saved_host
        if saved_url is None:
            os.environ.pop("WINDSURF_LANGUAGE_SERVER_URL", None)
        else:
            os.environ["WINDSURF_LANGUAGE_SERVER_URL"] = saved_url


def main() -> int:
    # Parse CLI arguments first
    args = sys.argv[1:]

    # Handle --audit-local-auth PORT
    if len(args) >= 2 and args[0] == "--audit-local-auth":
        try:
            port = int(args[1])
            if port == 0:
                # Auto-discover port
                registry = discover_runtime_ls_registry_state()
                port = registry.get("primary_ls_port", 0)
                if not port:
                    emit_output({"error": "Could not discover live LS port", "registry": registry})
                    return 1

            # Get CSRF token and session ID from environment or bootstrap
            csrf_token = get_local_csrf_token()
            session_id = os.environ.get("WINDSURF_SESSION_ID", "")
            if not session_id:
                # Try to extract from bootstrap state
                bootstrap_path = pathlib.Path.home() / "AppData" / "Roaming" / "Windsurf" / "User" / "globalStorage" / "windsurf-live-bootstrap.json"
                if bootstrap_path.exists():
                    try:
                        bootstrap_data = json.loads(bootstrap_path.read_text(encoding="utf-8"))
                        session_id = bootstrap_data.get("sessionId", "windsurf-session-default")
                    except Exception:
                        session_id = "windsurf-session-default"
                else:
                    session_id = "windsurf-session-default"

            result = run_local_rpc_auth_audit([port], csrf_token, session_id)
            emit_output(result)
            return 0
        except ValueError:
            emit_output({"error": f"Invalid port: {args[1]}"})
            return 1
        except Exception as error:
            emit_output({"error": error.__class__.__name__, "message": str(error)})
            return 1

    # Handle --map-port-surfaces PORT1 PORT2 ...
    if len(args) >= 2 and args[0] == "--map-port-surfaces":
        try:
            ports = [int(p) for p in args[1:]]
            result = run_port_surface_mapping(ports)
            emit_output(result)
            return 0
        except ValueError as error:
            emit_output({"error": "Invalid port list", "message": str(error)})
            return 1
        except Exception as error:
            emit_output({"error": error.__class__.__name__, "message": str(error)})
            return 1

    # Handle --run-abc-experiment
    if len(args) >= 1 and args[0] == "--run-abc-experiment":
        try:
            result = run_instrumentation_abc_experiment()
            emit_output(result)
            return 0
        except Exception as error:
            emit_output({"error": error.__class__.__name__, "message": str(error)})
            return 1

    # Handle legacy capture args
    capture_args = sys.argv[1:]
    if capture_args:
        try:
            payload = build_capture_cli_payload(capture_args)
            if payload is not None:
                emit_output(payload)
                return 0
        except Exception as error:
            capture_path = next((arg for arg in capture_args if arg.lower().endswith(".json")), None)
            emit_output(
                {
                    "capturePath": capture_path,
                    "error": error.__class__.__name__,
                    "message": str(error),
                }
            )
            return 1

    mode = get_probe_mode()
    instrumentation_context = build_instrumentation_context(mode)
    auth = resolve_auth_context_for_mode(mode)
    token = auth["token"]
    if not token:
        emit_output(
            {
                "error": f"{TOKEN_ENV_VAR} is empty",
                "hint": auth["hint"],
                "mode": mode,
                "authType": auth["authType"],
            }
        )
        return 1

    final_response_only = get_env_flag("WINDSURF_FINAL_RESPONSE_ONLY")

    if mode == "validate":
        request = build_validate_request(token)
        exit_code, result = DirectExecutor.execute(request)
        emit_output(finalize_probe_payload({"mode": mode, **instrumentation_context, **result}))
        return exit_code

    if mode == "direct":
        request, preview = build_chat_probe_request(token)
        exit_code, result = DirectExecutor.execute(request)
        if final_response_only:
            emit_final_response_only(mode, preview, result)
            return exit_code
        emit_output(finalize_probe_payload({"mode": mode, **instrumentation_context, "requestPreview": preview, **result}))
        return exit_code

    if mode == "ls_emulator":
        local_auth = resolve_auth_context_for_mode("ls_emulator")
        local_token = local_auth["token"]
        exit_code, cycle_payload = run_ls_emulator_cycle(
            local_token,
            prompt_text=os.environ.get("WINDSURF_CHAT_TEXT", "hello"),
            run_id=os.environ.get("WINDSURF_RUN_ID", "A"),
        )
        if final_response_only:
            send_payload = cycle_payload.get("sendUserCascadeMessage")
            if isinstance(send_payload, dict):
                emit_final_response_only(
                    mode,
                    send_payload.get("requestPreview", {}),
                    send_payload,
                )
            else:
                emit_output(
                    {
                        "mode": mode,
                        "requestType": "send-user-cascade-message",
                        "status": None,
                        "finalResponse": None,
                    }
                )
            return exit_code
        emit_output(finalize_probe_payload({"mode": mode, **instrumentation_context, **cycle_payload}))
        return exit_code

    if mode == "traffic_replay_emulator":
        capture_path = os.environ.get("WINDSURF_REPLAY_CAPTURE_PATH", "").strip()
        if not capture_path:
            payload = finalize_probe_payload({
                "mode": mode,
                **instrumentation_context,
                "error": "WINDSURF_REPLAY_CAPTURE_PATH is required",
            }, enforce_native_routing_boundary=False)
            emit_output(payload)
            return 1
        payload = finalize_probe_payload({
            "mode": mode,
            **instrumentation_context,
            **replay_from_capture(capture_path),
        }, enforce_native_routing_boundary=False)
        emit_output(payload)
        return 0

    if mode == "chat":
        request, preview = build_chat_probe_request(token)
        exit_code, result = DirectExecutor.execute(request)
        if final_response_only:
            emit_final_response_only(mode, preview, result)
            return exit_code
        emit_output(finalize_probe_payload({"mode": mode, **instrumentation_context, "requestPreview": preview, **result}))
        return exit_code

    if mode == "assign-model":
        request, preview = build_assign_model_probe_request(token)
        exit_code, result = DirectExecutor.execute(request)
        if final_response_only:
            emit_final_response_only(mode, preview, result)
            return exit_code
        emit_output(finalize_probe_payload({"mode": mode, **instrumentation_context, "requestPreview": preview, **result}))
        return exit_code

    if mode == "cascade":
        live_language_server_url = resolve_live_language_server_url()
        exit_code, preview, result = run_local_cascade_flow(token, live_language_server_url)
        if final_response_only:
            emit_final_response_only(mode, preview, result)
            return exit_code
        emit_output(finalize_probe_payload({"mode": mode, **instrumentation_context, "requestPreview": preview, **result}))
        return exit_code

    if mode == "api-wrapper":
        request, preview = build_api_wrapper_probe_request(token)
        exit_code, result = DirectExecutor.execute(request)
        if final_response_only:
            emit_final_response_only(mode, preview, result)
            return exit_code
        emit_output(
            {
                "mode": mode,
                **instrumentation_context,
                "requestPreview": preview,
                **result,
            }
        )
        return exit_code

    request, preview = build_raw_chat_probe_request(token)
    exit_code, result = DirectExecutor.execute(request)
    followup_chat_variants = []
    if mode == "assign-model" and isinstance(result.get("decodedProto"), dict):
        followup_chat_variants = run_assignment_followup_variants(
            token,
            result.get("decodedProto", {}).get("assignment"),
        )
    if final_response_only:
        emit_final_response_only(mode, preview, result)
        return exit_code
    payload = finalize_probe_payload({
        "mode": mode,
        **instrumentation_context,
        "requestPreview": preview,
        "followupChatVariants": followup_chat_variants,
        **result,
    })
    emit_output(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
