#!/usr/bin/env python3
"""
Windsurf Immediate Test - Using Captured Payload
Tests the API with the real captured SendUserCascadeMessage payload.
"""

import requests
import sys

# Configuration from captured request
CSRF_TOKEN = "3a1d0e5e-db26-4abe-b2f9-41704544534e"
PORT = 53740  # From captured request
BASE_URL = f"http://127.0.0.1:{PORT}"

# The captured payload (binary string from the fetch request)
CAPTURED_PAYLOAD = b'\n$b2734ac2-d2c1-4e02-9279-ffd06548f5ad\x12\x0f\n\rje suis amine\x1a\xcc\x02\n\x08windsurf\x12\x061.48.2\x1a\xbd\x01devin-session-token$eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uX2lkIjoid2luZHN1cmYtc2Vzc2lvbi1iYzBlM2MwYzY4NTc0NTc3YjRlZDkxODZmMmU5ZTJiZSJ9.MwP97lrDHO5pG_mXOVl5KhbTor_VJrPmdgbOglPIOq0"\x02en:\x062.1.32b\x08windsurf\xa2\x01%user-47ba71096f0b498daaf30bd1b11a9b6b\xf2\x01\x03\x00\x01\x03\x023devin-team$account-ae790c86db964e3f9c0296307fcf4691*2\n\x15\x12\x02 \x01j\x00\x02\x0cswe-1-6-fast:\x19\x08\x012\x022\x00r\x11MODEL_UNSPECIFIED'

def print_header():
    """Print script header."""
    print("\n" + "="*70)
    print("  WINDSURF API - IMMEDIATE TEST WITH CAPTURED PAYLOAD")
    print("="*70)
    print()

def test_send_user_cascade_message():
    """Test SendUserCascadeMessage with captured payload."""
    endpoint = f"{BASE_URL}/exa.language_server_pb.LanguageServerService/SendUserCascadeMessage"
    
    headers = {
        "accept": "*/*",
        "accept-language": "en-US",
        "connect-protocol-version": "1",
        "content-type": "application/proto",
        "x-codeium-csrf-token": CSRF_TOKEN,
        "Host": f"d.localhost:{PORT}"  # Using subdomain from captured request
    }
    
    print(f"🔗 Endpoint: {endpoint}")
    print(f"🔑 CSRF Token: {CSRF_TOKEN}")
    print(f"📦 Payload size: {len(CAPTURED_PAYLOAD)} bytes")
    print(f"🌐 Host header: d.localhost:{PORT}")
    print()
    
    try:
        print("📤 Sending request...")
        response = requests.post(
            endpoint,
            headers=headers,
            data=CAPTURED_PAYLOAD,
            timeout=10
        )
        
        print(f"\n✅ Response Status: {response.status_code}")
        print(f"📋 Response Headers:")
        for key, value in response.headers.items():
            print(f"   {key}: {value}")
        
        print(f"\n📄 Response Body ({len(response.content)} bytes):")
        if response.content:
            # Try to display as text if possible
            try:
                print(response.content.decode('utf-8'))
            except:
                print(f"   [Binary data: {response.content[:100]}...]")
        else:
            print("   [Empty response]")
        
        if response.status_code == 200:
            print("\n🎉 SUCCESS! The API is working!")
            return True
        else:
            print(f"\n⚠️  Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("\n💡 Possible reasons:")
        print("   1. Windsurf is not running")
        print("   2. Port has changed (current: 53740)")
        print("   3. Language server not started")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def test_with_updated_port():
    """Try to detect current port and test."""
    print("\n" + "="*70)
    print("  TRYING TO DETECT CURRENT PORT")
    print("="*70)
    print()
    
    # Common ports to try
    ports_to_try = [53740, 59455, 50000, 51000, 52000, 54000, 55000]
    
    for port in ports_to_try:
        print(f"🔍 Trying port {port}...")
        test_url = f"http://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetModelStatuses"
        
        try:
            response = requests.post(
                test_url,
                headers={
                    "content-type": "application/proto",
                    "x-codeium-csrf-token": CSRF_TOKEN,
                    "Host": f"x.localhost:{port}"
                },
                data=CAPTURED_PAYLOAD[:100],  # Just test with partial payload
                timeout=2
            )
            
            if response.status_code != 404:  # Any response except 404 means server is there
                print(f"✅ Found server on port {port}!")
                global PORT, BASE_URL
                PORT = port
                BASE_URL = f"http://127.0.0.1:{port}"
                return True
        except:
            continue
    
    print("❌ Could not find Windsurf server on any common port")
    return False

def main():
    """Main test function."""
    print_header()
    
    # First, try with the captured port
    print("📍 Step 1: Testing with captured port (53740)")
    print("-" * 70)
    success = test_send_user_cascade_message()
    
    if not success:
        print("\n📍 Step 2: Trying to detect current port")
        print("-" * 70)
        if test_with_updated_port():
            print("\n📍 Step 3: Retrying with detected port")
            print("-" * 70)
            success = test_send_user_cascade_message()
    
    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    
    if success:
        print("\n✅ API Test: PASSED")
        print("\n🎯 Next Steps:")
        print("   1. Integrate with OmniRoute")
        print("   2. Implement token refresh")
        print("   3. Add streaming support")
        print("   4. Handle model selection")
    else:
        print("\n❌ API Test: FAILED")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure Windsurf is running")
        print("   2. Check if port has changed:")
        print("      - Open Windsurf DevTools (Ctrl+Shift+I)")
        print("      - Go to Network tab")
        print("      - Look for any request to see current port")
        print("   3. Update CSRF token if expired:")
        print("      - In Network tab, find x-codeium-csrf-token header")
        print("      - Copy the new token value")
        print("   4. Capture a fresh payload:")
        print("      - Send a message in Cascade")
        print("      - Copy the payload from DevTools")
    
    print()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
