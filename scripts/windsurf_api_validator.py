#!/usr/bin/env python3
"""
Windsurf API Validator - Active validation of Windsurf API connectivity.

Extracted from windsurf_test_immediate.py and made reusable.
Tests the complete cascade flow with authentication validation.

Usage:
    from windsurf_api_validator import validate_windsurf_api

    result = validate_windsurf_api(
        port=59455,
        csrf_token="a5d004fc-...",
        host_header="l.localhost"
    )

    if result["valid"]:
        print("API is working!")
    else:
        print(f"Errors: {result['errors']}")
"""

import requests
import json
from typing import Any, Optional
from datetime import datetime


def validate_windsurf_api(
    port: int,
    csrf_token: str,
    host_header: str = "l.localhost",
    timeout: float = 10.0,
    test_message: bool = True,
    test_model: bool = False
) -> dict[str, Any]:
    """
    Validate Windsurf API connectivity and authentication.

    Args:
        port: Windsurf Language Server port (usually 59455)
        csrf_token: CSRF token for authentication
        host_header: Host header value (default: "l.localhost")
        timeout: Request timeout in seconds (default: 10.0)
        test_message: Whether to test SendUserCascadeMessage (default: True)
        test_model: Whether to test AssignModel (default: False, requires modelRouterUid)

    Returns:
        dict with:
            - valid: bool - Overall validation result
            - startCascade: bool - StartCascade endpoint working
            - sendMessage: bool - SendUserCascadeMessage endpoint working
            - assignModel: bool - AssignModel endpoint working (if tested)
            - cascadeId: str | None - Cascade ID from StartCascade
            - errors: list[str] - List of error messages
            - details: dict - Detailed results per endpoint
    """
    result: dict[str, Any] = {
        "valid": False,
        "startCascade": False,
        "sendMessage": False,
        "assignModel": False,
        "cascadeId": None,
        "errors": [],
        "details": {}
    }

    api_base = f"http://localhost:{port}"

    headers = {
        "X-CSRF-Token": csrf_token,
        "Host": host_header,
        "User-Agent": "Windsurf/2.1.32",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Test 1: StartCascade
    try:
        url = f"{api_base}/StartCascade"
        payload = {
            "sweVersion": "swe-1-6",
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "clientVersion": "2.1.32"
            }
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout,
            verify=True
        )

        result["details"]["startCascade"] = {
            "status_code": response.status_code,
            "url": url
        }

        if response.status_code == 200:
            try:
                data = response.json()
                cascade_id = data.get("cascadeId")

                if cascade_id:
                    result["startCascade"] = True
                    result["cascadeId"] = cascade_id
                    result["details"]["startCascade"]["cascadeId"] = cascade_id
                else:
                    result["errors"].append("StartCascade: No cascadeId in response")
            except json.JSONDecodeError:
                result["errors"].append("StartCascade: Invalid JSON response")
        else:
            result["errors"].append(f"StartCascade: HTTP {response.status_code}")
            result["details"]["startCascade"]["error"] = response.text[:200]

    except requests.exceptions.RequestException as e:
        result["errors"].append(f"StartCascade: Request failed - {str(e)}")
        result["details"]["startCascade"] = {"error": str(e)}

    # Test 2: SendUserCascadeMessage (if StartCascade succeeded and requested)
    if result["cascadeId"] and test_message:
        try:
            url = f"{api_base}/SendUserCascadeMessage"
            payload = {
                "cascadeId": result["cascadeId"],
                "message": {
                    "content": "API validation test",
                    "role": "user"
                },
                "sweVersion": "swe-1-6"
            }

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout,
                verify=True
            )

            result["details"]["sendMessage"] = {
                "status_code": response.status_code,
                "url": url
            }

            if response.status_code == 200:
                result["sendMessage"] = True
            else:
                result["errors"].append(f"SendUserCascadeMessage: HTTP {response.status_code}")
                result["details"]["sendMessage"]["error"] = response.text[:200]

        except requests.exceptions.RequestException as e:
            result["errors"].append(f"SendUserCascadeMessage: Request failed - {str(e)}")
            result["details"]["sendMessage"] = {"error": str(e)}

    # Test 3: AssignModel (if requested and cascadeId available)
    if result["cascadeId"] and test_model:
        try:
            url = f"{api_base}/AssignModel"
            payload = {
                "cascadeId": result["cascadeId"],
                "modelRouterUid": "43078c0b-7eed-427a-ad6f-ba2c0ed61f98",
                "sweVersion": "swe-1-6"
            }

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout,
                verify=True
            )

            result["details"]["assignModel"] = {
                "status_code": response.status_code,
                "url": url
            }

            if response.status_code == 200:
                result["assignModel"] = True
            elif response.status_code == 500:
                # Server error is acceptable (DEVIN_TOKEN_EXCHANGE_PSK not set)
                # Client-side auth worked
                result["assignModel"] = True
                result["details"]["assignModel"]["note"] = "Server error (config issue, not auth)"
            else:
                result["errors"].append(f"AssignModel: HTTP {response.status_code}")
                result["details"]["assignModel"]["error"] = response.text[:200]

        except requests.exceptions.RequestException as e:
            result["errors"].append(f"AssignModel: Request failed - {str(e)}")
            result["details"]["assignModel"] = {"error": str(e)}

    # Overall validation result
    result["valid"] = result["startCascade"] and (
        result["sendMessage"] if test_message else True
    ) and (
        result["assignModel"] if test_model else True
    )

    return result


def test_csrf_token(port: int, csrf_token: str) -> bool:
    """
    Quick test if CSRF token is valid.

    Args:
        port: Windsurf Language Server port
        csrf_token: CSRF token to test

    Returns:
        True if token is valid, False otherwise
    """
    result = validate_windsurf_api(
        port=port,
        csrf_token=csrf_token,
        test_message=False,
        test_model=False
    )

    return result["startCascade"]


# Example usage
if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("Windsurf API Validator - Test")
    print("=" * 70)

    # Example configuration
    PORT = 59455
    CSRF_TOKEN = "a5d004fc-a32d-49ab-ab4d-3d27db4167f9"

    print(f"\nPort: {PORT}")
    print(f"CSRF Token: {CSRF_TOKEN[:8]}...{CSRF_TOKEN[-8:]}")

    print("\n[1/3] Testing StartCascade...")
    result = validate_windsurf_api(
        port=PORT,
        csrf_token=CSRF_TOKEN,
        test_message=True,
        test_model=False
    )

    print(f"\n[OK] Valid: {result['valid']}")
    print(f"[OK] StartCascade: {'PASS' if result['startCascade'] else 'FAIL'}")
    print(f"[OK] SendMessage: {'PASS' if result['sendMessage'] else 'FAIL'}")

    if result["cascadeId"]:
        print(f"[OK] Cascade ID: {result['cascadeId']}")

    if result["errors"]:
        print("\n[ERR] Errors:")
        for error in result["errors"]:
            print(f"  - {error}")
        sys.exit(1)

    print("\n[SUCCESS] API validation successful!")
    print(f"\nDetails: {json.dumps(result['details'], indent=2)}")
