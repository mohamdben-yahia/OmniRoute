#!/usr/bin/env python3
"""
Windsurf MITM Token Capture Script

This script uses mitmproxy to intercept HTTPS traffic from Windsurf
and extract authentication tokens from Cascade API requests.

Requirements:
    pip install mitmproxy

Usage:
    1. Run this script: python windsurf_mitm_capture.py
    2. Configure Windsurf to use proxy (see instructions below)
    3. Send a Cascade message in Windsurf
    4. Script will capture and save auth tokens

Author: Investigation Team
Date: 2026-05-03
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from mitmproxy import http
from mitmproxy.tools.main import mitmdump


class WindsurfTokenCapture:
    """Captures authentication tokens from Windsurf API requests."""
    
    def __init__(self, output_file="windsurf_tokens.json"):
        self.output_file = Path(output_file)
        self.captured_tokens = []
        self.target_domains = [
            "server.self-serve.windsurf.com",
            "inference.codeium.com",
            "api.codeium.com"
        ]
        
    def request(self, flow: http.HTTPFlow) -> None:
        """Intercept and analyze HTTP requests."""
        
        # Check if this is a Windsurf API request
        if not any(domain in flow.request.pretty_host for domain in self.target_domains):
            return
            
        print(f"\n{'='*70}")
        print(f"🎯 Captured Request to: {flow.request.pretty_url}")
        print(f"{'='*70}")
        
        # Extract all headers
        headers = dict(flow.request.headers)
        
        # Look for authentication headers
        auth_headers = {}
        auth_keywords = [
            'authorization', 'auth', 'token', 'bearer',
            'session', 'csrf', 'x-', 'api-key', 'access'
        ]
        
        for key, value in headers.items():
            key_lower = key.lower()
            if any(keyword in key_lower for keyword in auth_keywords):
                auth_headers[key] = value
                print(f"🔑 {key}: {value}")
        
        # Extract request body if present
        body = None
        if flow.request.content:
            try:
                body = flow.request.text
                if body:
                    print(f"\n📦 Request Body Preview:")
                    print(body[:500] + ("..." if len(body) > 500 else ""))
            except Exception as e:
                print(f"⚠️  Could not decode body: {e}")
        
        # Save captured data
        capture = {
            "timestamp": datetime.now().isoformat(),
            "url": flow.request.pretty_url,
            "method": flow.request.method,
            "host": flow.request.pretty_host,
            "path": flow.request.path,
            "headers": dict(headers),
            "auth_headers": auth_headers,
            "body_preview": body[:1000] if body else None,
            "user_agent": headers.get("User-Agent", ""),
        }
        
        self.captured_tokens.append(capture)
        self._save_tokens()
        
        print(f"\n✅ Saved to {self.output_file}")
        print(f"📊 Total captures: {len(self.captured_tokens)}")
        
    def response(self, flow: http.HTTPFlow) -> None:
        """Intercept and analyze HTTP responses."""
        
        if not any(domain in flow.request.pretty_host for domain in self.target_domains):
            return
            
        print(f"\n📥 Response Status: {flow.response.status_code}")
        
        # Extract response headers
        response_headers = dict(flow.response.headers)
        
        # Look for auth-related response headers
        for key, value in response_headers.items():
            key_lower = key.lower()
            if any(keyword in key_lower for keyword in ['token', 'session', 'auth', 'csrf']):
                print(f"🔑 Response {key}: {value}")
        
        # Try to parse response body
        if flow.response.content:
            try:
                body = flow.response.text
                if body and len(body) < 2000:
                    print(f"\n📦 Response Body:")
                    print(body)
            except Exception as e:
                print(f"⚠️  Could not decode response: {e}")
    
    def _save_tokens(self):
        """Save captured tokens to JSON file."""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.captured_tokens, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving tokens: {e}")


def main():
    """Main entry point."""
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           Windsurf MITM Token Capture Script                    ║
╚══════════════════════════════════════════════════════════════════╝

This script will intercept HTTPS traffic from Windsurf to capture
authentication tokens.

📋 Setup Instructions:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Install mitmproxy CA certificate:
   - This script will start mitmproxy on port 8080
   - Open http://mitm.it in your browser
   - Download and install the certificate for your OS

2. Configure Windsurf to use the proxy:
   
   Option A - Environment Variables (Recommended):
   ┌────────────────────────────────────────────────────────┐
   │ # PowerShell:                                          │
   │ $env:HTTP_PROXY="http://127.0.0.1:8080"               │
   │ $env:HTTPS_PROXY="http://127.0.0.1:8080"              │
   │                                                        │
   │ # Then launch Windsurf from the same terminal:        │
   │ & "C:\\Program Files\\Windsurf\\Windsurf.exe"          │
   └────────────────────────────────────────────────────────┘
   
   Option B - System Proxy Settings:
   ┌────────────────────────────────────────────────────────┐
   │ Windows Settings → Network & Internet → Proxy          │
   │ Manual proxy setup:                                    │
   │   Address: 127.0.0.1                                   │
   │   Port: 8080                                           │
   └────────────────────────────────────────────────────────┘

3. Send a Cascade message in Windsurf
   - Open Windsurf
   - Send any message to Cascade
   - This script will capture the auth tokens

4. Check the output:
   - Tokens will be saved to: windsurf_tokens.json
   - Real-time output will show captured requests

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  IMPORTANT NOTES:
   - You MUST install the mitmproxy CA certificate first
   - Without the cert, HTTPS interception will fail
   - Press Ctrl+C to stop capturing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Starting mitmproxy on port 8080...
Waiting for Windsurf traffic...

""")
    
    # Create capture instance
    capture = WindsurfTokenCapture()
    
    # Start mitmproxy with our addon
    try:
        sys.argv = [
            'mitmdump',
            '--listen-port', '8080',
            '--ssl-insecure',  # Allow self-signed certs
            '--set', 'stream_large_bodies=1m',  # Stream large bodies
        ]
        
        from mitmproxy.tools import main
        main.mitmdump([
            '--listen-port', '8080',
            '--ssl-insecure',
            '-s', __file__,  # Load this script as addon
        ])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping capture...")
        print(f"✅ Captured {len(capture.captured_tokens)} requests")
        print(f"📁 Tokens saved to: {capture.output_file.absolute()}")
        
        if capture.captured_tokens:
            print("\n" + "="*70)
            print("📊 CAPTURE SUMMARY")
            print("="*70)
            
            for i, token in enumerate(capture.captured_tokens, 1):
                print(f"\n{i}. {token['method']} {token['url']}")
                if token['auth_headers']:
                    print("   Auth Headers:")
                    for key, value in token['auth_headers'].items():
                        print(f"     - {key}: {value[:50]}...")
        else:
            print("\n⚠️  No tokens captured. Make sure:")
            print("   1. mitmproxy CA certificate is installed")
            print("   2. Windsurf is configured to use the proxy")
            print("   3. You sent a Cascade message in Windsurf")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


# mitmproxy addon interface
addons = [WindsurfTokenCapture()]


if __name__ == "__main__":
    main()
