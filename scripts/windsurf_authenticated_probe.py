#!/usr/bin/env python3
"""
Windsurf Authenticated Probe — Use Captured Tokens
===================================================

This script extends windsurf_direct_probe.py to use tokens captured
via windsurf_token_extractor.py, bypassing the 401 authentication issue.

Usage:
    # Extract tokens first
    python windsurf_token_extractor.py --extract-all --output tokens.json
    
    # Use captured tokens
    python windsurf_authenticated_probe.py --tokens tokens.json --test-start-cascade
    python windsurf_authenticated_probe.py --session-id "abc123" --csrf-token "xyz789" --test-start-cascade
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional


def load_captured_tokens(tokens_path: str) -> Dict[str, Any]:
    """Load tokens from windsurf_token_extractor.py output."""
    path = Path(tokens_path)
    if not path.exists():
        raise FileNotFoundError(f"Tokens file not found: {tokens_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        tokens = json.load(f)
    
    return tokens


def extract_session_credentials(tokens: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Extract sessionId and csrfToken from captured tokens."""
    session_id = tokens.get("sessionId")
    csrf_token = tokens.get("csrfToken")
    
    # Fallback: check headers
    if not session_id or not csrf_token:
        headers = tokens.get("headers", {})
        for key, value in headers.items():
            if "session" in key.lower() and not session_id:
                session_id = value
            if "csrf" in key.lower() and not csrf_token:
                csrf_token = value
    
    # Fallback: check localStorage
    if not session_id or not csrf_token:
        local_storage = tokens.get("localStorage", {})
        for key, value in local_storage.items():
            if "session" in key.lower() and not session_id:
                session_id = value
            if "csrf" in key.lower() and not csrf_token:
                csrf_token = value
    
    # Fallback: check cookies
    if not session_id or not csrf_token:
        cookies = tokens.get("cookies", [])
        for cookie in cookies:
            name = cookie.get("name", "")
            value = cookie.get("value", "")
            if "session" in name.lower() and not session_id:
                session_id = value
            if "csrf" in name.lower() and not csrf_token:
                csrf_token = value
    
    return {
        "sessionId": session_id,
        "csrfToken": csrf_token
    }


def test_start_cascade(session_id: str, csrf_token: str, ls_port: int = 59602) -> Dict[str, Any]:
    """
    Test StartCascade RPC with captured tokens.
    
    This should return 200 instead of 401 if tokens are valid.
    """
    url = f"http://127.0.0.1:{ls_port}/exa.cascade_pb.CascadeService/StartCascade"
    
    # Build minimal protobuf payload
    # Field 1: metadata (contains sessionId as apiKey)
    # Field 4: source (int64, value=1)
    
    # Simplified protobuf encoding (field 1 = metadata message)
    # For a real implementation, use proper protobuf encoding
    # Here we'll use a minimal payload that matches the expected structure
    
    # This is a placeholder - in production, use proper protobuf library
    body = b""  # Minimal empty body for testing
    
    headers = {
        "Content-Type": "application/proto",
        "Connect-Protocol-Version": "1",
        "Accept": "application/proto, application/json",
        "User-Agent": "connect-go/1.17.0 (go1.23.4)",
        "Accept-Encoding": "identity",
        "Connect-Accept-Encoding": "gzip",
        "host": f"q.localhost:{ls_port}",
        "x-codeium-csrf-token": csrf_token
    }
    
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status = response.status
            body = response.read()
            
            return {
                "status": status,
                "success": True,
                "body_length": len(body),
                "headers": dict(response.headers),
                "message": "✅ Authentication successful!" if status == 200 else f"Status: {status}"
            }
    
    except urllib.error.HTTPError as e:
        return {
            "status": e.code,
            "success": False,
            "reason": e.reason,
            "body": e.read().decode("utf-8", errors="replace"),
            "message": f"❌ HTTP {e.code}: {e.reason}"
        }
    
    except Exception as e:
        return {
            "status": None,
            "success": False,
            "error": str(e),
            "message": f"❌ Request failed: {e}"
        }


def test_with_windsurf_direct_probe(session_id: str, csrf_token: str, ls_port: int = 59602) -> Dict[str, Any]:
    """
    Use windsurf_direct_probe.py with captured tokens.
    
    Sets environment variables and calls the original script.
    """
    import os
    import subprocess
    
    env = os.environ.copy()
    env["WINDSURF_SESSION_ID"] = session_id
    env["WINDSURF_CSRF_TOKEN"] = csrf_token
    env["WINDSURF_LANGUAGE_SERVER_URL"] = f"http://127.0.0.1:{ls_port}"
    env["WINDSURF_LS_HOST_HEADER"] = f"q.localhost:{ls_port}"
    env["WINDSURF_PROBE_MODE"] = "ls_emulator"
    env["WINDSURF_CHAT_TEXT"] = "hello from authenticated probe"
    
    # Get path to windsurf_direct_probe.py
    probe_script = Path(__file__).parent / "windsurf_direct_probe.py"
    
    if not probe_script.exists():
        return {
            "success": False,
            "error": f"windsurf_direct_probe.py not found at {probe_script}"
        }
    
    try:
        result = subprocess.run(
            [sys.executable, str(probe_script)],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Try to parse JSON output
        try:
            output = json.loads(result.stdout)
        except:
            output = {"raw_stdout": result.stdout, "raw_stderr": result.stderr}
        
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "output": output,
            "stderr": result.stderr if result.stderr else None
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Timeout after 30 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description="Test Windsurf LS with captured authentication tokens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use tokens from file
  python windsurf_authenticated_probe.py --tokens tokens.json --test-start-cascade
  
  # Use explicit tokens
  python windsurf_authenticated_probe.py \\
    --session-id "observed-session-abc" \\
    --csrf-token "3a1d0e5e-db26-4abe-b2f9-41704544534e" \\
    --test-start-cascade
  
  # Use with windsurf_direct_probe.py
  python windsurf_authenticated_probe.py --tokens tokens.json --use-direct-probe
        """
    )
    
    parser.add_argument("--tokens", help="Path to tokens JSON file (from windsurf_token_extractor.py)")
    parser.add_argument("--session-id", help="Session ID (overrides tokens file)")
    parser.add_argument("--csrf-token", help="CSRF token (overrides tokens file)")
    parser.add_argument("--ls-port", type=int, default=59602, help="Language server port (default: 59602)")
    parser.add_argument("--test-start-cascade", action="store_true", help="Test StartCascade RPC")
    parser.add_argument("--use-direct-probe", action="store_true", help="Use windsurf_direct_probe.py with tokens")
    
    args = parser.parse_args()
    
    # Resolve credentials
    session_id = args.session_id
    csrf_token = args.csrf_token
    
    if args.tokens:
        print(f"📦 Loading tokens from: {args.tokens}")
        tokens = load_captured_tokens(args.tokens)
        creds = extract_session_credentials(tokens)
        
        if not session_id:
            session_id = creds["sessionId"]
        if not csrf_token:
            csrf_token = creds["csrfToken"]
        
        print(f"✔ Extracted credentials:")
        print(f"  Session ID: {session_id or '❌ NOT FOUND'}")
        print(f"  CSRF Token: {csrf_token or '❌ NOT FOUND'}")
    
    if not session_id or not csrf_token:
        print("\n❌ Missing credentials!")
        print("\n💡 Options:")
        print("  1. Run: python windsurf_token_extractor.py --extract-all --output tokens.json")
        print("  2. Then: python windsurf_authenticated_probe.py --tokens tokens.json --test-start-cascade")
        print("  3. Or provide explicit tokens with --session-id and --csrf-token")
        return 1
    
    print("\n" + "=" * 70)
    print("🔐 AUTHENTICATED PROBE")
    print("=" * 70)
    print(f"Session ID: {session_id[:20]}...")
    print(f"CSRF Token: {csrf_token[:20]}...")
    print(f"LS Port: {args.ls_port}")
    
    # Run tests
    if args.test_start_cascade:
        print("\n" + "=" * 70)
        print("🧪 Testing StartCascade RPC")
        print("=" * 70)
        
        result = test_start_cascade(session_id, csrf_token, args.ls_port)
        
        print(f"\nStatus: {result.get('status')}")
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        
        if result.get("success"):
            print("\n✅ AUTHENTICATION SUCCESSFUL!")
            print("The captured tokens are valid and accepted by the LS.")
        else:
            print("\n❌ AUTHENTICATION FAILED")
            print("Possible reasons:")
            print("  1. Tokens expired or invalid")
            print("  2. Session not active")
            print("  3. LS port incorrect")
            print("  4. Protobuf payload malformed")
        
        print("\n📋 Full result:")
        print(json.dumps(result, indent=2))
    
    if args.use_direct_probe:
        print("\n" + "=" * 70)
        print("🔧 Using windsurf_direct_probe.py")
        print("=" * 70)
        
        result = test_with_windsurf_direct_probe(session_id, csrf_token, args.ls_port)
        
        print(f"\nSuccess: {result.get('success')}")
        print(f"Exit Code: {result.get('exit_code')}")
        
        if result.get("success"):
            print("\n✅ PROBE SUCCESSFUL!")
        else:
            print("\n❌ PROBE FAILED")
        
        print("\n📋 Full result:")
        print(json.dumps(result, indent=2))
    
    if not args.test_start_cascade and not args.use_direct_probe:
        print("\n💡 No test specified. Use --test-start-cascade or --use-direct-probe")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
