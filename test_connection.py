#!/usr/bin/env python3
"""Test direct connection to Windsurf LS."""
import urllib.request
import json

port = 59455
csrf_token = "a5d004fc-a32d-49ab-ab4d-3d27db4167f9"

# Test different host variations
hosts_to_test = [
    f"http://localhost:{port}",
    f"http://127.0.0.1:{port}",
    f"http://l.localhost:{port}",
]

for base_url in hosts_to_test:
    print(f"\n=== Testing {base_url} ===")
    try:
        # Simple health check or method list request
        url = f"{base_url}/exa.language_server_pb.LanguageServerService/CheckUserMessageRateLimit"
        headers = {
            "Content-Type": "application/connect+proto",
            "x-codeium-csrf-token": csrf_token,
        }
        req = urllib.request.Request(url, data=b"", headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"OK Connected! Status: {response.status}")
            print(f"  Response length: {len(response.read())} bytes")
    except urllib.error.HTTPError as e:
        print(f"X Failed with HTTP {e.code}: {e.reason}")
    except Exception as e:
        print(f"X Failed: {e}")
