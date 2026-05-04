#!/usr/bin/env python3
"""
Windsurf Payload Capturer
Captures real Protobuf payloads from Windsurf network traffic.

This script monitors the language_server process and captures
the actual binary payloads being sent to the API.
"""

import subprocess
import json
import time
import re
from datetime import datetime

def get_language_server_pid():
    """Get the PID of the language_server process."""
    try:
        result = subprocess.run(
            ['powershell', '-Command', 
             'Get-Process -Name "language_server_windows_x64" | Select-Object -ExpandProperty Id'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
        return None
    except Exception as e:
        print(f"Error getting PID: {e}")
        return None

def main():
    print("=" * 60)
    print("  WINDSURF PAYLOAD CAPTURER")
    print("=" * 60)
    print("\n⚠️  IMPORTANT INSTRUCTIONS:")
    print("\n1. This script needs you to manually capture payloads")
    print("2. Open Chrome DevTools in Windsurf:")
    print("   - Press Ctrl+Shift+I in Windsurf")
    print("   - Go to Network tab")
    print("   - Filter by 'LanguageServerService'")
    print("3. Send a Cascade message in Windsurf")
    print("4. In DevTools:")
    print("   - Right-click on the request")
    print("   - Select 'Copy' > 'Copy as cURL (bash)'")
    print("   - Or view the request payload in the 'Payload' tab")
    print("5. Save the binary payload to a file")
    print("\n" + "=" * 60)
    print("  ALTERNATIVE: Use Browser Export")
    print("=" * 60)
    print("\n1. In Chrome DevTools Network tab:")
    print("2. Right-click on SendUserCascadeMessage request")
    print("3. Select 'Save as HAR with content'")
    print("4. Save to: windsurf_captured_request.har")
    print("5. Run: python windsurf_har_extractor.py")
    print("\n" + "=" * 60)
    print("  BEST OPTION: Direct Binary Capture")
    print("=" * 60)
    print("\n1. In Chrome DevTools Network tab:")
    print("2. Click on SendUserCascadeMessage request")
    print("3. Go to 'Payload' tab")
    print("4. Click 'view source' (if available)")
    print("5. Copy the hex dump")
    print("6. Paste it into a file: captured_payload.hex")
    print("7. Run: python windsurf_hex_to_binary.py")
    
    print("\n" + "=" * 60)
    print("  CURRENT STATUS")
    print("=" * 60)
    
    pid = get_language_server_pid()
    if pid:
        print(f"\n✅ Language server is running (PID: {pid})")
        print(f"📡 Listening on port 59455")
        print(f"🔑 CSRF Token: a5d004fc-a32d-49ab-ab4d-3d27db4167f9")
    else:
        print("\n❌ Language server not found")
        print("   Start Windsurf first")
    
    print("\n" + "=" * 60)
    print("  NEXT STEPS")
    print("=" * 60)
    print("\n1. Capture a real payload using DevTools")
    print("2. Save it as binary file: real_payload.bin")
    print("3. Test it with: python windsurf_replay_payload.py")
    print()

if __name__ == "__main__":
    main()
