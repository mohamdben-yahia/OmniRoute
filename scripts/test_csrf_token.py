#!/usr/bin/env python3
"""
Test CSRF Token with Windsurf Language Server
Tests various protocols and endpoints with the discovered CSRF token.
"""

import asyncio
import json
import sys
from pathlib import Path

try:
    import websockets
    import aiohttp
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("   pip install websockets aiohttp")
    sys.exit(1)


async def test_http_endpoints(csrf_token, base_url="http://127.0.0.1:51497"):
    """Test HTTP endpoints with CSRF token."""
    print("=" * 70)
    print("Testing HTTP Endpoints")
    print("=" * 70)
    
    headers = {
        'X-CSRF-Token': csrf_token,
        'Content-Type': 'application/json',
        'User-Agent': 'Windsurf-Client'
    }
    
    endpoints = [
        ('GET', '/'),
        ('GET', '/health'),
        ('GET', '/status'),
        ('GET', '/api'),
        ('GET', '/v1'),
        ('POST', '/', {'method': 'ping'}),
        ('POST', '/', {'jsonrpc': '2.0', 'method': 'ping', 'id': 1}),
        ('POST', '/rpc', {'jsonrpc': '2.0', 'method': 'initialize', 'id': 1}),
    ]
    
    async with aiohttp.ClientSession() as session:
        for method, path, *body_args in endpoints:
            url = f"{base_url}{path}"
            body = body_args[0] if body_args else None
            
            try:
                if method == 'GET':
                    async with session.get(url, headers=headers, timeout=5) as resp:
                        print(f"\n✓ {method} {path}")
                        print(f"  Status: {resp.status}")
                        if resp.status == 200:
                            text = await resp.text()
                            print(f"  Response: {text[:200]}")
                else:
                    async with session.post(url, headers=headers, json=body, timeout=5) as resp:
                        print(f"\n✓ {method} {path}")
                        print(f"  Status: {resp.status}")
                        if resp.status == 200:
                            text = await resp.text()
                            print(f"  Response: {text[:200]}")
            except asyncio.TimeoutError:
                print(f"\n✗ {method} {path} - Timeout")
            except Exception as e:
                print(f"\n✗ {method} {path} - {type(e).__name__}: {str(e)[:100]}")


async def test_websocket_connection(csrf_token, ws_url="ws://127.0.0.1:51497"):
    """Test WebSocket connection with CSRF token."""
    print("\n" + "=" * 70)
    print("Testing WebSocket Connection")
    print("=" * 70)
    
    headers = {
        'X-CSRF-Token': csrf_token,
        'User-Agent': 'Windsurf-Client'
    }
    
    try:
        async with websockets.connect(ws_url, extra_headers=headers, timeout=5) as ws:
            print(f"✅ WebSocket connected to {ws_url}")
            
            # Try sending a ping
            ping_msg = json.dumps({
                'jsonrpc': '2.0',
                'method': 'ping',
                'id': 1
            })
            
            await ws.send(ping_msg)
            print(f"📤 Sent: {ping_msg}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                print(f"📥 Received: {response}")
                return True
            except asyncio.TimeoutError:
                print("⚠️  No response received (timeout)")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket connection failed: {type(e).__name__}: {str(e)}")
        return False


async def test_language_server_protocol(csrf_token, base_url="http://127.0.0.1:51497"):
    """Test Language Server Protocol (LSP) initialization."""
    print("\n" + "=" * 70)
    print("Testing Language Server Protocol")
    print("=" * 70)
    
    headers = {
        'X-CSRF-Token': csrf_token,
        'Content-Type': 'application/json',
        'User-Agent': 'Windsurf-Client'
    }
    
    # LSP initialize request
    initialize_request = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'initialize',
        'params': {
            'processId': None,
            'clientInfo': {
                'name': 'windsurf-test',
                'version': '1.0.0'
            },
            'capabilities': {}
        }
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(base_url, headers=headers, json=initialize_request, timeout=5) as resp:
                print(f"Status: {resp.status}")
                text = await resp.text()
                print(f"Response: {text[:500]}")
                
                if resp.status == 200:
                    try:
                        data = json.loads(text)
                        print("\n✅ LSP Initialize successful!")
                        print(json.dumps(data, indent=2)[:500])
                        return True
                    except json.JSONDecodeError:
                        print("⚠️  Response is not JSON")
                        return False
        except Exception as e:
            print(f"❌ LSP request failed: {type(e).__name__}: {str(e)}")
            return False


async def test_cascade_api(csrf_token, session_id=None):
    """Test Cascade API endpoints."""
    print("\n" + "=" * 70)
    print("Testing Cascade API")
    print("=" * 70)
    
    headers = {
        'X-CSRF-Token': csrf_token,
        'Content-Type': 'application/json',
        'User-Agent': 'Windsurf-Client'
    }
    
    if session_id:
        headers['X-Session-ID'] = session_id
    
    # Try common Cascade endpoints
    cascade_requests = [
        ('http://127.0.0.1:51497/cascade/chat', {
            'message': 'test',
            'sessionId': session_id or 'test-session'
        }),
        ('http://127.0.0.1:51501/cascade/chat', {
            'message': 'test',
            'sessionId': session_id or 'test-session'
        }),
    ]
    
    async with aiohttp.ClientSession() as session:
        for url, body in cascade_requests:
            try:
                async with session.post(url, headers=headers, json=body, timeout=5) as resp:
                    print(f"\n✓ POST {url}")
                    print(f"  Status: {resp.status}")
                    if resp.status in [200, 201]:
                        text = await resp.text()
                        print(f"  Response: {text[:200]}")
                        return True
            except Exception as e:
                print(f"\n✗ POST {url} - {type(e).__name__}")


async def main():
    csrf_token = "d1dfed32-5615-4751-9a46-f08c30e9700b"
    session_id = None  # Add session ID if found
    
    print("=" * 70)
    print("Windsurf CSRF Token Validator")
    print("=" * 70)
    print(f"\nTesting CSRF Token: {csrf_token}")
    print()
    
    # Test HTTP endpoints
    await test_http_endpoints(csrf_token)
    
    # Test WebSocket
    await test_websocket_connection(csrf_token)
    
    # Test LSP
    await test_language_server_protocol(csrf_token)
    
    # Test Cascade API
    await test_cascade_api(csrf_token, session_id)
    
    print("\n" + "=" * 70)
    print("Testing Complete")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
