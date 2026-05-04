#!/usr/bin/env python3
"""
Windsurf runtime inspector discovery helpers.

This module discovers the live NodeService runtime used by Windsurf and the
random localhost inspector port exposed by the NodeService process that starts
with --experimental-network-inspection --inspect-port=0.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any, Dict, Optional


def _run_powershell(command: str, timeout: int = 5) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    stdout = (result.stdout or "").strip()
    if result.returncode != 0 and not stdout:
        return {"ok": False, "error": (result.stderr or "unknown error").strip()}

    if not stdout:
        return {"ok": False, "error": "empty output"}

    try:
        payload = json.loads(stdout.splitlines()[-1])
    except Exception:
        return {"ok": False, "error": "invalid json", "raw": stdout}

    if not isinstance(payload, dict):
        return {"ok": False, "error": "unexpected payload", "raw": stdout}

    payload["ok"] = True
    return payload


def discover_nodeservice_runtime() -> Dict[str, Any]:
    command = (
        "$node = Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -eq 'Windsurf.exe' -and $_.CommandLine -match '--utility-sub-type=node\\.mojom\\.NodeService' } | "
        "Where-Object { $_.CommandLine -match '--experimental-network-inspection' } | "
        "Select-Object -First 1; "
        "if (-not $node) { @{ status='NOT_FOUND'; message='No NodeService with experimental network inspection found' } | ConvertTo-Json -Compress; return }; "
        "$ports = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -eq $node.ProcessId } | Select-Object -ExpandProperty LocalPort | Sort-Object -Unique); "
        "$inspector = $null; "
        "foreach ($port in $ports) { if ($port -ge 1024) { $inspector = [int]$port; break } }; "
        "@{ status='READY'; nodeServicePid=[int]$node.ProcessId; parentPid=[int]$node.ParentProcessId; commandLine=[string]$node.CommandLine; listenPorts=$ports; inspectorPort=$inspector } | ConvertTo-Json -Compress"
    )
    return _run_powershell(command)


def get_nodeservice_inspector_port() -> Optional[int]:
    payload = discover_nodeservice_runtime()
    if not payload.get("ok"):
        return None
    if payload.get("status") != "READY":
        return None
    port = payload.get("inspectorPort")
    return port if isinstance(port, int) and port > 0 else None


def format_nodeservice_runtime_summary() -> str:
    payload = discover_nodeservice_runtime()
    if not payload.get("ok"):
        return f"NodeService runtime discovery failed: {payload.get('error', 'unknown error')}"
    if payload.get("status") != "READY":
        return str(payload.get("message") or payload.get("status") or "NodeService runtime not ready")

    pid = payload.get("nodeServicePid")
    port = payload.get("inspectorPort")
    ports = payload.get("listenPorts") or []
    return f"NodeService PID {pid} with inspector port {port} and listeners {ports}"
