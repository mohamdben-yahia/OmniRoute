#!/usr/bin/env python3
"""
Windsurf Connection Helper - Interactive tool to configure Windsurf routing (Hybrid version).

This tool:
1. Checks Windsurf health (port, epoch, PID) via passive observation
2. Prompts user for CSRF token and Language Server port
3. Validates configuration via active API test
4. Saves unified configuration for OmniRoute routing

Usage:
    python windsurf_connection_helper_hybrid.py

Interactive prompts:
    - Detects Windsurf automatically (passive)
    - Asks for CSRF token (from browser DevTools or Fiddler)
    - Asks for Language Server port (usually 59455)
    - Validates via active API test
    - Saves to windsurf_config.json
"""

import sys
from typing import Any

# Import required modules
try:
    from windsurf_health_check import windsurf_health_check
except ImportError:
    print("Error: windsurf_health_check.py not found in same directory")
    sys.exit(1)

try:
    from windsurf_unified_config import WindsurfConfig
except ImportError:
    print("Error: windsurf_unified_config.py not found in same directory")
    sys.exit(1)

try:
    from windsurf_api_validator import validate_windsurf_api
except ImportError:
    print("Warning: windsurf_api_validator.py not found - API validation will be skipped")
    validate_windsurf_api = None


def prompt_csrf_token(existing_token: str = None) -> str:
    """Prompt user for CSRF token with instructions."""
    print("\n" + "=" * 70)
    print("CSRF Token Required")
    print("=" * 70)
    print("\nTo get your Windsurf CSRF token:")
    print("  1. Open Windsurf and start a Cascade chat")
    print("  2. Open Fiddler/Charles/Browser DevTools Network tab")
    print("  3. Submit a message in Cascade")
    print("  4. Find the POST request to:")
    print("     https://server.self-serve.windsurf.com/api/v1/cascade/...")
    print("  5. Copy the 'x-csrf-token' or 'csrf-token' header value")
    print("\nExample token format: a07dae5d-afc8-4fd9-839e-b505412f481b")

    if existing_token:
        print(f"\nExisting token: {existing_token[:8]}...{existing_token[-8:]}")

    print("=" * 70)

    while True:
        token = input("\nEnter CSRF token (or 'skip' to save without token): ").strip()

        if token.lower() == "skip":
            return ""

        if not token:
            print("[X] Token cannot be empty. Try again or type 'skip'.")
            continue

        # Basic validation: UUID format
        if len(token) == 36 and token.count("-") == 4:
            return token

        print("[!] Token format looks unusual (expected UUID format)")
        confirm = input("Use this token anyway? (y/n): ").strip().lower()
        if confirm == "y":
            return token


def prompt_language_server_port(existing_port: int = None) -> int:
    """Prompt user for Language Server port."""
    print("\n" + "=" * 70)
    print("Language Server Port")
    print("=" * 70)
    print("\nThe Language Server port is used for active API validation.")
    print("This is usually 59455 but may vary.")
    print("\nTo find the port:")
    print("  1. Open Windsurf DevTools (Help > Toggle Developer Tools)")
    print("  2. Look for 'Language Server' in console logs")
    print("  3. Or check network requests to localhost")

    if existing_port:
        print(f"\nExisting port: {existing_port}")

    print("=" * 70)

    while True:
        default = existing_port or 59455
        port_input = input(f"\nEnter Language Server port (default: {default}): ").strip()

        if not port_input:
            return default

        try:
            port = int(port_input)
            if 1024 <= port <= 65535:
                return port
            else:
                print("[X] Port must be between 1024 and 65535")
        except ValueError:
            print("[X] Invalid port number")


def main() -> None:
    """Main entry point."""
    print("=" * 70)
    print("Windsurf Connection Helper (Hybrid)")
    print("=" * 70)

    # Initialize config manager
    config = WindsurfConfig()

    # Step 1: Check Windsurf health (passive)
    print("\n[1/5] Checking Windsurf health (passive observation)...")
    health = windsurf_health_check()

    print(f"\nStatus: {health['status'].upper()}")
    print(f"Extension Server Port: {health['port']}")
    print(f"Epoch: {health['epoch']}")
    print(f"PID: {health['pid']}")
    print(f"Message: {health['message']}")

    if health["status"] == "dead":
        print("\n[X] Windsurf is not running or inactive.")
        print("   Please start Windsurf and try again.")
        sys.exit(1)

    if health["status"] == "stale":
        print("\n[!] Windsurf may be idle (no recent activity).")
        proceed = input("   Continue anyway? (y/n): ").strip().lower()
        if proceed != "y":
            sys.exit(0)

    # Update config from health check
    config.update_from_health(health)

    # Step 2: Load existing configuration
    print("\n[2/5] Loading existing configuration...")
    summary = config.get_summary()

    if summary["csrfConfigured"]:
        print(f"   Existing CSRF token: {config.get('csrfToken')[:8]}...{config.get('csrfToken')[-8:]}")
        update = input("   Update CSRF token? (y/n): ").strip().lower()
        if update != "y":
            print("\n[OK] Keeping existing CSRF token")
        else:
            csrf_token = prompt_csrf_token(config.get("csrfToken"))
            if csrf_token:
                config.set_csrf_token(csrf_token)
    else:
        # Step 3: Prompt for CSRF token
        print("\n[3/5] Configuring CSRF token...")
        csrf_token = prompt_csrf_token()

        if csrf_token:
            config.set_csrf_token(csrf_token)
        else:
            print("\n[!] Warning: CSRF token not configured.")

    # Step 4: Prompt for Language Server port
    print("\n[4/5] Configuring Language Server port...")
    ls_port = prompt_language_server_port(config.get("languageServerPort"))
    config.set_language_server_port(ls_port)

    # Step 5: Active API validation (if validator available and token configured)
    if validate_windsurf_api and config.get("csrfToken"):
        print("\n[5/5] Validating configuration (active API test)...")
        print("   This will make a test request to Windsurf API...")

        try:
            validation = validate_windsurf_api(
                port=ls_port,
                csrf_token=config.get("csrfToken"),
                timeout=10.0,
                test_message=True,
                test_model=False
            )

            config.update_from_validation(validation, ls_port)

            if validation["valid"]:
                print("\n[OK] API validation successful!")
                print(f"   StartCascade: PASS")
                print(f"   SendMessage: PASS")
                if validation.get("cascadeId"):
                    print(f"   Cascade ID: {validation['cascadeId']}")
            else:
                print("\n[X] API validation failed!")
                print("   Errors:")
                for error in validation["errors"]:
                    print(f"     - {error}")
                print("\n   Configuration saved but may not work correctly.")
                print("   Please verify CSRF token and Language Server port.")

        except Exception as e:
            print(f"\n[X] API validation error: {e}")
            print("   Configuration saved but not validated.")
    else:
        print("\n[5/5] Skipping API validation")
        if not validate_windsurf_api:
            print("   (windsurf_api_validator.py not available)")
        elif not config.get("csrfToken"):
            print("   (CSRF token not configured)")

    # Summary
    print("\n" + "=" * 70)
    print("Configuration Summary")
    print("=" * 70)
    summary = config.get_summary()
    print(f"Extension Server Port: {summary['extensionServerPort']}")
    print(f"Language Server Port: {summary['languageServerPort']}")
    print(f"Epoch: {summary['epoch']}")
    print(f"CSRF Token: {'[OK] Configured' if summary['csrfConfigured'] else '[X] Not configured'}")
    print(f"Status: {summary['status']}")
    print(f"Last Validation: {summary['lastValidation'] or 'Never'}")
    print(f"Validation Result: {summary['lastValidationResult'] or 'N/A'}")
    print(f"Is Valid: {'[OK] Yes' if summary['isValid'] else '[X] No'}")
    print("=" * 70)

    if not summary["csrfConfigured"]:
        print("\n[!] Warning: CSRF token not configured.")
        print("   OmniRoute will not be able to route requests to Windsurf.")
        print("   Run this tool again to add the token.")
    elif not summary["isValid"]:
        print("\n[!] Warning: Configuration is not valid.")
        print("   Please check the errors above and try again.")
    else:
        print("\n[OK] Setup complete! Configuration is valid and ready for use.")

    print(f"\nConfig file: {config.config_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[X] Cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[X] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
