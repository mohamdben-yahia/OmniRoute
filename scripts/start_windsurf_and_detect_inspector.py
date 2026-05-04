#!/usr/bin/env python3
"""
Start Windsurf and detect NodeService inspector port.
Alternative method using Python subprocess instead of PowerShell.
"""

import subprocess
import time
import sys
import os
from pathlib import Path

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

try:
    from windsurf_inspector_helper import find_node_inspector_port
except ImportError:
    print("❌ Cannot import windsurf_inspector_helper.py")
    print("   Make sure windsurf_inspector_helper.py is in the same directory")
    sys.exit(1)


def find_windsurf_executable():
    """Find Windsurf.exe in common installation locations."""
    common_paths = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Windsurf" / "Windsurf.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Windsurf" / "Windsurf.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Windsurf" / "Windsurf.exe",
    ]
    
    for path in common_paths:
        if path.exists():
            return path
    
    return None


def is_windsurf_running():
    """Check if Windsurf is already running."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Process -Name Windsurf -ErrorAction SilentlyContinue"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return "Windsurf" in result.stdout
    except Exception:
        return False


def start_windsurf(exe_path):
    """Start Windsurf process in detached mode."""
    try:
        # Use CREATE_NEW_PROCESS_GROUP and DETACHED_PROCESS flags
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        
        subprocess.Popen(
            [str(exe_path)],
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
        return True
    except Exception as e:
        print(f"❌ Failed to start Windsurf: {e}")
        return False


def main():
    print("=" * 70)
    print("Windsurf NodeService Inspector Detection")
    print("=" * 70)
    print()
    
    # Step 1: Check if Windsurf is already running
    print("Step 1: Checking if Windsurf is running...")
    if is_windsurf_running():
        print("✅ Windsurf is already running")
    else:
        print("⚠️  Windsurf is not running")
        
        # Step 2: Find Windsurf executable
        print("\nStep 2: Finding Windsurf executable...")
        exe_path = find_windsurf_executable()
        if not exe_path:
            print("❌ Cannot find Windsurf.exe")
            print("   Please start Windsurf manually and run this script again")
            return 1
        
        print(f"✅ Found: {exe_path}")
        
        # Step 3: Start Windsurf
        print("\nStep 3: Starting Windsurf...")
        if not start_windsurf(exe_path):
            return 1
        
        print("✅ Windsurf started")
        print("   Waiting 10 seconds for initialization...")
        time.sleep(10)
    
    # Step 4: Detect NodeService inspector port
    print("\nStep 4: Detecting NodeService inspector port...")
    for attempt in range(3):
        if attempt > 0:
            print(f"   Retry {attempt}/3...")
            time.sleep(3)
        
        port = find_node_inspector_port()
        if port:
            print(f"✅ NodeService inspector detected on port: {port}")
            print(f"   Inspector URL: http://127.0.0.1:{port}")
            print()
            print("=" * 70)
            print("SUCCESS: NodeService inspector is available")
            print("=" * 70)
            print()
            print("Next steps:")
            print("1. Update windsurf_quick_start.py to use this port")
            print("2. Update windsurf_token_extractor.py to connect to this port")
            print("3. Run: python windsurf_quick_start.py")
            return 0
    
    print("❌ Failed to detect NodeService inspector port")
    print()
    print("Troubleshooting:")
    print("1. Verify Windsurf is running: Get-Process -Name Windsurf")
    print("2. Check for inspector ports: netstat -ano | findstr LISTENING | findstr 127.0.0.1")
    print("3. Look for node.mojom.NodeService processes with --experimental-network-inspection")
    return 1


if __name__ == "__main__":
    sys.exit(main())
