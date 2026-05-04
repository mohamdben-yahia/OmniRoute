#!/usr/bin/env python3
"""
Windsurf gRPC/Connect API Test
Tests the discovered gRPC endpoint with proper Protobuf format.
"""

import requests
import json
import struct

# Configuration
CSRF_TOKEN = "a5d004fc-a32d-49ab-ab4d-3d27db4167f9"
BASE_URL = "http://127.0.0.1:59455"  # Use IP instead of v.localhost
HOST_HEADER = "v.localhost:59455"  # But keep it in Host header
DEVIN_SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uX2lkIjoid2luZHN1cmYtc2Vzc2lvbi1hNjliYzY5NWQyN2E0NWVjYmRmNjVmYWI5MWQxODZhNiJ9.KyaNgJ8vM6gQswVjs5YMDzSb4Q7lF5313TBlV_tybqM"

# Headers from captured request
HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US",
    "connect-protocol-version": "1",
    "content-type": "application/proto",
    "host": HOST_HEADER,  # Use the host header variable
    "origin": "vscode-file://vscode-app",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Windsurf/1.110.1 Chrome/142.0.7444.265 Electron/39.6.0 Safari/537.36",
    "x-codeium-csrf-token": CSRF_TOKEN,
}

def test_start_cascade():
    """Test StartCascade endpoint."""
    url = f"{BASE_URL}/exa.language_server_pb.LanguageServerService/StartCascade"
    
    print("=" * 60)
    print("  TEST: StartCascade")
    print("=" * 60)
    print(f"\n📤 URL: {url}")
    print(f"🔑 CSRF Token: {CSRF_TOKEN}\n")
    
    # Load the protobuf payload
    try:
        with open("windsurf_start_cascade.bin", "rb") as f:
            payload = f.read()
        print(f"📦 Loaded payload: {len(payload)} bytes")
        print(f"📦 Payload hex: {payload.hex()[:100]}...")
    except FileNotFoundError:
        print("❌ Payload file not found. Run windsurf_protobuf_builder.py first.")
        return False
    
    try:
        response = requests.post(url, headers=HEADERS, data=payload, timeout=5)
        
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        print(f"📥 Response Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print(f"📥 Response (hex): {response.content.hex()[:200]}")
            print(f"📥 Response (raw): {response.content[:200]}")
            
            # Try to parse as JSON (Connect protocol can return JSON errors)
            try:
                json_response = response.json()
                print(f"📥 Response (JSON): {json.dumps(json_response, indent=2)}")
            except:
                pass
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                print(f"📥 Response: {response.json()}")
            except:
                print(f"📥 Response: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_send_user_cascade_message():
    """Test SendUserCascadeMessage endpoint."""
    url = f"{BASE_URL}/exa.language_server_pb.LanguageServerService/SendUserCascadeMessage"
    
    print("\n" + "=" * 60)
    print("  TEST: SendUserCascadeMessage")
    print("=" * 60)
    print(f"\n📤 URL: {url}")
    print(f"🔑 CSRF Token: {CSRF_TOKEN}\n")
    
    # Load the protobuf payload
    try:
        with open("windsurf_send_message.bin", "rb") as f:
            payload = f.read()
        print(f"📦 Loaded payload: {len(payload)} bytes")
        print(f"📦 Payload hex: {payload.hex()[:100]}...")
    except FileNotFoundError:
        print("❌ Payload file not found. Run windsurf_protobuf_builder.py first.")
        return False
    
    try:
        response = requests.post(url, headers=HEADERS, data=payload, timeout=5)
        
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        print(f"📥 Response Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print(f"📥 Response (hex): {response.content.hex()[:200]}")
            
            # Try to parse as JSON
            try:
                json_response = response.json()
                print(f"📥 Response (JSON): {json.dumps(json_response, indent=2)}")
            except:
                pass
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                print(f"📥 Response: {response.json()}")
            except:
                print(f"📥 Response: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("  WINDSURF gRPC/CONNECT API TEST")
    print("=" * 60)
    print(f"\n🔗 Base URL: {BASE_URL}")
    print(f"🔑 CSRF Token: {CSRF_TOKEN}")
    print(f"🎫 Session Token: {DEVIN_SESSION_TOKEN[:50]}...")
    print("\nℹ️  Note: This is a gRPC/Connect API using Protobuf")
    print("ℹ️  We need to construct proper Protobuf messages\n")
    
    # Test endpoints
    test_start_cascade()
    test_send_user_cascade_message()
    
    print("\n" + "=" * 60)
    print("  NEXT STEPS")
    print("=" * 60)
    print("\n1. We need the .proto definition files")
    print("2. Or we need to reverse-engineer the Protobuf format")
    print("3. Or we can capture and replay actual Protobuf payloads")
    print("\n💡 Recommendation: Use mitmproxy to capture full requests")
    print("   including the binary Protobuf payloads\n")

if __name__ == "__main__":
    main()
