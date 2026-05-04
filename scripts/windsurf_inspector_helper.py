#!/usr/bin/env python3
"""
Windsurf NodeService Inspector Helper
Detects the NodeService inspector port dynamically.
"""

import subprocess
import re
from typing import Optional


def find_node_inspector_port() -> Optional[int]:
    """
    Find the NodeService inspector port by:
    1. Finding all localhost listeners via netstat
    2. Identifying Windsurf-owned processes
    3. Checking for node.mojom.NodeService with --experimental-network-inspection
    
    Returns:
        Port number if found, None otherwise
    """
    try:
        # Step 1: Get all listening ports on localhost
        netstat_result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10
        )
        
        if netstat_result.returncode != 0:
            return None
        
        # Parse netstat output for localhost listeners
        localhost_ports = {}
        for line in netstat_result.stdout.splitlines():
            if "LISTENING" in line and "127.0.0.1:" in line:
                parts = line.split()
                if len(parts) >= 5:
                    address = parts[1]
                    pid = parts[4]
                    match = re.search(r'127\.0\.0\.1:(\d+)', address)
                    if match:
                        port = int(match.group(1))
                        localhost_ports[port] = pid
        
        if not localhost_ports:
            return None
        
        # Step 2: Get all Windsurf process PIDs
        windsurf_pids = set()
        ps_result = subprocess.run(
            ["powershell", "-Command", 
             "Get-Process -Name Windsurf -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10
        )
        
        if ps_result.returncode == 0 and ps_result.stdout:
            for line in ps_result.stdout.splitlines():
                line = line.strip()
                if line.isdigit():
                    windsurf_pids.add(line)
        
        if not windsurf_pids:
            return None
        
        # Step 3: Check each Windsurf-owned port for NodeService inspector
        for port, pid in localhost_ports.items():
            if pid not in windsurf_pids:
                continue
            
            # Get process command line
            cmd_result = subprocess.run(
                ["powershell", "-Command",
                 f"(Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}').CommandLine"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )
            
            if cmd_result.returncode == 0:
                cmdline = cmd_result.stdout.strip()
                # Look for NodeService with experimental network inspection
                if "node.mojom.NodeService" in cmdline and "--experimental-network-inspection" in cmdline:
                    return port
        
        return None
        
    except Exception as e:
        print(f"Error detecting inspector port: {e}")
        return None


def main():
    """Test the inspector detection."""
    print("Detecting NodeService inspector port...")
    port = find_node_inspector_port()
    
    if port:
        print(f"✅ Found NodeService inspector on port: {port}")
        print(f"   Inspector URL: http://127.0.0.1:{port}")
    else:
        print("❌ NodeService inspector not found")
        print("   Make sure Windsurf is running")


if __name__ == "__main__":
    main()
