#!/usr/bin/env python3
"""
Windsurf Server Detector
Automatically detects if Windsurf is running and finds the current port.
"""

import subprocess
import re
import socket
import requests
import sys

def print_header():
    """Print script header."""
    print("\n" + "="*70)
    print("  WINDSURF SERVER DETECTOR")
    print("="*70)
    print()

def check_windsurf_process():
    """Check if Windsurf language server is running."""
    print("🔍 Checking for Windsurf processes...")
    
    try:
        # Check for language_server_windows_x64.exe
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq language_server_windows_x64.exe"],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if "language_server_windows_x64.exe" in result.stdout:
            print("✅ Windsurf Language Server is running!")
            
            # Extract PID
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if "language_server_windows_x64.exe" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        print(f"   PID: {pid}")
            return True
        else:
            print("❌ Windsurf Language Server is NOT running")
            return False
            
    except Exception as e:
        print(f"⚠️  Error checking process: {e}")
        return False

def find_listening_ports():
    """Find all ports that language_server is listening on."""
    print("\n🔍 Scanning for listening ports...")
    
    try:
        # Use netstat to find ports
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            shell=True
        )
        
        ports = set()
        lines = result.stdout.split('\n')
        
        for line in lines:
            if "LISTENING" in line and "127.0.0.1" in line:
                # Extract port number
                match = re.search(r'127\.0\.0\.1:(\d+)', line)
                if match:
                    port = int(match.group(1))
                    # Windsurf typically uses ports in 50000-60000 range
                    if 50000 <= port <= 60000:
                        ports.add(port)
        
        if ports:
            print(f"✅ Found {len(ports)} potential ports:")
            for port in sorted(ports):
                print(f"   - {port}")
            return sorted(ports)
        else:
            print("❌ No ports found in range 50000-60000")
            return []
            
    except Exception as e:
        print(f"⚠️  Error scanning ports: {e}")
        return []

def test_port(port, csrf_token="a5d004fc-a32d-49ab-ab4d-3d27db4167f9"):
    """Test if a port responds to Windsurf API requests."""
    test_url = f"http://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetModelStatuses"
    
    headers = {
        "content-type": "application/proto",
        "connect-protocol-version": "1",
        "x-codeium-csrf-token": csrf_token,
        "Host": f"x.localhost:{port}"
    }
    
    # Minimal protobuf payload for metadata
    minimal_payload = b'\n\x08windsurf\x12\x061.48.2'
    
    try:
        response = requests.post(
            test_url,
            headers=headers,
            data=minimal_payload,
            timeout=2
        )
        
        # Any response except connection error means server is there
        return True, response.status_code
    except requests.exceptions.ConnectionError:
        return False, None
    except Exception as e:
        return False, None

def scan_and_test_ports(ports, csrf_token="a5d004fc-a32d-49ab-ab4d-3d27db4167f9"):
    """Scan and test each port."""
    print("\n🧪 Testing ports for Windsurf API...")
    
    working_ports = []
    
    for port in ports:
        print(f"   Testing port {port}...", end=" ")
        is_working, status_code = test_port(port, csrf_token)
        
        if is_working:
            print(f"✅ WORKING (status: {status_code})")
            working_ports.append((port, status_code))
        else:
            print("❌ Not responding")
    
    return working_ports

def get_csrf_token_instructions():
    """Print instructions to get CSRF token."""
    print("\n" + "="*70)
    print("  HOW TO GET CURRENT CSRF TOKEN")
    print("="*70)
    print("""
1. Open Windsurf application
2. Press Ctrl+Shift+I to open DevTools
3. Go to Network tab
4. Send any message in Cascade
5. Click on any request in the list
6. Look for 'x-codeium-csrf-token' in Request Headers
7. Copy the token value

Example: 3a1d0e5e-db26-4abe-b2f9-41704544534e
""")

def main():
    """Main detection function."""
    print_header()
    
    # Step 1: Check if process is running
    print("📍 STEP 1: Process Detection")
    print("-" * 70)
    process_running = check_windsurf_process()
    
    if not process_running:
        print("\n" + "="*70)
        print("  WINDSURF IS NOT RUNNING")
        print("="*70)
        print("""
To start testing:
1. Launch Windsurf application
2. Wait for it to fully load
3. Make sure you're logged in
4. Run this script again

Or run the interactive guide:
   python scripts/windsurf_immediate_test_guide.py
""")
        return 1
    
    # Step 2: Find listening ports
    print("\n📍 STEP 2: Port Discovery")
    print("-" * 70)
    ports = find_listening_ports()
    
    if not ports:
        print("\n⚠️  No ports found. Windsurf might be starting up.")
        print("   Wait a few seconds and try again.")
        return 1
    
    # Step 3: Test ports
    print("\n📍 STEP 3: API Testing")
    print("-" * 70)
    working_ports = scan_and_test_ports(ports)
    
    # Summary
    print("\n" + "="*70)
    print("  DETECTION SUMMARY")
    print("="*70)
    
    if working_ports:
        print(f"\n✅ Found {len(working_ports)} working API port(s):")
        for port, status in working_ports:
            print(f"\n   Port: {port}")
            print(f"   Status: {status}")
            print(f"   Endpoint: http://127.0.0.1:{port}")
            print(f"   Host Header: *.localhost:{port}")
        
        print("\n🎯 Next Steps:")
        print(f"   1. Update your scripts to use port: {working_ports[0][0]}")
        print("   2. Get current CSRF token from DevTools")
        print("   3. Run the immediate test:")
        print("      python scripts/windsurf_test_with_captured_payload.py")
        
        get_csrf_token_instructions()
        
        return 0
    else:
        print("\n❌ No working API ports found")
        print("\n💡 Possible reasons:")
        print("   1. CSRF token is incorrect or expired")
        print("   2. Windsurf is still starting up")
        print("   3. API endpoint has changed")
        
        get_csrf_token_instructions()
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
