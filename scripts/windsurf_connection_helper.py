#!/usr/bin/env python3
"""
Windsurf Connection Helper - Interactive tool to configure Windsurf routing.

This tool:
1. Checks Windsurf health (port, epoch, PID)
2. If alive, prompts user for CSRF token
3. Saves configuration for OmniRoute routing

Usage:
    python windsurf_connection_helper.py

Interactive prompts:
    - Detects Windsurf automatically
    - Asks for CSRF token (from browser DevTools or Fiddler)
    - Saves to windsurf_config.json
"""

import json
import pathlib
import sys
from typing import Any

# Import health check function
try:
    from windsurf_health_check import windsurf_health_check
except ImportError:
    print("Error: windsurf_health_check.py not found in same directory")
    sys.exit(1)


def get_config_path() -> pathlib.Path:
    """Get path to Windsurf configuration file."""
    return pathlib.Path(__file__).parent / "windsurf_config.json"


def load_existing_config() -> dict[str, Any]:
    """Load existing configuration if it exists."""
    config_path = get_config_path()
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    config_path = get_config_path()
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"\n✓ Configuration saved to: {config_path}")


def prompt_csrf_token() -> str:
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
    print("=" * 70)

    while True:
        token = input("\nEnter CSRF token (or 'skip' to save without token): ").strip()

        if token.lower() == "skip":
            return ""

        if not token:
            print("❌ Token cannot be empty. Try again or type 'skip'.")
            continue

        # Basic validation: UUID format
        if len(token) == 36 and token.count("-") == 4:
            return token

        print("⚠️  Token format looks unusual (expected UUID format)")
        confirm = input("Use this token anyway? (y/n): ").strip().lower()
        if confirm == "y":
            return token


def main() -> None:
    """Main entry point."""
    print("=" * 70)
    print("Windsurf Connection Helper")
    print("=" * 70)

    # Step 1: Check Windsurf health
    print("\n[1/3] Checking Windsurf health...")
    health = windsurf_health_check()

    print(f"\nStatus: {health['status'].upper()}")
    print(f"Port: {health['port']}")
    print(f"Epoch: {health['epoch']}")
    print(f"PID: {health['pid']}")
    print(f"Message: {health['message']}")

    if health["status"] == "dead":
        print("\n❌ Windsurf is not running or inactive.")
        print("   Please start Windsurf and try again.")
        sys.exit(1)

    if health["status"] == "stale":
        print("\n⚠️  Windsurf may be idle (no recent activity).")
        proceed = input("   Continue anyway? (y/n): ").strip().lower()
        if proceed != "y":
            sys.exit(0)

    # Step 2: Load existing config
    print("\n[2/3] Loading existing configuration...")
    config = load_existing_config()

    if config:
        print(f"   Found existing config with {len(config)} entries")
        if "csrfToken" in config and config["csrfToken"]:
            print(f"   Existing CSRF token: {config['csrfToken'][:8]}...{config['csrfToken'][-8:]}")
            update = input("   Update CSRF token? (y/n): ").strip().lower()
            if update != "y":
                print("\n✓ Keeping existing configuration")
                sys.exit(0)

    # Step 3: Prompt for CSRF token
    print("\n[3/3] Configuring CSRF token...")
    csrf_token = prompt_csrf_token()

    # Update config
    config.update({
        "port": health["port"],
        "epoch": health["epoch"],
        "pid": health["pid"],
        "csrfToken": csrf_token if csrf_token else None,
        "lastUpdated": health["lastActivity"],
        "status": health["status"]
    })

    # Save config
    save_config(config)

    # Summary
    print("\n" + "=" * 70)
    print("Configuration Summary")
    print("=" * 70)
    print(f"Port: {config['port']}")
    print(f"Epoch: {config['epoch']}")
    print(f"CSRF Token: {'✓ Configured' if config['csrfToken'] else '✗ Not configured'}")
    print(f"Status: {config['status']}")
    print("=" * 70)

    if not config["csrfToken"]:
        print("\n⚠️  Warning: CSRF token not configured.")
        print("   OmniRoute will not be able to route requests to Windsurf.")
        print("   Run this tool again to add the token.")

    print("\n✓ Setup complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
