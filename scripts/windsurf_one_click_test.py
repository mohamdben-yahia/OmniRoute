#!/usr/bin/env python3
"""
Windsurf One-Click Test
Automated end-to-end test with minimal user interaction.
"""

import subprocess
import sys
import time
import os

def print_banner():
    """Print welcome banner."""
    print("\n" + "="*70)
    print("  🚀 WINDSURF API - ONE-CLICK TEST")
    print("="*70)
    print("\n  Automated testing with minimal interaction")
    print("  Press Ctrl+C at any time to cancel\n")
    print("="*70)

def print_step(number, title):
    """Print step header."""
    print(f"\n{'='*70}")
    print(f"  STEP {number}: {title}")
    print(f"{'='*70}\n")

def run_script(script_name, description):
    """Run a Python script and return success status."""
    print(f"🔄 {description}...")
    
    try:
        result = subprocess.run(
            ["python", f"scripts/{script_name}"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️  {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def check_windsurf_running():
    """Check if Windsurf is running."""
    print_step(1, "Checking Windsurf Status")
    
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq language_server_windows_x64.exe"],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if "language_server_windows_x64.exe" in result.stdout:
            print("✅ Windsurf Language Server is running!")
            return True
        else:
            print("❌ Windsurf Language Server is NOT running")
            return False
    except Exception as e:
        print(f"⚠️  Error checking Windsurf: {e}")
        return False

def prompt_start_windsurf():
    """Prompt user to start Windsurf."""
    print("\n" + "="*70)
    print("  ⚠️  WINDSURF NOT RUNNING")
    print("="*70)
    print("""
Please start Windsurf:
1. Launch Windsurf application
2. Wait for it to fully load (no splash screen)
3. Make sure you're logged in
4. Press Enter when ready...
""")
    
    try:
        input()
        return True
    except KeyboardInterrupt:
        return False

def detect_port():
    """Detect Windsurf API port."""
    print_step(2, "Detecting API Port")
    return run_script("windsurf_server_detector.py", "Port detection")

def get_csrf_token():
    """Get CSRF token from user."""
    print_step(3, "CSRF Token Required")
    
    print("""
To get your current CSRF token:
1. In Windsurf, press Ctrl+Shift+I (DevTools)
2. Go to Network tab
3. Send any message in Cascade
4. Click on any request
5. Find 'x-codeium-csrf-token' in Request Headers
6. Copy the token value

Example: 3a1d0e5e-db26-4abe-b2f9-41704544534e
""")
    
    print("📋 Paste your CSRF token here (or press Enter to use cached token):")
    token = input().strip()
    
    if token:
        print(f"✅ Token received: {token[:20]}...")
        return token
    else:
        print("⚠️  Using cached token (may be expired)")
        return None

def update_test_script(port=None, token=None):
    """Update the test script with new port and token."""
    if not port and not token:
        return True
    
    print("\n🔄 Updating test script configuration...")
    
    script_path = "scripts/windsurf_test_with_captured_payload.py"
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if port:
            # Update PORT line
            import re
            content = re.sub(
                r'PORT = \d+',
                f'PORT = {port}',
                content
            )
            print(f"   Updated PORT to {port}")
        
        if token:
            # Update CSRF_TOKEN line
            import re
            content = re.sub(
                r'CSRF_TOKEN = "[^"]*"',
                f'CSRF_TOKEN = "{token}"',
                content
            )
            print(f"   Updated CSRF_TOKEN")
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Test script updated")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update script: {e}")
        return False

def run_api_test():
    """Run the API test."""
    print_step(4, "Running API Test")
    return run_script("windsurf_test_with_captured_payload.py", "API test")

def show_summary(success):
    """Show final summary."""
    print("\n" + "="*70)
    print("  📊 TEST SUMMARY")
    print("="*70)
    
    if success:
        print("""
✅ API TEST PASSED!

The Windsurf API is working correctly.

🎯 Next Steps:
   1. Review the test output above
   2. Check WINDSURF_IMMEDIATE_TEST.md for integration steps
   3. Start integrating with OmniRoute

📚 Documentation:
   - WINDSURF_API_INVESTIGATION_FINAL_REPORT.md
   - WINDSURF_AUTH_INVESTIGATION_SUMMARY.md
   - WINDSURF_API_TESTING_GUIDE.md
""")
    else:
        print("""
❌ API TEST FAILED

Please check the error messages above.

💡 Troubleshooting:
   1. Make sure Windsurf is running
   2. Verify CSRF token is current
   3. Check port is correct
   4. Try manual test: python scripts/windsurf_immediate_test_guide.py

📚 Help:
   - WINDSURF_IMMEDIATE_TEST.md (troubleshooting section)
   - Run: python scripts/windsurf_status_summary.py
""")

def main():
    """Main one-click test function."""
    print_banner()
    
    try:
        # Step 1: Check Windsurf
        if not check_windsurf_running():
            if not prompt_start_windsurf():
                print("\n👋 Test cancelled by user")
                return 1
            
            # Wait a bit for Windsurf to start
            print("⏳ Waiting for Windsurf to start...")
            time.sleep(3)
            
            # Check again
            if not check_windsurf_running():
                print("\n❌ Windsurf still not running. Please start it and try again.")
                return 1
        
        # Step 2: Detect port
        port_detected = detect_port()
        
        # Step 3: Get CSRF token
        token = get_csrf_token()
        
        # Update script if we have new values
        if token:
            update_test_script(token=token)
        
        # Step 4: Run test
        test_passed = run_api_test()
        
        # Show summary
        show_summary(test_passed)
        
        return 0 if test_passed else 1
        
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
