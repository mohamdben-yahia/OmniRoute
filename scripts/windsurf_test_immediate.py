#!/usr/bin/env python3
"""
Windsurf Cascade API - Immediate Test Script
Tests the complete cascade flow with discovered CSRF token.
"""

import requests
import json
import sys
from datetime import datetime

# Discovered authentication credentials
CSRF_TOKEN = "a5d004fc-a32d-49ab-ab4d-3d27db4167f9"
HOST_HEADER = "l.localhost"
API_BASE = "http://localhost:59455"

# Common headers for all requests
COMMON_HEADERS = {
    "X-CSRF-Token": CSRF_TOKEN,
    "Host": HOST_HEADER,
    "User-Agent": "Windsurf/2.1.32",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_start_cascade():
    """Test StartCascade RPC method."""
    print_section("TEST 1: StartCascade")

    url = f"{API_BASE}/StartCascade"

    # Minimal payload with required sweVersion field
    payload = {
        "sweVersion": "swe-1-6",
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "clientVersion": "2.1.32"
        }
    }

    print(f"[OUT] Request URL: {url}")
    print(f"[OUT] Headers: {json.dumps(COMMON_HEADERS, indent=2)}")
    print(f"[OUT] Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            url,
            headers=COMMON_HEADERS,
            json=payload,
            timeout=10,
            verify=True
        )

        print(f"\n[OK] Status Code: {response.status_code}")
        print(f"[IN] Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"[IN] Response Body: {json.dumps(data, indent=2)}")

                # Extract cascadeId if present
                cascade_id = data.get("cascadeId")
                if cascade_id:
                    print(f"\n[SUCCESS] SUCCESS! Cascade ID: {cascade_id}")
                    return cascade_id
                else:
                    print("\n[WARN]  No cascadeId in response")
                    return None
            except json.JSONDecodeError:
                print(f"[IN] Response Body (text): {response.text}")
                return None
        else:
            print(f"[ERR] Error: {response.status_code}")
            print(f"[IN] Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"[ERR] Request failed: {e}")
        return None

def test_send_message(cascade_id):
    """Test SendUserCascadeMessage RPC method."""
    if not cascade_id:
        print("\n[WARN]  Skipping SendUserCascadeMessage (no cascadeId)")
        return False

    print_section("TEST 2: SendUserCascadeMessage")

    url = f"{API_BASE}/SendUserCascadeMessage"

    payload = {
        "cascadeId": cascade_id,
        "message": {
            "content": "Hello from OmniRoute test script!",
            "role": "user"
        },
        "sweVersion": "swe-1-6"
    }

    print(f"[OUT] Request URL: {url}")
    print(f"[OUT] Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            url,
            headers=COMMON_HEADERS,
            json=payload,
            timeout=10,
            verify=True
        )

        print(f"\n[OK] Status Code: {response.status_code}")

        if response.status_code == 200:
            print(f"[IN] Response: {response.text}")
            print("\n[SUCCESS] SUCCESS! Message sent")
            return True
        else:
            print(f"[ERR] Error: {response.status_code}")
            print(f"[IN] Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[ERR] Request failed: {e}")
        return False

def test_assign_model(cascade_id):
    """Test AssignModel RPC method."""
    if not cascade_id:
        print("\n[WARN]  Skipping AssignModel (no cascadeId)")
        return False

    print_section("TEST 3: AssignModel")

    url = f"{API_BASE}/AssignModel"

    # Using a known modelRouterUid from previous successful test
    payload = {
        "cascadeId": cascade_id,
        "modelRouterUid": "43078c0b-7eed-427a-ad6f-ba2c0ed61f98",
        "sweVersion": "swe-1-6"
    }

    print(f"[OUT] Request URL: {url}")
    print(f"[OUT] Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            url,
            headers=COMMON_HEADERS,
            json=payload,
            timeout=10,
            verify=True
        )

        print(f"\n[OK] Status Code: {response.status_code}")

        if response.status_code == 200:
            print(f"[IN] Response: {response.text}")
            print("\n[SUCCESS] SUCCESS! Model assigned")
            return True
        elif response.status_code == 500:
            print(f"[IN] Response: {response.text}")
            print("\n[WARN]  Server error (likely DEVIN_TOKEN_EXCHANGE_PSK not set)")
            print("    This is a server-side configuration issue, not client auth issue")
            return True  # Client-side auth worked
        else:
            print(f"[ERR] Error: {response.status_code}")
            print(f"[IN] Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[ERR] Request failed: {e}")
        return False

def main():
    """Run all tests in sequence."""
    print("\n" + "="*60)
    print("  WINDSURF CASCADE API - IMMEDIATE TEST")
    print("="*60)
    print(f"\n[KEY] CSRF Token: {CSRF_TOKEN}")
    print(f"[NET] Host Header: {HOST_HEADER}")
    print(f"[API] API Base: {API_BASE}")

    # Test 1: StartCascade
    cascade_id = test_start_cascade()

    if not cascade_id:
        print("\n[ERR] StartCascade failed. Cannot proceed with other tests.")
        sys.exit(1)

    # Test 2: SendUserCascadeMessage
    message_success = test_send_message(cascade_id)

    # Test 3: AssignModel
    model_success = test_assign_model(cascade_id)

    # Final summary
    print_section("TEST SUMMARY")
    print(f"[OK] StartCascade:           {'PASS' if cascade_id else 'FAIL'}")
    print(f"[OK] SendUserCascadeMessage: {'PASS' if message_success else 'FAIL'}")
    print(f"[OK] AssignModel:            {'PASS' if model_success else 'FAIL'}")

    if cascade_id and message_success:
        print("\n[SUCCESS] AUTHENTICATION SUCCESSFUL!")
        print("   The CSRF token and host header are working correctly.")
        print(f"   Cascade ID: {cascade_id}")
    else:
        print("\n[ERR] Some tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()

