#!/usr/bin/env python3
"""
Windsurf Network Traffic Monitor
Monitors network traffic from language_server_windows_x64.exe to capture auth tokens.
"""

import subprocess
import re
import json
import time
from pathlib import Path
from datetime import datetime


def get_language_server_pid():
    """Get the PID of language_server_windows_x64.exe."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-Process -Name language_server_windows_x64 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pid = result.stdout.strip()
            if pid.isdigit():
                return int(pid)
    except Exception as e:
        print(f"Error getting language server PID: {e}")
    
    return None


def capture_network_connections(pid):
    """Capture active network connections for a specific PID."""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10
        )
        
        connections = []
        for line in result.stdout.splitlines():
            if str(pid) in line and "ESTABLISHED" in line:
                parts = line.split()
                if len(parts) >= 5:
                    local_addr = parts[1]
                    remote_addr = parts[2]
                    connections.append({
                        "local": local_addr,
                        "remote": remote_addr,
                        "timestamp": datetime.now().isoformat()
                    })
        
        return connections
    
    except Exception as e:
        print(f"Error capturing connections: {e}")
        return []


def monitor_language_server(duration_seconds=60):
    """
    Monitor language_server network activity for a specified duration.
    
    Args:
        duration_seconds: How long to monitor (default 60 seconds)
    """
    print("=" * 70)
    print("Windsurf Language Server Network Monitor")
    print("=" * 70)
    print()
    
    # Get language server PID
    print("Step 1: Finding language_server_windows_x64.exe...")
    pid = get_language_server_pid()
    
    if not pid:
        print("❌ language_server_windows_x64.exe not found")
        print("   Make sure Windsurf is running and Cascade is active")
        return None
    
    print(f"✅ Found language_server_windows_x64.exe (PID: {pid})")
    print()
    
    # Monitor connections
    print(f"Step 2: Monitoring network connections for {duration_seconds} seconds...")
    print("   (Send some Cascade messages to generate traffic)")
    print()
    
    all_connections = []
    unique_remotes = set()
    
    start_time = time.time()
    check_interval = 2  # Check every 2 seconds
    
    while time.time() - start_time < duration_seconds:
        connections = capture_network_connections(pid)
        
        for conn in connections:
            remote = conn["remote"]
            if remote not in unique_remotes:
                unique_remotes.add(remote)
                all_connections.append(conn)
                print(f"🔍 New connection: {conn['local']} → {conn['remote']}")
        
        time.sleep(check_interval)
    
    print()
    print("=" * 70)
    print("📊 MONITORING SUMMARY")
    print("=" * 70)
    print(f"\n📡 Total unique remote endpoints: {len(unique_remotes)}")
    
    if all_connections:
        print("\n🌐 Remote endpoints contacted:")
        for conn in all_connections:
            print(f"   - {conn['remote']}")
    
    # Save results
    output_file = Path("windsurf_network_monitor.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "pid": pid,
            "duration_seconds": duration_seconds,
            "connections": all_connections,
            "unique_remotes": list(unique_remotes)
        }, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")
    
    return all_connections


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor Windsurf language server network traffic")
    parser.add_argument("--duration", type=int, default=60, help="Monitoring duration in seconds (default: 60)")
    
    args = parser.parse_args()
    
    connections = monitor_language_server(duration_seconds=args.duration)
    
    if connections:
        print()
        print("=" * 70)
        print("💡 NEXT STEPS")
        print("=" * 70)
        print()
        print("1. Identify the Cascade API endpoint from the remote addresses")
        print("2. Use a tool like Wireshark or Fiddler to capture HTTP headers")
        print("3. Look for Authorization headers in the captured traffic")
        print("4. Extract sessionId and csrfToken from the headers")
        return 0
    else:
        print()
        print("⚠️  No connections captured")
        print("   Make sure to send Cascade messages during monitoring")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
