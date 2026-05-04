#!/usr/bin/env python3
"""
Windsurf Final Verification
Verifies that all files, scripts, and documentation are in place.
"""

import os
import sys

def print_header():
    """Print verification header."""
    print("\n" + "="*70)
    print("  ✅ WINDSURF API - FINAL VERIFICATION")
    print("="*70)
    print("\n  Checking that everything is ready for testing...")
    print()

def check_file(filepath, description):
    """Check if a file exists."""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"  {status} {description}")
    return exists

def check_files():
    """Check all required files."""
    print("📚 Documentation Files:")
    print("-" * 70)
    
    docs = [
        ("START_HERE.md", "Quick start guide"),
        ("WINDSURF_TEST_FINAL_SUMMARY.md", "Final summary"),
        ("WINDSURF_IMMEDIATE_TEST.md", "Detailed guide"),
        ("WINDSURF_API_TESTING_GUIDE.md", "Testing guide"),
        ("WINDSURF_QUICK_REFERENCE.md", "Quick reference"),
        ("WINDSURF_SCRIPTS_INVENTORY.md", "Scripts inventory"),
        ("WINDSURF_API_INVESTIGATION_FINAL_REPORT.md", "Investigation report"),
        ("WINDSURF_AUTH_INVESTIGATION_SUMMARY.md", "Auth summary"),
        ("WINDSURF_DOCUMENTATION_INDEX.md", "Documentation index"),
        ("WINDSURF_SUCCESS.txt", "Success banner"),
    ]
    
    doc_count = sum(check_file(f, d) for f, d in docs)
    
    print(f"\n  Total: {doc_count}/{len(docs)} documentation files found")
    
    print("\n🛠️  Script Files:")
    print("-" * 70)
    
    scripts = [
        ("windsurf_test.py", "Universal launcher"),
        ("scripts/windsurf_one_click_test.py", "One-click test"),
        ("scripts/windsurf_test_with_captured_payload.py", "Test with payload"),
        ("scripts/windsurf_immediate_test_guide.py", "Interactive guide"),
        ("scripts/windsurf_server_detector.py", "Server detector"),
        ("scripts/windsurf_status_summary.py", "Status summary"),
        ("scripts/windsurf_replay_payload.py", "Payload replayer"),
        ("scripts/windsurf_grpc_test.py", "gRPC test"),
        ("scripts/windsurf_hex_to_binary.py", "Hex converter"),
        ("scripts/windsurf_protobuf_builder.py", "Protobuf builder"),
        ("scripts/windsurf_main_menu.py", "Main menu"),
        ("scripts/README.md", "Scripts documentation"),
    ]
    
    script_count = sum(check_file(f, d) for f, d in scripts)
    
    print(f"\n  Total: {script_count}/{len(scripts)} script files found")
    
    print("\n📦 Data Files:")
    print("-" * 70)
    
    data = [
        ("reponce", "Captured payload"),
    ]
    
    data_count = sum(check_file(f, d) for f, d in data)
    
    print(f"\n  Total: {data_count}/{len(data)} data files found")
    
    return doc_count, script_count, data_count, len(docs), len(scripts), len(data)

def check_python():
    """Check Python version."""
    print("\n🐍 Python Environment:")
    print("-" * 70)
    
    version = sys.version_info
    print(f"  Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("  ✅ Python version is compatible")
        return True
    else:
        print("  ❌ Python 3.8+ required")
        return False

def check_dependencies():
    """Check required dependencies."""
    print("\n📦 Dependencies:")
    print("-" * 70)
    
    try:
        import requests
        print("  ✅ requests library installed")
        return True
    except ImportError:
        print("  ❌ requests library NOT installed")
        print("     Install with: pip install requests")
        return False

def print_summary(doc_count, script_count, data_count, total_docs, total_scripts, total_data, python_ok, deps_ok):
    """Print final summary."""
    print("\n" + "="*70)
    print("  📊 VERIFICATION SUMMARY")
    print("="*70)
    
    all_docs = doc_count == total_docs
    all_scripts = script_count == total_scripts
    all_data = data_count == total_data
    
    print(f"\n  Documentation:  {doc_count}/{total_docs} {'✅' if all_docs else '❌'}")
    print(f"  Scripts:        {script_count}/{total_scripts} {'✅' if all_scripts else '❌'}")
    print(f"  Data:           {data_count}/{total_data} {'✅' if all_data else '❌'}")
    print(f"  Python:         {'✅' if python_ok else '❌'}")
    print(f"  Dependencies:   {'✅' if deps_ok else '❌'}")
    
    all_ok = all_docs and all_scripts and all_data and python_ok and deps_ok
    
    print("\n" + "="*70)
    if all_ok:
        print("  ✅ ALL CHECKS PASSED - READY FOR TESTING!")
        print("="*70)
        print("""
  🚀 You can now start testing:
  
     python windsurf_test.py
  
  Or read the quick start guide:
  
     START_HERE.md
""")
        return 0
    else:
        print("  ⚠️  SOME CHECKS FAILED")
        print("="*70)
        print("""
  Please fix the issues above before testing.
  
  Common fixes:
  - Install Python 3.8+
  - Install requests: pip install requests
  - Make sure you're in the OmniRoute directory
""")
        return 1

def main():
    """Main verification function."""
    print_header()
    
    doc_count, script_count, data_count, total_docs, total_scripts, total_data = check_files()
    python_ok = check_python()
    deps_ok = check_dependencies()
    
    return print_summary(doc_count, script_count, data_count, total_docs, total_scripts, total_data, python_ok, deps_ok)

if __name__ == "__main__":
    sys.exit(main())
