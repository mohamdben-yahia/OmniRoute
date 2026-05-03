"""
Windsurf Backend Resolver - Integration module for OmniRoute routing.

This module provides Windsurf backend resolution for OmniRoute by:
1. Checking Windsurf health via passive observation
2. Loading CSRF token from configuration
3. Providing connection details for routing

Usage in OmniRoute:
    from windsurf_backend_resolver import resolve_windsurf_backend

    backend = resolve_windsurf_backend()
    if backend["available"]:
        # Route to Windsurf
        url = f"http://127.0.0.1:{backend['port']}/api/v1/cascade/start"
        headers = {"x-csrf-token": backend["csrfToken"]}
    else:
        # Fallback to other provider
        pass
"""

import json
import pathlib
from typing import Any, Optional

try:
    from windsurf_health_check import windsurf_health_check
except ImportError:
    # Fallback if health check not available
    def windsurf_health_check() -> dict[str, Any]:
        return {
            "status": "error",
            "message": "windsurf_health_check module not found",
            "port": None,
            "epoch": None,
            "pid": None,
            "lastActivity": None,
            "ageMinutes": None,
            "csrfToken": None
        }


def get_config_path() -> pathlib.Path:
    """Get path to Windsurf configuration file."""
    return pathlib.Path(__file__).parent / "windsurf_config.json"


def load_windsurf_config() -> Optional[dict[str, Any]]:
    """Load Windsurf configuration from file."""
    config_path = get_config_path()
    if not config_path.exists():
        return None

    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def resolve_windsurf_backend(
    max_age_minutes: float = 5.0,
    require_csrf: bool = True
) -> dict[str, Any]:
    """
    Resolve Windsurf backend for routing.

    Args:
        max_age_minutes: Maximum age of last activity to consider Windsurf alive (default: 5 minutes)
        require_csrf: Whether to require CSRF token for availability (default: True)

    Returns:
        dict with:
            - available: bool - Whether Windsurf is available for routing
            - port: int | None - Extension Server port
            - csrfToken: str | None - CSRF token for authentication
            - epoch: str | None - Current Windsurf epoch
            - status: str - Health status (alive/stale/dead/error)
            - message: str - Human-readable status message
            - reason: str | None - Reason for unavailability (if available=False)
    """
    result: dict[str, Any] = {
        "available": False,
        "port": None,
        "csrfToken": None,
        "epoch": None,
        "status": "unknown",
        "message": None,
        "reason": None
    }

    # Step 1: Check Windsurf health
    health = windsurf_health_check()
    result.update({
        "port": health["port"],
        "epoch": health["epoch"],
        "status": health["status"],
        "message": health["message"]
    })

    # Step 2: Check if Windsurf is alive
    if health["status"] == "dead":
        result["reason"] = "Windsurf is not running or inactive"
        return result

    if health["status"] == "error":
        result["reason"] = f"Health check error: {health['message']}"
        return result

    # Step 3: Check age threshold
    if health["ageMinutes"] is not None and health["ageMinutes"] > max_age_minutes:
        result["reason"] = f"Windsurf is stale (last activity {health['ageMinutes']:.1f} minutes ago)"
        return result

    # Step 4: Load CSRF token from config
    config = load_windsurf_config()
    if config and config.get("csrfToken"):
        result["csrfToken"] = config["csrfToken"]
    elif require_csrf:
        result["reason"] = "CSRF token not configured (run windsurf_connection_helper.py)"
        return result

    # Step 5: All checks passed
    result["available"] = True
    result["reason"] = None

    return result


def get_windsurf_request_headers(csrf_token: str) -> dict[str, str]:
    """
    Get HTTP headers for Windsurf API requests.

    Args:
        csrf_token: CSRF token from configuration

    Returns:
        dict with required headers
    """
    return {
        "x-csrf-token": csrf_token,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


def get_windsurf_api_url(port: int, endpoint: str = "/api/v1/cascade/start") -> str:
    """
    Get Windsurf API URL.

    Args:
        port: Extension Server port
        endpoint: API endpoint path (default: /api/v1/cascade/start)

    Returns:
        Full URL string
    """
    return f"http://127.0.0.1:{port}{endpoint}"


# Example usage
if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("Windsurf Backend Resolver - Test")
    print("=" * 70)

    backend = resolve_windsurf_backend()

    print(f"\nAvailable: {backend['available']}")
    print(f"Status: {backend['status']}")
    print(f"Port: {backend['port']}")
    print(f"Epoch: {backend['epoch']}")
    print(f"CSRF Token: {'[OK] Configured' if backend['csrfToken'] else '[X] Not configured'}")
    print(f"Message: {backend['message']}")

    if not backend["available"]:
        print(f"\nReason: {backend['reason']}")
        sys.exit(1)

    # Show example usage
    print("\n" + "=" * 70)
    print("Example Usage")
    print("=" * 70)
    print(f"\nURL: {get_windsurf_api_url(backend['port'])}")
    print(f"Headers: {json.dumps(get_windsurf_request_headers(backend['csrfToken']), indent=2)}")
    print("\n[OK] Windsurf backend is ready for routing")
