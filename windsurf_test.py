#!/usr/bin/env python3
"""
Windsurf Universal Launcher
Automatically detects the best testing option and executes it.
"""

import subprocess
import sys
import os

def print_banner():
    """Print welcome banner."""
    print("\n" + "="*70)
    print("  🚀 WINDSURF API - UNIVERSAL LAUNCHER")
    print("="*70)
    print("\n  Automatic detection and optimal test execution")
    print("  Version: 1.0 - Final")
    print("  Date: 2026-05-03 23:27 UTC")
    print("\n" + "="*70)

def check_windsurf_running():
    """Quick check if Windsurf is running."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq language_server_windows_x64.exe"],
            capture_output=True,
            text=True,
            shell=True,
            timeout=5
        )
        return "language_server_windows_x64.exe" in result.stdout
    except:
        return False

def check_payload_exists():
    """Check if captured payload files exist."""
    payload_files = [
        "captured_send_message.bin",
        "captured_start_cascade.bin",
        "captured_assign_model.bin"
    ]
    return any(os.path.exists(f) for f in payload_files)

def check_scripts_exist():
    """Check if all required scripts exist."""
    required_scripts = [
        "scripts/windsurf_one_click_test.py",
        "scripts/windsurf_immediate_test_guide.py",
        "scripts/windsurf_server_detector.py",
        "scripts/windsurf_test_with_captured_payload.py"
    ]
    return all(os.path.exists(s) for s in required_scripts)

def run_script(script_path):
    """Run a Python script."""
    try:
        result = subprocess.run(
            ["python", script_path],
            timeout=300  # 5 minutes max
        )
        return result.returncode
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running script: {e}")
        return 1

def main():
    """Main launcher function."""
    print_banner()
    
    # Check prerequisites
    print("\n🔍 Checking prerequisites...")
    
    # Check if scripts exist
    if not check_scripts_exist():
        print("\n❌ ERROR: Required scripts not found!")
        print("   Make sure you're in the OmniRoute directory")
        return 1
    
    print("✅ All scripts found")
    
    # Check Windsurf status
    print("\n🔍 Checking Windsurf status...")
    windsurf_running = check_windsurf_running()
    
    if windsurf_running:
        print("✅ Windsurf is running")
    else:
        print("❌ Windsurf is NOT running")
    
    # Check payload status
    print("\n🔍 Checking payload status...")
    payload_exists = check_payload_exists()
    
    if payload_exists:
        print("✅ Captured payload found")
    else:
        print("⚠️  No captured payload found")
    
    # Decide best option
    print("\n" + "="*70)
    print("  🎯 RECOMMENDED ACTION")
    print("="*70)
    
    if not windsurf_running:
        print("""
❌ Windsurf is not running

REQUIRED ACTION:
1. Launch Windsurf application
2. Wait for it to fully load
3. Make sure you're logged in
4. Run this script again

Or run the guided test:
   python scripts/windsurf_immediate_test_guide.py
""")
        return 1
    
    elif windsurf_running and payload_exists:
        print("""
✅ Windsurf is running
✅ Payload is available

RECOMMENDED: One-Click Test (fastest)

This will:
1. Detect the current port automatically
2. Ask for your CSRF token
3. Run the test with existing payload
4. Show results

Press Enter to start, or Ctrl+C to cancel...
""")
        try:
            input()
            print("\n🚀 Launching one-click test...\n")
            return run_script("scripts/windsurf_one_click_test.py")
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled by user")
            return 1
    
    elif windsurf_running and not payload_exists:
        print("""
✅ Windsurf is running
⚠️  No payload captured yet

RECOMMENDED: Guided Test (captures new payload)

This will:
1. Guide you step-by-step
2. Help you capture a fresh payload
3. Convert it automatically
4. Run the test
5. Show results

Press Enter to start, or Ctrl+C to cancel...
""")
        try:
            input()
            print("\n🚀 Launching guided test...\n")
            return run_script("scripts/windsurf_immediate_test_guide.py")
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled by user")
            return 1
    
    else:
        print("""
⚠️  Unexpected state

Please run one of these manually:
   python scripts/windsurf_status_summary.py
   python scripts/windsurf_main_menu.py
""")
        return 1

if __name__ == "__main__":
    sys.exit(main())
