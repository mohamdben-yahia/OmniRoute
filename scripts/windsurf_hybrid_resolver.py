#!/usr/bin/env python3
"""
Windsurf Hybrid Resolver - Combines passive health checks with active API validation.

This module provides a unified backend resolution strategy that:
1. Uses passive observation for continuous health monitoring (lightweight)
2. Uses active API validation for authentication verification (thorough)
3. Combines both approaches for robust routing decisions

Usage:
    from windsurf_hybrid_resolver import resolve_windsurf_backend_hybrid

    backend = resolve_windsurf_backend_hybrid(
        max_age_minutes=5.0,
        require_csrf=True,
        validate_api=False  # Only validate on setup/periodic checks
    )

    if backend["available"]:
        # Route to Windsurf
        url = f"http://127.0.0.1:{backend['port']}/api/v1/cascade/start"
        headers = {"x-csrf-token": backend["csrfToken"]}
    else:
        # Fallback to other provider
        print(f"Reason: {backend['reason']}")
"""

import json
import pathlib
from typing import Any, Optional
from datetime import datetime, timezone

try:
    from windsurf_health_check import windsurf_health_check
except ImportError:
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

try:
    from windsurf_api_validator import validate_windsurf_api, test_csrf_token
except ImportError:
    def validate_windsurf_api(*args, **kwargs) -> dict[str, Any]:
        return {
            "valid": False,
            "errors": ["windsurf_api_validator module not found"]
        }

    def test_csrf_token(*args, **kwargs) -> bool:
        return False


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


def save_windsurf_config(config: dict[str, Any]) -> None:
    """Save Windsurf configuration to file."""
    config_path = get_config_path()
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def resolve_windsurf_backend_hybrid(
    max_age_minutes: float = 5.0,
    require_csrf: bool = True,
    validate_api: bool = False,
    validation_timeout: float = 10.0
) -> dict[str, Any]:
    """
    Resolve Windsurf backend using hybrid passive + active approach.

    Args:
        max_age_minutes: Maximum age of last activity to consider Windsurf alive (default: 5 minutes)
        require_csrf: Whether to require CSRF token for availability (default: True)
        validate_api: Whether to perform active API validation (default: False, expensive)
        validation_timeout: Timeout for API validation requests (default: 10.0 seconds)

    Returns:
        dict with:
            - available: bool - Whether Windsurf is available for routing
            - port: int | None - Extension Server port (from passive)
            - languageServerPort: int | None - Language Server port (from config)
            - csrfToken: str | None - CSRF token for authentication
            - epoch: str | None - Current Windsurf epoch
            - status: str - Health status (alive/stale/dead/error)
            - health: dict - Full health check results (from passive)
            - validation: dict | None - API validation results (from active, if requested)
            - message: str - Human-readable status message
            - reason: str | None - Reason for unavailability (if available=False)
            - lastValidation: str | None - Timestamp of last API validation
    """
    result: dict[str, Any] = {
        "available": False,
        "port": None,
        "languageServerPort": None,
        "csrfToken": None,
        "epoch": None,
        "status": "unknown",
        "health": None,
        "validation": None,
        "message": None,
        "reason": None,
        "lastValidation": None
    }

    # Step 1: Passive health check
    health = windsurf_health_check()
    result["health"] = health
    result.update({
        "port": health["port"],
        "epoch": health["epoch"],
        "status": health["status"],
        "message": health["message"]
    })

    # Step 2: Check if Windsurf is alive (passive)
    if health["status"] == "dead":
        result["reason"] = "Windsurf is not running or inactive (passive check)"
        return result

    if health["status"] == "error":
        result["reason"] = f"Health check error: {health['message']}"
        return result

    # Step 3: Check age threshold (passive)
    if health["ageMinutes"] is not None and health["ageMinutes"] > max_age_minutes:
        result["reason"] = f"Windsurf is stale (last activity {health['ageMinutes']:.1f} minutes ago)"
        return result

    # Step 4: Load configuration (CSRF token + Language Server port)
    config = load_windsurf_config()
    if config:
        result["csrfToken"] = config.get("csrfToken")
        result["languageServerPort"] = config.get("languageServerPort")
        result["lastValidation"] = config.get("lastValidation")

    # Step 5: Check CSRF token availability
    if require_csrf and not result["csrfToken"]:
        result["reason"] = "CSRF token not configured (run windsurf_connection_helper.py)"
        return result

    # Step 6: Active API validation (if requested)
    if validate_api and result["csrfToken"] and result["languageServerPort"]:
        try:
            validation = validate_windsurf_api(
                port=result["languageServerPort"],
                csrf_token=result["csrfToken"],
                timeout=validation_timeout,
                test_message=True,
                test_model=False
            )

            result["validation"] = validation

            if not validation["valid"]:
                result["reason"] = f"API validation failed: {', '.join(validation['errors'])}"

                # Update config with validation failure
                if config:
                    config["lastValidation"] = datetime.now(timezone.utc).isoformat()
                    config["lastValidationResult"] = "failed"
                    config["lastValidationErrors"] = validation["errors"]
                    save_windsurf_config(config)

                return result

            # Update config with successful validation
            if config:
                config["lastValidation"] = datetime.now(timezone.utc).isoformat()
                config["lastValidationResult"] = "success"
                config["lastValidationErrors"] = []
                save_windsurf_config(config)

            result["lastValidation"] = config["lastValidation"]

        except Exception as e:
            result["reason"] = f"API validation exception: {str(e)}"
            return result

    # Step 7: All checks passed
    result["available"] = True
    result["reason"] = None

    return result


def get_windsurf_request_headers(csrf_token: str, for_language_server: bool = False) -> dict[str, str]:
    """
    Get HTTP headers for Windsurf API requests.

    Args:
        csrf_token: CSRF token from configuration
        for_language_server: If True, include Language Server specific headers (default: False)

    Returns:
        dict with required headers
    """
    headers = {
        "x-csrf-token": csrf_token,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    if for_language_server:
        headers.update({
            "X-CSRF-Token": csrf_token,  # Language Server uses uppercase
            "Host": "l.localhost",
            "User-Agent": "Windsurf/2.1.32"
        })

    return headers


def get_windsurf_api_url(
    port: int,
    endpoint: str = "/api/v1/cascade/start",
    use_language_server: bool = False
) -> str:
    """
    Get Windsurf API URL.

    Args:
        port: Server port (Extension Server or Language Server)
        endpoint: API endpoint path (default: /api/v1/cascade/start)
        use_language_server: If True, use Language Server RPC format (default: False)

    Returns:
        Full URL string
    """
    if use_language_server:
        # Language Server uses direct RPC endpoints
        return f"http://127.0.0.1:{port}{endpoint}"
    else:
        # Extension Server uses standard REST API
        return f"http://127.0.0.1:{port}{endpoint}"


# Example usage
if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("Windsurf Hybrid Resolver - Test")
    print("=" * 70)

    # Test 1: Passive health check only
    print("\n[1/3] Testing passive health check...")
    backend = resolve_windsurf_backend_hybrid(
        max_age_minutes=5.0,
        require_csrf=True,
        validate_api=False
    )

    print(f"\nAvailable: {backend['available']}")
    print(f"Status: {backend['status']}")
    print(f"Extension Server Port: {backend['port']}")
    print(f"Language Server Port: {backend['languageServerPort']}")
    print(f"Epoch: {backend['epoch']}")
    print(f"CSRF Token: {'[OK] Configured' if backend['csrfToken'] else '[X] Not configured'}")
    print(f"Message: {backend['message']}")

    if not backend["available"]:
        print(f"\nReason: {backend['reason']}")
        sys.exit(1)

    # Test 2: With API validation (if CSRF token available)
    if backend["csrfToken"] and backend["languageServerPort"]:
        print("\n[2/3] Testing with API validation...")
        backend_validated = resolve_windsurf_backend_hybrid(
            max_age_minutes=5.0,
            require_csrf=True,
            validate_api=True
        )

        print(f"\nValidation Result: {'PASS' if backend_validated['validation'] and backend_validated['validation']['valid'] else 'FAIL'}")

        if backend_validated["validation"]:
            print(f"StartCascade: {'PASS' if backend_validated['validation']['startCascade'] else 'FAIL'}")
            print(f"SendMessage: {'PASS' if backend_validated['validation']['sendMessage'] else 'FAIL'}")

            if backend_validated["validation"]["errors"]:
                print("\nValidation Errors:")
                for error in backend_validated["validation"]["errors"]:
                    print(f"  - {error}")

    # Test 3: Show example usage
    print("\n[3/3] Example Usage")
    print("=" * 70)

    if backend["available"]:
        print("\n# Extension Server (for routing)")
        print(f"URL: {get_windsurf_api_url(backend['port'])}")
        print(f"Headers: {json.dumps(get_windsurf_request_headers(backend['csrfToken']), indent=2)}")

        if backend["languageServerPort"]:
            print("\n# Language Server (for RPC)")
            print(f"URL: {get_windsurf_api_url(backend['languageServerPort'], '/StartCascade', use_language_server=True)}")
            print(f"Headers: {json.dumps(get_windsurf_request_headers(backend['csrfToken'], for_language_server=True), indent=2)}")

        print("\n[OK] Windsurf backend is ready for routing")
    else:
        print(f"\n[X] Windsurf backend unavailable: {backend['reason']}")
        sys.exit(1)
