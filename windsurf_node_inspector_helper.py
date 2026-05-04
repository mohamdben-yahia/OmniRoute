#!/usr/bin/env python3
"""
windsurf_node_inspector_helper.py

Detects and connects to Windsurf's NodeService inspector on a random port.
Windsurf doesn't expose renderer CDP on port 9222, but instead exposes a
NodeService inspector with --experimental-network-inspection --inspect-port=0.

This helper:
1. Finds running Windsurf processes
2. Locates NodeService process with inspector flags
3. Extracts inspector port from network listeners
4. Validates inspector endpoint
5. Returns inspector URL for use by other scripts
"""

import subprocess
import json
import re
import time
import sys
from typing import Optional, Dict, List, Tuple


def get_windsurf_processes() -> List[Dict[str, any]]:
    """
    Get all running Windsurf processes with their PIDs and command lines.
    
    Returns:
        List of dicts with 'pid' and 'commandline' keys
    """
    try:
        # Use PowerShell to get process details
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'Windsurf.exe' } | Select-Object ProcessId, CommandLine | ConvertTo-Json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"❌ Failed to get Windsurf processes: {result.stderr}", file=sys.stderr)
            return []
        
        # Parse JSON output
        output = result.stdout.strip()
        if not output:
            return []
        
        # Handle single process (not array) vs multiple processes (array)
        processes_data = json.loads(output)
        if isinstance(processes_data, dict):
            processes_data = [processes_data]
        
        # Convert to our format
        processes = []
        for proc in processes_data:
            processes.append({
                'pid': proc.get('ProcessId'),
                'commandline': proc.get('CommandLine', '')
            })
        
        return processes
    
    except subprocess.TimeoutExpired:
        print("❌ Timeout getting Windsurf processes", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse process JSON: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"❌ Error getting Windsurf processes: {e}", file=sys.stderr)
        return []


def find_node_inspector_process(processes: List[Dict[str, any]]) -> Optional[Dict[str, any]]:
    """
    Find the NodeService process with inspector flags.
    
    Looks for process with:
    - --experimental-network-inspection
    - --inspect-port=0
    
    Args:
        processes: List of process dicts from get_windsurf_processes()
    
    Returns:
        Process dict with 'pid' and 'commandline', or None if not found
    """
    for proc in processes:
        cmdline = proc.get('commandline', '').lower()
        
        # Check for inspector flags
        if '--experimental-network-inspection' in cmdline and '--inspect-port=0' in cmdline:
            return proc
    
    return None


def get_inspector_port_from_network(pid: int) -> Optional[int]:
    """
    Extract inspector port from network listeners for a given PID.
    
    Uses netstat to find listening ports owned by the PID.
    
    Args:
        pid: Process ID to search for
    
    Returns:
        Inspector port number, or None if not found
    """
    try:
        # Use netstat to find listening ports
        cmd = ["netstat", "-ano"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"❌ Failed to run netstat: {result.stderr}", file=sys.stderr)
            return None
        
        # Parse netstat output
        # Format: Proto  Local Address          Foreign Address        State           PID
        # Example: TCP    127.0.0.1:56692        0.0.0.0:0              LISTENING       1580
        
        for line in result.stdout.splitlines():
            if 'LISTENING' not in line:
                continue
            
            # Extract PID from end of line
            parts = line.split()
            if not parts:
                continue
            
            line_pid = parts[-1]
            if line_pid != str(pid):
                continue
            
            # Extract port from local address (format: 127.0.0.1:PORT)
            local_addr = parts[1] if len(parts) > 1 else ''
            if ':' not in local_addr:
                continue
            
            port_str = local_addr.split(':')[-1]
            try:
                port = int(port_str)
                # Inspector ports are typically in high range (>10000)
                if port > 10000:
                    return port
            except ValueError:
                continue
        
        return None
    
    except subprocess.TimeoutExpired:
        print("❌ Timeout running netstat", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Error extracting inspector port: {e}", file=sys.stderr)
        return None


def validate_inspector_endpoint(port: int) -> Tuple[bool, Optional[str]]:
    """
    Validate inspector endpoint and find correct URL.
    
    Tries multiple endpoints to handle 403 responses:
    - /json
    - /json/list
    - /json/version
    - /json/protocol
    
    Args:
        port: Inspector port number
    
    Returns:
        Tuple of (success: bool, endpoint_url: Optional[str])
    """
    import urllib.request
    import urllib.error
    
    endpoints = [
        f"http://127.0.0.1:{port}/json",
        f"http://127.0.0.1:{port}/json/list",
        f"http://127.0.0.1:{port}/json/version",
        f"http://127.0.0.1:{port}/json/protocol",
    ]
    
    for endpoint in endpoints:
        try:
            req = urllib.request.Request(endpoint)
            req.add_header('Host', f'127.0.0.1:{port}')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    # Validate response is JSON
                    content = response.read().decode('utf-8')
                    json.loads(content)  # Will raise if not valid JSON
                    return True, endpoint
        
        except urllib.error.HTTPError as e:
            # 403 Forbidden - try next endpoint
            if e.code == 403:
                continue
            print(f"⚠️  HTTP error on {endpoint}: {e.code} {e.reason}", file=sys.stderr)
        
        except urllib.error.URLError as e:
            print(f"⚠️  URL error on {endpoint}: {e.reason}", file=sys.stderr)
        
        except json.JSONDecodeError:
            print(f"⚠️  Invalid JSON response from {endpoint}", file=sys.stderr)
        
        except Exception as e:
            print(f"⚠️  Error validating {endpoint}: {e}", file=sys.stderr)
    
    return False, None


def detect_node_inspector(verbose: bool = True) -> Optional[str]:
    """
    Main function to detect NodeService inspector URL.
    
    Workflow:
    1. Get all Windsurf processes
    2. Find NodeService process with inspector flags
    3. Extract inspector port from network listeners
    4. Validate inspector endpoint
    5. Return inspector URL
    
    Args:
        verbose: Print progress messages
    
    Returns:
        Inspector URL (e.g., "http://127.0.0.1:56692/json"), or None if not found
    """
    if verbose:
        print("🔍 Detecting Windsurf NodeService inspector...")
    
    # Step 1: Get Windsurf processes
    processes = get_windsurf_processes()
    if not processes:
        if verbose:
            print("❌ No Windsurf processes found")
        return None
    
    if verbose:
        print(f"✅ Found {len(processes)} Windsurf process(es)")
    
    # Step 2: Find NodeService with inspector
    inspector_proc = find_node_inspector_process(processes)
    if not inspector_proc:
        if verbose:
            print("❌ No NodeService process with inspector flags found")
        return None
    
    pid = inspector_proc['pid']
    if verbose:
        print(f"✅ Found NodeService inspector process (PID: {pid})")
    
    # Step 3: Extract inspector port
    port = get_inspector_port_from_network(pid)
    if not port:
        if verbose:
            print(f"❌ Could not extract inspector port for PID {pid}")
        return None
    
    if verbose:
        print(f"✅ Found inspector port: {port}")
    
    # Step 4: Validate endpoint
    success, endpoint_url = validate_inspector_endpoint(port)
    if not success:
        if verbose:
            print(f"❌ Could not validate inspector endpoint on port {port}")
            print("⚠️  All endpoints returned 403 or failed")
        return None
    
    if verbose:
        print(f"✅ Validated inspector endpoint: {endpoint_url}")
    
    return endpoint_url


def wait_for_inspector(timeout: int = 30, poll_interval: float = 1.0, verbose: bool = True) -> Optional[str]:
    """
    Wait for NodeService inspector to become available.
    
    Polls detect_node_inspector() until success or timeout.
    
    Args:
        timeout: Maximum wait time in seconds
        poll_interval: Time between polls in seconds
        verbose: Print progress messages
    
    Returns:
        Inspector URL, or None if timeout
    """
    if verbose:
        print(f"⏳ Waiting for NodeService inspector (timeout: {timeout}s)...")
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        inspector_url = detect_node_inspector(verbose=False)
        
        if inspector_url:
            if verbose:
                print(f"✅ Inspector available: {inspector_url}")
            return inspector_url
        
        time.sleep(poll_interval)
    
    if verbose:
        print(f"❌ Timeout waiting for inspector ({timeout}s)")
    
    return None


def main():
    """
    CLI entry point for testing.
    """
    print("=" * 60)
    print("Windsurf NodeService Inspector Detection")
    print("=" * 60)
    print()
    
    # Detect inspector
    inspector_url = detect_node_inspector(verbose=True)
    
    if inspector_url:
        print()
        print("=" * 60)
        print("✅ SUCCESS")
        print("=" * 60)
        print(f"Inspector URL: {inspector_url}")
        print()
        print("You can now use this URL with Chrome DevTools Protocol clients.")
        return 0
    else:
        print()
        print("=" * 60)
        print("❌ FAILED")
        print("=" * 60)
        print("Could not detect NodeService inspector.")
        print()
        print("Possible reasons:")
        print("1. Windsurf is not running")
        print("2. NodeService process doesn't have inspector flags")
        print("3. Inspector port is not listening")
        print("4. All inspector endpoints return 403")
        print()
        print("Try:")
        print("1. Restart Windsurf")
        print("2. Check if Windsurf is running: Get-Process Windsurf")
        print("3. Check process command lines for inspector flags")
        return 1


if __name__ == "__main__":
    sys.exit(main())
