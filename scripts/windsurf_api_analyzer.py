#!/usr/bin/env python3
"""
Windsurf API Endpoint Analyzer
Analyzes Windsurf's communication with Cascade API endpoints.
"""

import json
import subprocess
import time
from pathlib import Path
from datetime import datetime


def analyze_cascade_endpoints():
    """
    Analyze the Cascade API endpoints discovered from network monitoring.
    """
    print("=" * 70)
    print("Windsurf Cascade API Endpoint Analyzer")
    print("=" * 70)
    print()
    
    # Known endpoints from network monitoring
    endpoints = [
        {
            "ip": "35.223.238.178",
            "port": 443,
            "hostname": "178.238.223.35.bc.googleusercontent.com",
            "type": "Google Cloud"
        },
        {
            "ip": "34.49.14.144",
            "port": 443,
            "hostname": "144.14.49.34.bc.googleusercontent.com",
            "type": "Google Cloud"
        }
    ]
    
    print("📡 Discovered Cascade API Endpoints:")
    print()
    for i, endpoint in enumerate(endpoints, 1):
        print(f"{i}. {endpoint['ip']}:{endpoint['port']}")
        print(f"   Hostname: {endpoint['hostname']}")
        print(f"   Type: {endpoint['type']}")
        print()
    
    print("=" * 70)
    print("🔍 ANALYSIS")
    print("=" * 70)
    print()
    
    print("These are HTTPS endpoints (port 443), which means:")
    print("1. Traffic is encrypted with TLS")
    print("2. Cannot capture headers with simple network monitoring")
    print("3. Need to intercept at application level or use proxy")
    print()
    
    print("=" * 70)
    print("💡 RECOMMENDED APPROACHES")
    print("=" * 70)
    print()
    
    print("Approach 1: Use Windsurf's Internal State")
    print("  - Check if Windsurf stores auth tokens in memory")
    print("  - Use NodeService inspector to inject code")
    print("  - Extract tokens from language_server process memory")
    print()
    
    print("Approach 2: HTTP Proxy Interception")
    print("  - Set up mitmproxy or Fiddler")
    print("  - Configure Windsurf to use the proxy")
    print("  - Capture decrypted HTTPS traffic")
    print()
    
    print("Approach 3: Process Memory Dump")
    print("  - Dump language_server_windows_x64.exe memory")
    print("  - Search for sessionId and csrfToken patterns")
    print("  - Extract tokens from memory dump")
    print()
    
    print("Approach 4: Reverse Engineer Language Server")
    print("  - Analyze language_server_windows_x64.exe binary")
    print("  - Find where tokens are stored/used")
    print("  - Hook into token retrieval functions")
    print()
    
    # Save analysis
    output = {
        "timestamp": datetime.now().isoformat(),
        "endpoints": endpoints,
        "recommendations": [
            "Use NodeService inspector to inject code",
            "Set up HTTP proxy (mitmproxy/Fiddler)",
            "Dump process memory and search for tokens",
            "Reverse engineer language_server binary"
        ]
    }
    
    output_file = Path("windsurf_api_analysis.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Analysis saved to: {output_file}")
    print()
    
    return endpoints


def suggest_next_steps():
    """Suggest concrete next steps based on analysis."""
    print("=" * 70)
    print("🎯 IMMEDIATE NEXT STEPS")
    print("=" * 70)
    print()
    
    print("OPTION A: Memory Dump Approach (Fastest)")
    print("  1. Install procdump: https://docs.microsoft.com/sysinternals/downloads/procdump")
    print("  2. Run: procdump -ma language_server_windows_x64.exe")
    print("  3. Search dump for 'sessionId' and 'csrfToken' strings")
    print("  4. Extract tokens from memory dump")
    print()
    
    print("OPTION B: HTTP Proxy Approach (Most Reliable)")
    print("  1. Install mitmproxy: pip install mitmproxy")
    print("  2. Start proxy: mitmproxy -p 8080")
    print("  3. Configure Windsurf to use proxy (if possible)")
    print("  4. Capture and analyze HTTPS traffic")
    print()
    
    print("OPTION C: NodeService Inspector Injection (Most Direct)")
    print("  1. Connect to NodeService inspector WebSocket")
    print("  2. Inject code to access language_server internals")
    print("  3. Extract tokens from runtime state")
    print("  4. Return tokens via CDP protocol")
    print()
    
    print("Which approach would you like to try first?")


def main():
    endpoints = analyze_cascade_endpoints()
    suggest_next_steps()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
