#!/usr/bin/env python3
"""
Windsurf Health Check - Passive observation for runtime health monitoring.

This module provides a lightweight health check for Windsurf runtime by:
1. Detecting if Windsurf is alive (epoch discovery)
2. Extracting Extension Server port from logs
3. Verifying process health (PID, memory)
4. Checking event freshness (< 5 minutes = active)

Usage:
    python windsurf_health_check.py

Returns JSON:
    {
        "status": "alive" | "stale" | "dead",
        "port": 53300,
        "epoch": "20260504T001558",
        "pid": 12116,
        "lastActivity": "2026-05-04T00:16:29Z",
        "ageMinutes": 2.5,
        "csrfToken": null  # Must be provided manually by user
    }
"""

import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Optional


def get_windsurf_logs_dir() -> pathlib.Path:
    """Get Windsurf logs directory path."""
    import os
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA environment variable not set")
    return pathlib.Path(appdata) / "Windsurf" / "logs"


def discover_latest_epoch() -> Optional[str]:
    """Discover the most recent Windsurf epoch directory."""
    logs_dir = get_windsurf_logs_dir()
    if not logs_dir.exists():
        return None

    epochs = [
        d.name for d in logs_dir.iterdir()
        if d.is_dir() and re.match(r"\d{8}T\d{6}", d.name)
    ]

    if not epochs:
        return None

    return sorted(epochs)[-1]


def extract_port_from_epoch(epoch: str) -> Optional[int]:
    """Extract Extension Server port from epoch logs."""
    logs_dir = get_windsurf_logs_dir() / epoch

    # Search in all window directories
    for window_dir in logs_dir.glob("window*"):
        windsurf_log = window_dir / "exthost" / "codeium.windsurf" / "Windsurf.log"
        if not windsurf_log.exists():
            continue

        content = windsurf_log.read_text(encoding="utf-8", errors="ignore")

        # Pattern: "Created extension server client at port 53300"
        match = re.search(r"Created extension server client at port (\d+)", content)
        if match:
            return int(match.group(1))

    return None


def extract_pid_from_epoch(epoch: str) -> Optional[int]:
    """Extract Language Server PID from epoch logs."""
    logs_dir = get_windsurf_logs_dir() / epoch

    for window_dir in logs_dir.glob("window*"):
        windsurf_log = window_dir / "exthost" / "codeium.windsurf" / "Windsurf.log"
        if not windsurf_log.exists():
            continue

        content = windsurf_log.read_text(encoding="utf-8", errors="ignore")

        # Pattern: "Starting language server process with pid 12116"
        match = re.search(r"Starting language server process with pid (\d+)", content)
        if match:
            return int(match.group(1))

    return None


def extract_last_activity_from_epoch(epoch: str) -> Optional[str]:
    """Extract timestamp of most recent log activity."""
    logs_dir = get_windsurf_logs_dir() / epoch
    latest_timestamp = None

    for window_dir in logs_dir.glob("window*"):
        windsurf_log = window_dir / "exthost" / "codeium.windsurf" / "Windsurf.log"
        if not windsurf_log.exists():
            continue

        content = windsurf_log.read_text(encoding="utf-8", errors="ignore")

        # Pattern: "2026-05-04 00:16:29.123 [info] ..."
        matches = re.findall(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})", content)
        if matches:
            # Get the last timestamp
            last_match = matches[-1]
            # Convert to ISO format
            dt = datetime.strptime(last_match, "%Y-%m-%d %H:%M:%S.%f")
            timestamp = dt.replace(tzinfo=timezone.utc).isoformat()

            if latest_timestamp is None or timestamp > latest_timestamp:
                latest_timestamp = timestamp

    return latest_timestamp


def check_process_alive(pid: int) -> bool:
    """Check if process with given PID is still running."""
    try:
        # Use tasklist on Windows
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True,
            text=True,
            check=False
        )
        return str(pid) in result.stdout
    except Exception:
        return False


def calculate_age_minutes(timestamp: str) -> float:
    """Calculate age in minutes from ISO timestamp to now."""
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    delta = now - dt
    # Return absolute value to handle clock skew
    return abs(delta.total_seconds() / 60)


def windsurf_health_check() -> dict[str, Any]:
    """
    Perform passive health check on Windsurf runtime.

    Returns:
        dict with status, port, epoch, pid, lastActivity, ageMinutes, csrfToken
    """
    result: dict[str, Any] = {
        "status": "dead",
        "port": None,
        "epoch": None,
        "pid": None,
        "lastActivity": None,
        "ageMinutes": None,
        "csrfToken": None,
        "message": None
    }

    # Step 1: Discover latest epoch
    epoch = discover_latest_epoch()
    if not epoch:
        result["message"] = "No Windsurf epochs found"
        return result

    result["epoch"] = epoch

    # Step 2: Extract port
    port = extract_port_from_epoch(epoch)
    if not port:
        result["message"] = "Extension Server port not found in logs"
        return result

    result["port"] = port

    # Step 3: Extract PID
    pid = extract_pid_from_epoch(epoch)
    if pid:
        result["pid"] = pid

        # Check if process is still alive
        if not check_process_alive(pid):
            result["status"] = "dead"
            result["message"] = f"Language Server process (PID {pid}) is not running"
            return result

    # Step 4: Extract last activity timestamp
    last_activity = extract_last_activity_from_epoch(epoch)
    if not last_activity:
        result["status"] = "stale"
        result["message"] = "No recent activity found in logs"
        return result

    result["lastActivity"] = last_activity

    # Step 5: Calculate age and determine status
    age_minutes = calculate_age_minutes(last_activity)
    result["ageMinutes"] = round(age_minutes, 2)

    if age_minutes < 5:
        result["status"] = "alive"
        result["message"] = f"Windsurf is active (last activity {age_minutes:.1f} minutes ago)"
    elif age_minutes < 30:
        result["status"] = "stale"
        result["message"] = f"Windsurf may be idle (last activity {age_minutes:.1f} minutes ago)"
    else:
        result["status"] = "dead"
        result["message"] = f"Windsurf appears inactive (last activity {age_minutes:.1f} minutes ago)"

    return result


def main() -> None:
    """Main entry point."""
    try:
        health = windsurf_health_check()
        print(json.dumps(health, indent=2))

        # Exit code based on status
        if health["status"] == "alive":
            sys.exit(0)
        elif health["status"] == "stale":
            sys.exit(1)
        else:
            sys.exit(2)

    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e),
            "port": None,
            "epoch": None,
            "pid": None,
            "lastActivity": None,
            "ageMinutes": None,
            "csrfToken": None
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(3)


if __name__ == "__main__":
    main()
