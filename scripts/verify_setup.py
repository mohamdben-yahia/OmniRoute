#!/usr/bin/env python3
"""
Windsurf Authentication Toolkit — Setup Verification Script

This script verifies that your environment is correctly configured
to use the Windsurf Authentication Toolkit.

Usage:
    python verify_setup.py
    python verify_setup.py --verbose
    python verify_setup.py --fix

Author: OmniRoute Research Team
Version: 1.0.0
Last Updated: 2026-05-02
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from typing import List, Tuple, Dict

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is 3.8 or higher."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)"

def check_dependency(package: str) -> Tuple[bool, str]:
    """Check if a Python package is installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Extract version from pip show output
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':', 1)[1].strip()
                    return True, f"{package} {version}"
            return True, package
        return False, package
    except Exception as e:
        return False, f"{package} (error: {str(e)})"

def check_file_exists(filepath: str) -> Tuple[bool, str]:
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        size = path.stat().st_size
        return True, f"{filepath} ({size} bytes)"
    return False, filepath

def check_windsurf_running() -> Tuple[bool, str]:
    """Check if Windsurf is running."""
    try:
        # Try to find Windsurf process
        if sys.platform == 'win32':
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq Windsurf.exe'],
                capture_output=True,
                text=True,
                timeout=5
            )
            running = 'Windsurf.exe' in result.stdout
        else:
            result = subprocess.run(
                ['pgrep', '-i', 'windsurf'],
                capture_output=True,
                text=True,
                timeout=5
            )
            running = result.returncode == 0
        
        if running:
            return True, "Windsurf is running"
        return False, "Windsurf is not running"
    except Exception as e:
        return False, f"Could not check (error: {str(e)})"

def check_cdp_available() -> Tuple[bool, str]:
    """Check if CDP is available on port 9222."""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 9222))
        sock.close()
        
        if result == 0:
            return True, "CDP available on port 9222"
        return False, "CDP not available on port 9222"
    except Exception as e:
        return False, f"Could not check (error: {str(e)})"

def check_ls_available() -> Tuple[bool, str]:
    """Check if Language Server is available on port 59602."""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 59602))
        sock.close()
        
        if result == 0:
            return True, "LS available on port 59602"
        return False, "LS not available on port 59602"
    except Exception as e:
        return False, f"Could not check (error: {str(e)})"

def check_tokens_file() -> Tuple[bool, str]:
    """Check if tokens.json exists and is valid."""
    try:
        path = Path('tokens.json')
        if not path.exists():
            return False, "tokens.json not found (run token extractor first)"
        
        with open(path, 'r') as f:
            tokens = json.load(f)
        
        if 'sessionId' in tokens and 'csrfToken' in tokens:
            return True, f"tokens.json valid (sessionId: {tokens['sessionId'][:10]}...)"
        return False, "tokens.json invalid (missing sessionId or csrfToken)"
    except Exception as e:
        return False, f"tokens.json error: {str(e)}"

def install_dependency(package: str) -> bool:
    """Install a Python package."""
    try:
        print_info(f"Installing {package}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0
    except Exception as e:
        print_error(f"Failed to install {package}: {str(e)}")
        return False

def main():
    """Main verification function."""
    verbose = '--verbose' in sys.argv
    fix = '--fix' in sys.argv
    
    print_header("Windsurf Authentication Toolkit — Setup Verification")
    
    # Track overall status
    all_checks_passed = True
    
    # 1. Check Python version
    print_info("Checking Python version...")
    success, message = check_python_version()
    if success:
        print_success(message)
    else:
        print_error(message)
        all_checks_passed = False
    
    # 2. Check dependencies
    print_info("\nChecking Python dependencies...")
    dependencies = ['websockets', 'aiohttp']
    missing_deps = []
    
    for dep in dependencies:
        success, message = check_dependency(dep)
        if success:
            print_success(message)
        else:
            print_error(f"{message} not installed")
            missing_deps.append(dep)
            all_checks_passed = False
    
    # Fix missing dependencies if requested
    if fix and missing_deps:
        print_info("\nAttempting to install missing dependencies...")
        for dep in missing_deps:
            if install_dependency(dep):
                print_success(f"Installed {dep}")
            else:
                print_error(f"Failed to install {dep}")
    
    # 3. Check required scripts
    print_info("\nChecking required scripts...")
    scripts = [
        'windsurf_quick_start.py',
        'windsurf_token_extractor.py',
        'windsurf_authenticated_probe.py',
        'windsurf_cdp_inject.py',
        'windsurf_auth_test_suite.py',
        'windsurf_direct_probe.py'
    ]
    
    for script in scripts:
        success, message = check_file_exists(script)
        if success:
            print_success(message)
        else:
            print_error(f"{message} not found")
            all_checks_passed = False
    
    # 4. Check documentation
    print_info("\nChecking documentation...")
    docs = [
        'README.md',
        'CHEAT_SHEET.md',
        'README_AUTH_TOOLKIT.md',
        'WINDSURF_AUTH_FLOW.md',
        'CDP_INJECTION_GUIDE.md'
    ]
    
    for doc in docs:
        success, message = check_file_exists(doc)
        if success:
            print_success(message)
        else:
            print_warning(f"{message} not found")
    
    # 5. Check Windsurf runtime
    print_info("\nChecking Windsurf runtime...")
    
    success, message = check_windsurf_running()
    if success:
        print_success(message)
    else:
        print_warning(message)
        print_info("  → Start Windsurf to enable token extraction")
    
    success, message = check_cdp_available()
    if success:
        print_success(message)
    else:
        print_warning(message)
        print_info("  → Launch Windsurf with: --remote-debugging-port=9222")
    
    success, message = check_ls_available()
    if success:
        print_success(message)
    else:
        print_warning(message)
        print_info("  → LS starts automatically when Windsurf is running")
    
    # 6. Check tokens
    print_info("\nChecking tokens...")
    success, message = check_tokens_file()
    if success:
        print_success(message)
    else:
        print_warning(message)
        print_info("  → Run: python windsurf_token_extractor.py --extract-all")
    
    # 7. Summary
    print_header("Verification Summary")
    
    if all_checks_passed:
        print_success("All critical checks passed! ✨")
        print_info("\nYou're ready to use the toolkit:")
        print_info("  → Quick start: python windsurf_quick_start.py --auto-launch")
        print_info("  → Documentation: README.md")
        print_info("  → Cheat sheet: CHEAT_SHEET.md")
    else:
        print_error("Some checks failed. Please fix the issues above.")
        print_info("\nCommon fixes:")
        print_info("  → Install dependencies: pip install -r requirements.txt")
        print_info("  → Launch Windsurf: Windsurf.exe --remote-debugging-port=9222")
        print_info("  → Extract tokens: python windsurf_token_extractor.py --extract-all")
        
        if fix:
            print_info("\nRun with --fix to automatically install missing dependencies:")
            print_info("  python verify_setup.py --fix")
    
    # 8. Next steps
    print_header("Next Steps")
    print_info("1. Read the documentation: README.md")
    print_info("2. Run quick start: python windsurf_quick_start.py --auto-launch")
    print_info("3. Check the cheat sheet: CHEAT_SHEET.md")
    print_info("4. Explore the toolkit: ls -la")
    
    print()
    
    # Exit with appropriate code
    sys.exit(0 if all_checks_passed else 1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Verification cancelled by user.{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
