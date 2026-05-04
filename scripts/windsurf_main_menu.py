#!/usr/bin/env python3
"""
Windsurf API Testing - Main Menu
Central script to access all testing tools.
"""

import os
import sys

def print_header():
    """Print the main header."""
    print("\n" + "=" * 70)
    print("  WINDSURF CASCADE API - TESTING TOOLKIT")
    print("=" * 70)
    print("\n🎯 Authentication Discovered!")
    print("   CSRF Token: a5d004fc-a32d-49ab-ab4d-3d27db4167f9")
    print("   API Port: 59455 (check with netstat if changed)")
    print("   Protocol: gRPC/Connect with Protobuf")
    print()

def print_menu():
    """Print the main menu."""
    print("=" * 70)
    print("  AVAILABLE TOOLS")
    print("=" * 70)
    print("\n📡 DISCOVERY TOOLS")
    print("   1. Detect Inspector Port")
    print("   2. Monitor Network Connections")
    print("   3. Discover API Endpoints")
    print("\n🔧 PAYLOAD TOOLS")
    print("   4. Build Protobuf Messages (basic)")
    print("   5. Analyze Captured Payloads")
    print("   6. Convert Hex to Binary")
    print("\n🧪 TESTING TOOLS")
    print("   7. Test gRPC API")
    print("   8. Replay Captured Payload (RECOMMENDED)")
    print("   9. Quick Authentication Test")
    print("\n📚 DOCUMENTATION")
    print("   10. View Testing Guide")
    print("   11. View Investigation Summary")
    print("\n   0. Exit")
    print()

def run_script(script_name):
    """Run a Python script."""
    script_path = os.path.join("scripts", script_name)
    if os.path.exists(script_path):
        print(f"\n🚀 Running: {script_name}\n")
        os.system(f"python {script_path}")
    else:
        print(f"\n❌ Script not found: {script_path}")
    
    input("\nPress Enter to continue...")

def view_file(filename):
    """View a documentation file."""
    if os.path.exists(filename):
        print(f"\n📖 Opening: {filename}\n")
        if sys.platform == "win32":
            os.system(f"notepad {filename}")
        else:
            os.system(f"cat {filename} | less")
    else:
        print(f"\n❌ File not found: {filename}")
    
    input("\nPress Enter to continue...")

def main():
    """Main menu loop."""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print_header()
        print_menu()
        
        choice = input("Select an option (0-11): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!\n")
            break
        elif choice == "1":
            run_script("windsurf_inspector_helper.py")
        elif choice == "2":
            run_script("windsurf_network_monitor.py")
        elif choice == "3":
            run_script("windsurf_discover_endpoints.py")
        elif choice == "4":
            run_script("windsurf_protobuf_builder.py")
        elif choice == "5":
            run_script("windsurf_payload_analyzer.py")
        elif choice == "6":
            run_script("windsurf_hex_to_binary.py")
        elif choice == "7":
            run_script("windsurf_grpc_test.py")
        elif choice == "8":
            run_script("windsurf_replay_payload.py")
        elif choice == "9":
            run_script("windsurf_test_immediate.py")
        elif choice == "10":
            view_file("WINDSURF_API_TESTING_GUIDE.md")
        elif choice == "11":
            view_file("WINDSURF_AUTH_INVESTIGATION_SUMMARY.md")
        else:
            print("\n❌ Invalid option. Please try again.")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!\n")
        sys.exit(0)
