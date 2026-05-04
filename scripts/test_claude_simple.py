#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Claude Variants Test
============================
Loads environment from .env.windsurf.local and tests Claude variants.
"""

import json
import os
import sys
import time
from pathlib import Path

# Fix encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment from .env.windsurf.local
env_file = Path(__file__).parent.parent / ".env.windsurf.local"
if env_file.exists():
    print(f"Loading environment from {env_file}")
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ[key] = value
            print(f"  Set {key}")
    print()

try:
    from windsurf_direct_probe import start_cascade, send_user_cascade_message
except ImportError as e:
    print(f"ERROR: Failed to import windsurf_direct_probe: {e}")
    sys.exit(1)

# Claude variants to test
CLAUDE_VARIANTS = [
    ("claude-opus-4-7-medium", "Claude Opus 4.7 Medium (CONFIRMED)"),
    ("claude-opus-4-7", "Claude Opus 4.7"),
    ("claude-sonnet-4-6", "Claude Sonnet 4.6"),
    ("claude-haiku-4-5", "Claude Haiku 4.5"),
]

def test_model(model_uid: str, description: str) -> dict:
    """Test a single model."""
    print(f"  {model_uid:30} ... ", end="", flush=True)

    try:
        token = os.environ.get("WINDSURF_DIRECT_KEY", "").strip()
        port = os.environ.get("WINDSURF_LS_PORT", "51834")
        base_url = f"http://127.0.0.1:{port}"

        # Start cascade
        exit_code, request, preview, cascade_response = start_cascade(token, base_url)

        if not cascade_response or cascade_response.get("status") != 200:
            error = cascade_response.get("body", {}).get("message", "unknown") if cascade_response else "no response"
            print(f"FAIL (cascade: {error})")
            return {"model_uid": model_uid, "available": False, "error": f"cascade_failed: {error}"}

        cascade_id = cascade_response.get("cascadeId")
        if not cascade_id:
            print("FAIL (no cascadeId)")
            return {"model_uid": model_uid, "available": False, "error": "no_cascade_id"}

        # Send message with model
        exit_code, request, preview, message_response = send_user_cascade_message(
            token=token,
            cascade_id=cascade_id,
            message="test",
            requested_model_uid=model_uid,
            base_url=base_url,
        )

        if not message_response:
            print("FAIL (no response)")
            return {"model_uid": model_uid, "available": False, "error": "no_response"}

        status = message_response.get("status")

        if status == 200:
            print("SUCCESS!")
            return {
                "model_uid": model_uid,
                "description": description,
                "available": True,
                "status": 200,
            }
        elif status == 500:
            error_body = message_response.get("body", {})
            error_msg = error_body.get("message", "")

            if "unknown model UID" in error_msg or "model not found" in error_msg:
                print("NOT FOUND")
                return {"model_uid": model_uid, "available": False, "error": "not_found"}
            else:
                print(f"ERROR: {error_msg[:40]}")
                return {"model_uid": model_uid, "available": False, "error": error_msg}
        else:
            print(f"STATUS {status}")
            return {"model_uid": model_uid, "available": False, "error": f"status_{status}"}

    except Exception as e:
        print(f"EXCEPTION: {str(e)[:40]}")
        return {"model_uid": model_uid, "available": False, "error": str(e)}


def main():
    """Test Claude variants."""
    print("=" * 80)
    print("Claude Variants Discovery (Simple)")
    print("=" * 80)
    print()

    # Verify environment
    token = os.environ.get("WINDSURF_DIRECT_KEY", "").strip()
    csrf = os.environ.get("WINDSURF_CSRF_TOKEN", "").strip()
    session = os.environ.get("WINDSURF_SESSION_ID", "").strip()
    port = os.environ.get("WINDSURF_LS_PORT", "51834")

    print("Environment check:")
    print(f"  WINDSURF_DIRECT_KEY: {'SET' if token else 'MISSING'}")
    print(f"  WINDSURF_CSRF_TOKEN: {'SET' if csrf else 'MISSING'}")
    print(f"  WINDSURF_SESSION_ID: {'SET' if session else 'MISSING'}")
    print(f"  WINDSURF_LS_PORT: {port}")
    print()

    if not token or not csrf or not session:
        print("ERROR: Missing required environment variables")
        print("Please ensure .env.windsurf.local contains:")
        print("  WINDSURF_DIRECT_KEY")
        print("  WINDSURF_CSRF_TOKEN")
        print("  WINDSURF_SESSION_ID")
        print("  WINDSURF_LS_PORT")
        return 1

    print(f"Testing {len(CLAUDE_VARIANTS)} Claude variants...")
    print("-" * 80)

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_tested": len(CLAUDE_VARIANTS),
        "available": [],
        "not_available": [],
    }

    for model_uid, description in CLAUDE_VARIANTS:
        result = test_model(model_uid, description)

        if result["available"]:
            results["available"].append(result)
        else:
            results["not_available"].append(result)

        time.sleep(0.5)

    print()
    print("=" * 80)
    print("Results")
    print("=" * 80)
    print()

    available_count = len(results["available"])
    print(f"Available: {available_count}/{len(CLAUDE_VARIANTS)}")
    print()

    if results["available"]:
        print("DISCOVERED:")
        for model in results["available"]:
            print(f"  ✓ {model['model_uid']}")
        print()

    # Save results
    output_file = Path(__file__).parent.parent / "windsurf_claude_simple_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Results saved to: {output_file}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
