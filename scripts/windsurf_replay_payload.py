#!/usr/bin/env python3
"""
Windsurf Payload Replayer
Replays a captured binary payload to test the API.
"""

import requests
import sys
import os

# Configuration
CSRF_TOKEN = "a5d004fc-a32d-49ab-ab4d-3d27db4167f9"
BASE_URL = "http://127.0.0.1:59455"
HOST_HEADER = "v.localhost:59455"

HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US",
    "connect-protocol-version": "1",
    "content-type": "application/proto",
    "host": HOST_HEADER,
    "origin": "vscode-file://vscode-app",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Windsurf/1.110.1 Chrome/142.0.7444.265 Electron/39.6.0 Safari/537.36",
    "x-codeium-csrf-token": CSRF_TOKEN,
}

def replay_payload(endpoint, payload_file):
    """Replay a captured payload."""
    url = f"{BASE_URL}/exa.language_server_pb.LanguageServerService/{endpoint}"
    
    print("=" * 60)
    print(f"  REPLAYING: {endpoint}")
    print("=" * 60)
    print(f"\n📤 URL: {url}")
    print(f"🔑 CSRF Token: {CSRF_TOKEN}")
    print(f"📦 Payload file: {payload_file}\n")
    
    # Load payload
    if not os.path.exists(payload_file):
        print(f"❌ Payload file not found: {payload_file}")
        print("\nTo capture a payload:")
        print("1. Open Windsurf DevTools (Ctrl+Shift+I)")
        print("2. Go to Network tab")
        print("3. Send a Cascade message")
        print("4. Find the request in Network tab")
        print("5. Right-click > Copy > Copy as cURL")
        print("6. Extract the binary data and save to file")
        return False
    
    with open(payload_file, "rb") as f:
        payload = f.read()
    
    print(f"📦 Payload size: {len(payload)} bytes")
    print(f"📦 First 50 bytes (hex): {payload[:50].hex()}")
    print(f"📦 First 50 bytes (ascii): {payload[:50].decode('ascii', errors='ignore')}\n")
    
    # Send request
    try:
        response = requests.post(url, headers=HEADERS, data=payload, timeout=10)
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📥 Response Headers:")
        for key, value in response.headers.items():
            print(f"   {key}: {value}")
        
        print(f"\n📥 Response Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print(f"✅ SUCCESS!")
            print(f"📥 Response (hex): {response.content.hex()[:200]}")
            
            # Try to decode as text
            try:
                text = response.content.decode('utf-8', errors='ignore')
                if text:
                    print(f"📥 Response (text): {text[:200]}")
            except:
                pass
            
            # Try to parse as JSON
            try:
                import json
                json_response = response.json()
                print(f"📥 Response (JSON):")
                print(json.dumps(json_response, indent=2))
            except:
                pass
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error = response.json()
                print(f"📥 Error details:")
                print(json.dumps(error, indent=2))
            except:
                print(f"📥 Response: {response.text}")
            
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 60)
    print("  WINDSURF PAYLOAD REPLAYER")
    print("=" * 60)
    print(f"\n🔗 Base URL: {BASE_URL}")
    print(f"🔑 CSRF Token: {CSRF_TOKEN}\n")
    
    # Check for payload files
    endpoints = {
        "StartCascade": "captured_start_cascade.bin",
        "SendUserCascadeMessage": "captured_send_message.bin",
        "AssignModel": "captured_assign_model.bin"
    }
    
    found_any = False
    for endpoint, filename in endpoints.items():
        if os.path.exists(filename):
            found_any = True
            print(f"\n{'='*60}")
            replay_payload(endpoint, filename)
    
    if not found_any:
        print("\n⚠️  No captured payload files found!")
        print("\nExpected files:")
        for endpoint, filename in endpoints.items():
            print(f"   - {filename} (for {endpoint})")
        
        print("\n📝 How to capture payloads:")
        print("\n1. Open Windsurf")
        print("2. Press Ctrl+Shift+I to open DevTools")
        print("3. Go to Network tab")
        print("4. Send a Cascade message")
        print("5. Find the request (e.g., SendUserCascadeMessage)")
        print("6. Click on it, go to 'Payload' tab")
        print("7. If you see hex data, copy it to a .hex file")
        print("8. If you see binary, use 'Copy as cURL' and extract data")
        print("\n💡 Or provide the hex dump and I'll convert it to binary")
    
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print("\nTo test the API, we need real captured payloads.")
    print("The Protobuf format is too complex to reconstruct manually.")
    print("Once you capture a payload, this script will replay it.\n")

if __name__ == "__main__":
    main()
