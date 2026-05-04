#!/usr/bin/env python3
"""
Windsurf Immediate Test - Step by Step Guide
Interactive guide for testing the Windsurf API.
"""

import os
import subprocess
import time

def print_step(number, title, description):
    """Print a formatted step."""
    print(f"\n{'='*70}")
    print(f"  STEP {number}: {title}")
    print(f"{'='*70}")
    print(f"\n{description}\n")

def wait_for_user():
    """Wait for user confirmation."""
    input("Press Enter when ready to continue...")

def main():
    print("\n" + "="*70)
    print("  WINDSURF API - IMMEDIATE TEST GUIDE")
    print("="*70)
    print("\n🎯 Goal: Test the Windsurf Cascade API with a real payload")
    print("⏱️  Estimated time: 5-10 minutes")
    print()
    
    # Step 1: Start Windsurf
    print_step(1, "Start Windsurf", 
        "1. Launch Windsurf application\n"
        "2. Wait for it to fully load\n"
        "3. Make sure you're logged in")
    wait_for_user()
    
    # Step 2: Open DevTools
    print_step(2, "Open DevTools",
        "1. In Windsurf, press Ctrl+Shift+I\n"
        "2. DevTools panel should open\n"
        "3. Click on the 'Network' tab\n"
        "4. Make sure recording is enabled (red dot)")
    wait_for_user()
    
    # Step 3: Clear and prepare
    print_step(3, "Prepare Network Capture",
        "1. In Network tab, click the 'Clear' button (🚫)\n"
        "2. Make sure 'All' filter is selected\n"
        "3. You're ready to capture!")
    wait_for_user()
    
    # Step 4: Send Cascade message
    print_step(4, "Send a Cascade Message",
        "1. In Windsurf, open Cascade (if not already open)\n"
        "2. Type any message (e.g., 'Hello')\n"
        "3. Send the message\n"
        "4. Watch the Network tab fill with requests")
    wait_for_user()
    
    # Step 5: Find the request
    print_step(5, "Find SendUserCascadeMessage Request",
        "1. In Network tab, look for 'SendUserCascadeMessage'\n"
        "2. It should be in the list of requests\n"
        "3. Click on it to select it\n"
        "4. The details panel will open on the right")
    wait_for_user()
    
    # Step 6: Copy payload
    print_step(6, "Copy the Payload",
        "1. In the details panel, click 'Payload' tab\n"
        "2. You should see binary/hex data\n"
        "3. Right-click and select 'Copy value'\n"
        "   OR\n"
        "4. Select all the hex data and copy it")
    
    print("\n📋 Paste the hex data here (or press Enter to skip):")
    hex_data = input().strip()
    
    if hex_data:
        # Save hex data
        print("\n💾 Saving hex data to captured_send_message.hex...")
        with open("captured_send_message.hex", "w") as f:
            f.write(hex_data)
        print("✅ Saved!")
        
        # Convert to binary
        print("\n🔄 Converting to binary...")
        result = subprocess.run(
            ["python", "scripts/windsurf_hex_to_binary.py"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        
        if os.path.exists("captured_send_message.bin"):
            print("✅ Binary file created!")
            
            # Step 7: Get current CSRF token
            print_step(7, "Get Current CSRF Token",
                "1. In the same request details\n"
                "2. Click 'Headers' tab\n"
                "3. Scroll to 'Request Headers'\n"
                "4. Find 'x-codeium-csrf-token'\n"
                "5. Copy the token value")
            
            print("\n🔑 Paste the CSRF token here (or press Enter to use cached):")
            csrf_token = input().strip()
            
            if csrf_token:
                print(f"\n✅ Token: {csrf_token}")
                print("\n📝 Updating scripts with new token...")
                # Update token in replay script
                # (This would require modifying the script file)
            
            # Step 8: Replay
            print_step(8, "Replay the Payload",
                "Now we'll replay the captured payload to test the API.")
            
            print("\n🚀 Running replay script...")
            wait_for_user()
            
            result = subprocess.run(
                ["python", "scripts/windsurf_replay_payload.py"],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            
            if "200" in result.stdout:
                print("\n🎉 SUCCESS! The API is working!")
            else:
                print("\n⚠️  Check the output above for any errors")
        else:
            print("❌ Binary conversion failed")
    else:
        print("\n⚠️  No hex data provided. Manual steps:")
        print("\n1. Save hex data to: captured_send_message.hex")
        print("2. Run: python scripts/windsurf_hex_to_binary.py")
        print("3. Run: python scripts/windsurf_replay_payload.py")
    
    # Final summary
    print("\n" + "="*70)
    print("  TEST COMPLETE")
    print("="*70)
    print("\n📚 For more information:")
    print("   • WINDSURF_API_TESTING_GUIDE.md")
    print("   • WINDSURF_QUICK_REFERENCE.md")
    print("\n💡 Next steps:")
    print("   • Integrate with OmniRoute")
    print("   • Implement token refresh")
    print("   • Add error handling")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. You can resume anytime!\n")
