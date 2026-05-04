#!/usr/bin/env python3
"""
Windsurf Authentication Token Capture - Optimized Script

This script captures authentication tokens from Windsurf Cascade API requests
using mitmproxy to intercept HTTPS traffic.

Usage:
    mitmdump -s windsurf_token_capture.py --listen-port 8080

Requirements:
    - mitmproxy 12.2.2+ installed
    - CA certificate installed (visit http://mitm.it)
    - Windsurf configured to use proxy

Author: OmniRoute Team
Date: 2026-05-03
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from mitmproxy import http
from mitmproxy import ctx


class WindsurfTokenCapture:
    """Captures authentication tokens from Windsurf API requests."""

    def __init__(self):
        self.output_file = Path("windsurf_captured_tokens.json")
        self.log_file = Path("windsurf_capture_log.txt")
        self.captured_count = 0
        self.target_domains = [
            "server.self-serve.windsurf.com",
            "inference.codeium.com",
            "api.codeium.com",
            "codeium.com"
        ]

        # Initialize log file
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Windsurf Token Capture Log ===\n")
            f.write(f"Started: {datetime.now().isoformat()}\n")
            f.write(f"Target domains: {', '.join(self.target_domains)}\n\n")

        ctx.log.info(f"🚀 Windsurf Token Capture initialized")
        ctx.log.info(f"📝 Logging to: {self.log_file}")
        ctx.log.info(f"💾 Tokens will be saved to: {self.output_file}")

    def request(self, flow: http.HTTPFlow) -> None:
        """Intercept and analyze HTTP requests."""

        # Check if this is a Windsurf API request
        host = flow.request.pretty_host
        if not any(domain in host for domain in self.target_domains):
            return

        self.captured_count += 1
        timestamp = datetime.now().isoformat()

        # Log to console
        ctx.log.info(f"\n{'='*70}")
        ctx.log.info(f"🎯 CAPTURED REQUEST #{self.captured_count}")
        ctx.log.info(f"{'='*70}")
        ctx.log.info(f"🌐 URL: {flow.request.pretty_url}")
        ctx.log.info(f"📅 Time: {timestamp}")
        ctx.log.info(f"🔧 Method: {flow.request.method}")

        # Extract all headers
        headers = dict(flow.request.headers)

        # Look for authentication headers
        auth_headers = {}
        auth_keywords = [
            'authorization', 'auth', 'token', 'bearer',
            'session', 'csrf', 'x-', 'api-key', 'access',
            'cookie'
        ]

        for key, value in headers.items():
            key_lower = key.lower()
            if any(keyword in key_lower for keyword in auth_keywords):
                auth_headers[key] = value
                ctx.log.info(f"🔑 {key}: {value[:50]}{'...' if len(value) > 50 else ''}")

        # Extract cookies separately
        cookies = {}
        if 'cookie' in headers or 'Cookie' in headers:
            cookie_header = headers.get('cookie') or headers.get('Cookie', '')
            for cookie in cookie_header.split(';'):
                if '=' in cookie:
                    name, value = cookie.strip().split('=', 1)
                    cookies[name] = value
                    ctx.log.info(f"🍪 Cookie: {name}={value[:30]}{'...' if len(value) > 30 else ''}")

        # Extract request body if present
        body_preview = None
        if flow.request.content:
            try:
                body_text = flow.request.text
                if body_text:
                    body_preview = body_text[:500]
                    ctx.log.info(f"\n📦 Request Body Preview:")
                    ctx.log.info(body_preview + ("..." if len(body_text) > 500 else ""))
            except Exception as e:
                ctx.log.warn(f"⚠️  Could not decode body: {e}")

        # Prepare capture data
        capture = {
            "captured_at": timestamp,
            "request_number": self.captured_count,
            "url": flow.request.pretty_url,
            "method": flow.request.method,
            "host": host,
            "path": flow.request.path,
            "headers": dict(headers),
            "auth_headers": auth_headers,
            "cookies": cookies,
            "body_preview": body_preview,
            "user_agent": headers.get('user-agent') or headers.get('User-Agent', 'unknown')
        }

        # Save to JSON file (append mode)
        try:
            # Load existing captures
            if self.output_file.exists():
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                    if not isinstance(existing, list):
                        existing = [existing]
            else:
                existing = []

            # Append new capture
            existing.append(capture)

            # Save updated captures
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)

            ctx.log.info(f"✅ Saved capture #{self.captured_count} to {self.output_file}")

        except Exception as e:
            ctx.log.error(f"❌ Failed to save capture: {e}")

        # Append to log file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*70}\n")
                f.write(f"Capture #{self.captured_count} at {timestamp}\n")
                f.write(f"URL: {flow.request.pretty_url}\n")
                f.write(f"Method: {flow.request.method}\n")
                f.write(f"\nAuth Headers:\n")
                for key, value in auth_headers.items():
                    f.write(f"  {key}: {value}\n")
                f.write(f"\nCookies:\n")
                for name, value in cookies.items():
                    f.write(f"  {name}: {value}\n")
                if body_preview:
                    f.write(f"\nBody Preview:\n{body_preview}\n")
                f.write(f"{'='*70}\n")
        except Exception as e:
            ctx.log.error(f"❌ Failed to write to log: {e}")

        ctx.log.info(f"{'='*70}\n")

    def response(self, flow: http.HTTPFlow) -> None:
        """Intercept and analyze HTTP responses."""

        # Only log responses for captured requests
        host = flow.request.pretty_host
        if not any(domain in host for domain in self.target_domains):
            return

        ctx.log.info(f"📥 Response from {host}: {flow.response.status_code} {flow.response.reason}")

        # Log response headers that might contain tokens
        response_headers = dict(flow.response.headers)
        for key, value in response_headers.items():
            key_lower = key.lower()
            if any(keyword in key_lower for keyword in ['set-cookie', 'authorization', 'token', 'session']):
                ctx.log.info(f"🔑 Response {key}: {value[:50]}{'...' if len(value) > 50 else ''}")


# Create addon instance
addons = [WindsurfTokenCapture()]
