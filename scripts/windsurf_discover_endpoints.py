#!/usr/bin/env python3
"""
Windsurf Endpoint Discovery
Tries to discover available endpoints on the local server.
"""

import requests
import json

# Configuration
CSRF_TOKEN = "a5d004fc-a32d-49ab-ab4d-3d27db4167f9"
BASE_URL = "http://localhost:59455"

HEADERS = {
    "X-CSRF-Token": CSRF_TOKEN,
    "Host": "l.localhost",
    "User-Agent": "Windsurf/2.1.32",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Common RPC endpoint patterns to try
ENDPOINTS_TO_TRY = [
    "/",
    "/rpc",
    "/api",
    "/v1",
    "/cascade",
    "/StartCascade",
    "/start-cascade",
    "/startCascade",
    "/Cascade.StartCascade",
    "/cascade/start",
    "/jsonrpc",
    "/grpc",
    "/_rpc",
    "/api/rpc",
    "/api/cascade",
]

def test_endpoint(endpoint, method="GET"):
    """Test if an endpoint exists."""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, timeout=2)
        else:
            response = requests.post(url, headers=HEADERS, json={}, timeout=2)
        
        return {
            "endpoint": endpoint,
            "method": method,
            "status": response.status_code,
            "content_type": response.headers.get("Content-Type", ""),
            "response_preview": response.text[:200] if response.text else ""
        }
    except requests.exceptions.RequestException as e:
        return {
            "endpoint": endpoint,
            "method": method,
            "error": str(e)
        }

def main():
    print("=" * 60)
    print("  WINDSURF ENDPOINT DISCOVERY")
    print("=" * 60)
    print(f"\n🔗 Base URL: {BASE_URL}")
    print(f"🔑 CSRF Token: {CSRF_TOKEN}\n")
    
    results = []
    
    # Try GET requests
    print("\n📡 Testing GET requests...")
    for endpoint in ENDPOINTS_TO_TRY:
        result = test_endpoint(endpoint, "GET")
        results.append(result)
        
        if "error" not in result:
            status = result["status"]
            emoji = "✅" if status == 200 else "⚠️" if status < 500 else "❌"
            print(f"{emoji} {endpoint:30} -> {status} {result['content_type']}")
            if result['response_preview']:
                print(f"   Preview: {result['response_preview'][:100]}")
    
    # Try POST requests
    print("\n📤 Testing POST requests...")
    for endpoint in ENDPOINTS_TO_TRY:
        result = test_endpoint(endpoint, "POST")
        results.append(result)
        
        if "error" not in result:
            status = result["status"]
            emoji = "✅" if status == 200 else "⚠️" if status < 500 else "❌"
            print(f"{emoji} {endpoint:30} -> {status} {result['content_type']}")
            if result['response_preview']:
                print(f"   Preview: {result['response_preview'][:100]}")
    
    # Save results
    output_file = "windsurf_endpoint_discovery.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Summary
    successful = [r for r in results if "error" not in r and r["status"] == 200]
    if successful:
        print(f"\n✅ Found {len(successful)} successful endpoints:")
        for r in successful:
            print(f"   {r['method']} {r['endpoint']}")
    else:
        print("\n❌ No successful endpoints found (200 OK)")
        print("\nℹ️  The server might be using:")
        print("   - gRPC protocol (binary)")
        print("   - WebSocket connections")
        print("   - Custom binary protocol")
        print("   - Named pipes (not HTTP)")

if __name__ == "__main__":
    main()
