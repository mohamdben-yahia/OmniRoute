#!/usr/bin/env python3
"""
Windsurf Auth Quick Start — One-Command Setup
==============================================

Automates the entire authentication flow:
1. Check CDP availability
2. Extract tokens
3. Validate authentication
4. Display results

Usage:
    python windsurf_quick_start.py
    python windsurf_quick_start.py --auto-launch  # Launch Windsurf with CDP if needed
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any

from windsurf_runtime_inspector import (
    format_nodeservice_runtime_summary,
    get_nodeservice_inspector_port,
)


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a colored header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def check_cdp_availability(port: int = 9222) -> bool:
    """Check if CDP is available."""
    try:
        response = urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5)
        data = json.loads(response.read())
        return len(data) > 0
    except Exception:
        return False


def check_nodeservice_inspector() -> Optional[int]:
    """Return the live NodeService inspector port when available."""
    return get_nodeservice_inspector_port()


def is_windsurf_running() -> bool:
    """Check if Windsurf process is running."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Windsurf.exe"],
                capture_output=True,
                text=True
            )
            return "Windsurf.exe" in result.stdout
        else:
            result = subprocess.run(
                ["pgrep", "-f", "Windsurf"],
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
    except Exception:
        return False


def stop_windsurf() -> bool:
    """Stop all running Windsurf processes."""
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/IM", "Windsurf.exe", "/F"],
                capture_output=True,
                text=True,
            )
        else:
            subprocess.run(
                ["pkill", "-f", "Windsurf"],
                capture_output=True,
                text=True,
            )

        for _ in range(10):
            if not is_windsurf_running():
                return True
            time.sleep(1)

        return not is_windsurf_running()
    except Exception:
        return False


def launch_windsurf_with_cdp(port: int = 9222) -> bool:
    """Launch Windsurf with CDP enabled."""
    print_info(f"Launching Windsurf with CDP on port {port}...")

    if sys.platform == "win32":
        windsurf_path = r"C:\Users\amine\AppData\Local\Programs\Windsurf\Windsurf.exe"
    elif sys.platform == "darwin":
        windsurf_path = "/Applications/Windsurf.app/Contents/MacOS/Windsurf"
    else:
        windsurf_path = "windsurf"

    if not Path(windsurf_path).exists() and sys.platform == "win32":
        print_error(f"Windsurf not found at: {windsurf_path}")
        return False

    if is_windsurf_running():
        print_warning("Existing Windsurf instance detected; restarting with CDP enabled")
        if not stop_windsurf():
            print_error("Could not stop the existing Windsurf instance")
            return False
        time.sleep(2)

    try:
        subprocess.Popen(
            [windsurf_path, f"--remote-debugging-port={port}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for Windsurf to start
        print_info("Waiting for Windsurf to start...")
        for i in range(30):
            time.sleep(1)
            if check_cdp_availability(port):
                print_success("Windsurf started successfully!")
                return True
            print(f"  Waiting... ({i + 1}/30)", end="\r")

        print_error("Windsurf failed to start within 30 seconds")
        return False

    except Exception as e:
        print_error(f"Failed to launch Windsurf: {e}")
        return False


def extract_tokens(scripts_dir: Path, output_file: Path) -> Optional[Dict[str, Any]]:
    """Extract tokens using windsurf_token_extractor.py."""
    print_info("Extracting tokens via CDP...")

    extractor_script = scripts_dir / "windsurf_token_extractor.py"

    if not extractor_script.exists():
        print_error(f"Token extractor not found: {extractor_script}")
        return None

    try:
        result = subprocess.run(
            [sys.executable, str(extractor_script), "--extract-all", "--output", str(output_file)],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode != 0:
            print_error("Token extraction failed")
            print(f"  Error: {result.stderr[:200]}")
            return None

        if not output_file.exists():
            print_error("Tokens file not created")
            return None

        with open(output_file, "r") as f:
            tokens = json.load(f)

        if not tokens.get("sessionId") or not tokens.get("csrfToken"):
            print_warning("Tokens extracted but incomplete")
            print_info("Make sure Cascade panel is open and active in Windsurf")
            return None

        print_success("Tokens extracted successfully!")
        return tokens

    except subprocess.TimeoutExpired:
        print_error("Token extraction timed out")
        return None
    except Exception as e:
        print_error(f"Token extraction error: {e}")
        return None


def test_authentication(scripts_dir: Path, tokens_file: Path) -> bool:
    """Test authentication using windsurf_authenticated_probe.py."""
    print_info("Testing authentication...")

    probe_script = scripts_dir / "windsurf_authenticated_probe.py"

    if not probe_script.exists():
        print_error(f"Auth probe not found: {probe_script}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(probe_script), "--tokens", str(tokens_file), "--test-start-cascade"],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0 and "✅ AUTHENTICATION SUCCESSFUL" in result.stdout:
            print_success("Authentication test passed!")
            return True
        elif "Status: 200" in result.stdout:
            print_success("Authentication test passed (Status 200)!")
            return True
        else:
            print_error("Authentication test failed")
            print(f"  Output: {result.stdout[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print_error("Authentication test timed out")
        return False
    except Exception as e:
        print_error(f"Authentication test error: {e}")
        return False


def display_results(tokens: Dict[str, Any], auth_success: bool):
    """Display final results."""
    print_header("📊 RESULTS")

    print(f"{Colors.BOLD}Session ID:{Colors.ENDC} {tokens.get('sessionId', 'N/A')[:40]}...")
    print(f"{Colors.BOLD}CSRF Token:{Colors.ENDC} {tokens.get('csrfToken', 'N/A')[:40]}...")
    print(f"{Colors.BOLD}localStorage keys:{Colors.ENDC} {len(tokens.get('localStorage', {}))}")
    print(f"{Colors.BOLD}sessionStorage keys:{Colors.ENDC} {len(tokens.get('sessionStorage', {}))}")
    print(f"{Colors.BOLD}Cookies:{Colors.ENDC} {len(tokens.get('cookies', []))}")
    print(f"{Colors.BOLD}Headers captured:{Colors.ENDC} {len(tokens.get('headers', {}))}")
    print(f"{Colors.BOLD}Timestamp:{Colors.ENDC} {tokens.get('timestamp', 'N/A')}")

    print(f"\n{Colors.BOLD}Authentication Status:{Colors.ENDC}")
    if auth_success:
        print_success("PASSED — Tokens are valid and accepted by the LS")
    else:
        print_error("FAILED — Tokens may be invalid or expired")

    print_header("🚀 NEXT STEPS")

    if auth_success:
        print(f"{Colors.OKGREEN}✅ Authentication is working!{Colors.ENDC}\n")
        print("You can now:")
        print("  1. Use the captured tokens to call the LS directly")
        print("  2. Integrate into your application")
        print("  3. Run the full test suite:")
        print(f"     {Colors.OKCYAN}python windsurf_auth_test_suite.py{Colors.ENDC}")
        print("\nExample usage:")
        print(f"  {Colors.OKCYAN}python windsurf_authenticated_probe.py --tokens tokens.json --use-direct-probe{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠️  Authentication failed{Colors.ENDC}\n")
        print("Troubleshooting steps:")
        print("  1. Open Cascade panel in Windsurf")
        print("  2. Send a test message (e.g., 'hello')")
        print("  3. Re-run this script:")
        print(f"     {Colors.OKCYAN}python windsurf_quick_start.py{Colors.ENDC}")
        print("\nFor detailed debugging:")
        print(f"  {Colors.OKCYAN}python windsurf_auth_test_suite.py{Colors.ENDC}")


def main():
    parser = argparse.ArgumentParser(
        description="Windsurf Auth Quick Start — One-Command Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--auto-launch", action="store_true", help="Auto-launch Windsurf with CDP if not running")
    parser.add_argument("--port", type=int, default=9222, help="CDP port (default: 9222)")
    parser.add_argument("--skip-test", action="store_true", help="Skip authentication test")

    args = parser.parse_args()

    scripts_dir = Path(__file__).parent
    tokens_file = scripts_dir / "tokens.json"

    print_header("🚀 WINDSURF AUTH QUICK START")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scripts dir: {scripts_dir}")
    print(f"Renderer CDP port: {args.port}")

    # Step 1: Check CDP availability
    print_header("Step 1: Checking Runtime Debug Access")

    node_inspector_port = check_nodeservice_inspector()
    if node_inspector_port:
        print_success(f"NodeService inspector detected on port {node_inspector_port}")
        print_info(format_nodeservice_runtime_summary())
    elif check_cdp_availability(args.port):
        print_success(f"Renderer CDP is available on port {args.port}")
    else:
        print_warning("No live Windsurf debug endpoint detected")

        if args.auto_launch:
            if not launch_windsurf_with_cdp(args.port):
                print_error("Auto-launch failed")
                print("\nManual fallback:")
                print("  1. Close all Windsurf windows completely")
                print(f"  2. Run: powershell -ExecutionPolicy Bypass -File launch_windsurf_with_cdp.ps1")
                return 1
        else:
            print_error("Windsurf debug access is required for token extraction")
            print("\nRenderer CDP launch is unreliable in this runtime; prefer a live Windsurf session.")
            if sys.platform == "win32":
                print(f'  & "C:\\Users\\amine\\AppData\\Local\\Programs\\Windsurf\\Windsurf.exe" --remote-debugging-port={args.port}')
            else:
                print(f"  windsurf --remote-debugging-port={args.port}")
            print("\nOr run with --auto-launch to start automatically:")
            print(f"  python {Path(__file__).name} --auto-launch")
            return 1

    # Step 2: Extract tokens
    print_header("Step 2: Extracting Tokens")

    tokens = extract_tokens(scripts_dir, tokens_file)

    if not tokens:
        print_error("Token extraction failed")
        print("\nTroubleshooting:")
        print("  1. Make sure Windsurf is running")
        print("  2. Open a file in Windsurf (not just welcome screen)")
        print("  3. Open the Cascade panel")
        print("  4. Send a test message")
        print("  5. Re-run this script")
        return 1

    # Step 3: Test authentication
    auth_success = False

    if not args.skip_test:
        print_header("Step 3: Testing Authentication")
        auth_success = test_authentication(scripts_dir, tokens_file)
    else:
        print_info("Skipping authentication test (--skip-test)")

    # Step 4: Display results
    display_results(tokens, auth_success)

    return 0 if auth_success or args.skip_test else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}⚠️  Interrupted by user{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n{Colors.FAIL}❌ Unexpected error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
