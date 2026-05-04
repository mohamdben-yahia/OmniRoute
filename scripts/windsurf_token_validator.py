#!/usr/bin/env python3
"""
Windsurf Token Validator
Tests discovered tokens by making authenticated requests to the Language Server.
"""

import json
import sys
from pathlib import Path
import itertools

try:
    import requests
except ImportError:
    print("❌ Missing requests library. Install with:")
    print("   pip install requests")
    sys.exit(1)


def load_discovered_tokens():
    """Load tokens from the memory searcher output."""
    token_file = Path("windsurf_memory_tokens.json")
    
    if not token_file.exists():
        print("❌ Token file not found. Run windsurf_memory_searcher.py first")
        return None
    
    with open(token_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_token_combination(session_id, csrf_token, base_url="http://localhost:8000"):
    """
    Test a combination of sessionId and csrfToken.
    
    Args:
        session_id: Session ID to test
        csrf_token: CSRF token to test
        base_url: Base URL of the language server
    
    Returns:
        dict with test results
    """
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"sessionId={session_id}",
        "X-CSRF-Token": csrf_token
    }
    
    # Try a simple health check endpoint
    endpoints_to_test = [
        "/health",
        "/api/health",
        "/status",
        "/api/status",
        "/"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code != 404:
                return {
                    "success": True,
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "response": response.text[:500]
                }
        except requests.exceptions.RequestException:
            continue
    
    return {
        "success": False,
        "error": "All endpoints returned 404 or failed"
    }


def find_language_server_port():
    """Find the port where language_server is listening."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-Process -Name language_server_windows_x64 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pid = result.stdout.strip()
            
            # Get ports for this PID
            netstat_result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )
            
            ports = []
            for line in netstat_result.stdout.splitlines():
                if pid in line and "LISTENING" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        addr = parts[1]
                        if "127.0.0.1:" in addr or "0.0.0.0:" in addr:
                            port = addr.split(":")[-1]
                            if port.isdigit():
                                ports.append(int(port))
            
            return ports
    except Exception as e:
        print(f"Error finding language server port: {e}")
    
    return []


def main():
    print("=" * 70)
    print("Windsurf Token Validator")
    print("=" * 70)
    print()
    
    # Load discovered tokens
    print("Step 1: Loading discovered tokens...")
    tokens = load_discovered_tokens()
    
    if not tokens:
        return 1
    
    session_ids = tokens.get("sessionId_candidates", [])
    csrf_tokens = tokens.get("csrfToken_candidates", [])
    
    print(f"✅ Loaded {len(session_ids)} session ID candidates")
    print(f"✅ Loaded {len(csrf_tokens)} CSRF token candidates")
    print()
    
    # Find language server ports
    print("Step 2: Finding language server ports...")
    ports = find_language_server_port()
    
    if not ports:
        print("⚠️  Could not auto-detect ports, using defaults")
        ports = [8000, 3000, 51497, 51501]
    else:
        print(f"✅ Found ports: {ports}")
    
    print()
    
    # Test combinations
    print("Step 3: Testing token combinations...")
    print(f"   Testing {len(session_ids)} × {len(csrf_tokens)} = {len(session_ids) * len(csrf_tokens)} combinations")
    print()
    
    successful_combinations = []
    
    for port in ports:
        print(f"🔍 Testing port {port}...")
        
        for session_id, csrf_token in itertools.product(session_ids[:5], csrf_tokens[:5]):
            print(f"   Trying: sessionId={session_id[:20]}... csrf={csrf_token[:20]}...")
            
            result = test_token_combination(session_id, csrf_token, f"http://localhost:{port}")
            
            if result["success"]:
                print(f"   ✅ SUCCESS!")
                print(f"      Endpoint: {result['endpoint']}")
                print(f"      Status: {result['status_code']}")
                print(f"      Response: {result['response'][:100]}")
                
                successful_combinations.append({
                    "port": port,
                    "sessionId": session_id,
                    "csrfToken": csrf_token,
                    "result": result
                })
        
        print()
    
    # Summary
    print("=" * 70)
    print("📊 VALIDATION RESULTS")
    print("=" * 70)
    print()
    
    if successful_combinations:
        print(f"✅ Found {len(successful_combinations)} working token combination(s)!")
        print()
        
        for i, combo in enumerate(successful_combinations, 1):
            print(f"Combination {i}:")
            print(f"  Port: {combo['port']}")
            print(f"  Session ID: {combo['sessionId']}")
            print(f"  CSRF Token: {combo['csrfToken']}")
            print(f"  Endpoint: {combo['result']['endpoint']}")
            print()
        
        # Save successful combinations
        output_file = Path("windsurf_valid_tokens.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(successful_combinations, f, indent=2)
        
        print(f"✅ Valid tokens saved to: {output_file}")
    else:
        print("❌ No working token combinations found")
        print()
        print("💡 Possible reasons:")
        print("   1. Language server not running on tested ports")
        print("   2. Tokens are not the correct ones")
        print("   3. Tokens have expired")
        print("   4. Different authentication mechanism")
        print()
        print("💡 Next steps:")
        print("   1. Send a Cascade message to refresh tokens")
        print("   2. Run windsurf_memory_searcher.py again")
        print("   3. Try HTTP proxy interception (mitmproxy)")
    
    return 0 if successful_combinations else 1


if __name__ == "__main__":
    sys.exit(main())
