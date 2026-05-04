#!/usr/bin/env python3
"""
Windsurf Session Token Extractor — Enhanced CDP Capture
========================================================

This script extends the basic CDP injector with:
1. localStorage/sessionStorage extraction
2. Cookie capture
3. WebSocket message interception
4. Automatic token persistence
5. Replay capability with captured tokens

Usage:
    python windsurf_token_extractor.py --extract-all
    python windsurf_token_extractor.py --replay-with tokens.json
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import argparse
from datetime import datetime

try:
    import websockets
    import aiohttp
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("   pip install websockets aiohttp")
    sys.exit(1)

# Import inspector helper for dynamic port detection
try:
    from windsurf_inspector_helper import find_node_inspector_port
except ImportError:
    print("❌ Cannot import windsurf_inspector_helper.py")
    print("   Make sure windsurf_inspector_helper.py is in the same directory")
    sys.exit(1)


class WindsurfTokenExtractor:
    """Enhanced CDP-based token extractor with storage/cookie/WS support."""

    def __init__(self, debug_port: Optional[int] = None):
        """
        Initialize token extractor.

        Args:
            debug_port: Inspector port. If None, will auto-detect NodeService inspector.
        """
        self.debug_port = debug_port
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.msg_id = 0
        self.captured_tokens: Dict[str, Any] = {
            "sessionId": None,
            "csrfToken": None,
            "localStorage": {},
            "sessionStorage": {},
            "cookies": [],
            "headers": {},
            "websocket_messages": [],
            "timestamp": None
        }

    async def connect(self) -> bool:
        """Connect to Windsurf CDP endpoint."""
        try:
            # Auto-detect inspector port if not provided
            if self.debug_port is None:
                print("🔍 Auto-detecting NodeService inspector port...")
                self.debug_port = find_node_inspector_port()
                if not self.debug_port:
                    print("❌ Cannot detect NodeService inspector port")
                    print("💡 Make sure Windsurf is running")
                    return False
                print(f"✅ Detected inspector on port {self.debug_port}")

            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://127.0.0.1:{self.debug_port}/json") as resp:
                    if resp.status != 200:
                        print(f"❌ CDP not available on port {self.debug_port}")
                        print(f"💡 Start Windsurf with: --remote-debugging-port={self.debug_port}")
                        return False

                    targets = await resp.json()

            # Find main renderer
            renderer = None
            for target in targets:
                if target.get("type") == "page":
                    url = target.get("url", "")
                    if "windsurf" in url.lower() or "vscode" in url.lower():
                        renderer = target
                        break

            if not renderer:
                print("❌ No Windsurf renderer found")
                print("Available targets:")
                for t in targets:
                    print(f"  - {t.get('type')}: {t.get('title')} ({t.get('url', 'no url')[:80]})")
                return False

            ws_url = renderer["webSocketDebuggerUrl"]
            print(f"✔ Found renderer: {renderer['title']}")
            print(f"✔ URL: {renderer.get('url', 'unknown')[:80]}")

            self.ws = await websockets.connect(ws_url)
            print("✔ CDP connected")
            return True

        except Exception as e:
            print(f"❌ CDP connection failed: {e}")
            return False

    async def send_cdp(self, method: str, params: Optional[Dict] = None) -> Dict:
        """Send CDP command and wait for response."""
        if not self.ws:
            raise RuntimeError("Not connected")

        self.msg_id += 1
        msg = {
            "id": self.msg_id,
            "method": method,
            "params": params or {}
        }

        await self.ws.send(json.dumps(msg))

        # Wait for matching response
        while True:
            resp_raw = await self.ws.recv()
            resp = json.loads(resp_raw)

            # Capture WebSocket frames
            if "method" in resp and resp["method"] == "Network.webSocketFrameReceived":
                self._capture_websocket_frame(resp)

            if resp.get("id") == self.msg_id:
                return resp

    def _capture_websocket_frame(self, event: Dict):
        """Capture WebSocket messages for cascade protocol analysis."""
        try:
            params = event.get("params", {})
            response = params.get("response", {})
            payload = response.get("payloadData", "")

            # Try to parse as JSON
            try:
                data = json.loads(payload)
                if "sessionId" in str(data) or "csrfToken" in str(data):
                    self.captured_tokens["websocket_messages"].append({
                        "timestamp": datetime.now().isoformat(),
                        "payload": data
                    })
                    print(f"🔍 WS message with tokens: {str(data)[:100]}")
            except:
                pass
        except Exception as e:
            pass

    async def enable_domains(self):
        """Enable all necessary CDP domains."""
        print("🔧 Enabling CDP domains...")
        domains = [
            "Network",
            "Runtime",
            "Console",
            "DOMStorage",
            "Page"
        ]

        for domain in domains:
            await self.send_cdp(f"{domain}.enable")

        print("✔ Domains enabled")

    async def extract_local_storage(self) -> Dict[str, str]:
        """Extract localStorage contents."""
        print("📦 Extracting localStorage...")

        code = """
        (() => {
            const storage = {};
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                storage[key] = localStorage.getItem(key);
            }
            return storage;
        })();
        """

        result = await self.send_cdp("Runtime.evaluate", {
            "expression": code,
            "returnByValue": True
        })

        if "result" in result and "result" in result["result"]:
            storage = result["result"]["result"].get("value", {})
            self.captured_tokens["localStorage"] = storage

            # Look for tokens
            for key, value in storage.items():
                if "session" in key.lower() or "csrf" in key.lower() or "token" in key.lower():
                    print(f"  🔑 {key}: {str(value)[:50]}...")

            return storage

        return {}

    async def extract_session_storage(self) -> Dict[str, str]:
        """Extract sessionStorage contents."""
        print("📦 Extracting sessionStorage...")

        code = """
        (() => {
            const storage = {};
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                storage[key] = sessionStorage.getItem(key);
            }
            return storage;
        })();
        """

        result = await self.send_cdp("Runtime.evaluate", {
            "expression": code,
            "returnByValue": True
        })

        if "result" in result and "result" in result["result"]:
            storage = result["result"]["result"].get("value", {})
            self.captured_tokens["sessionStorage"] = storage

            # Look for tokens
            for key, value in storage.items():
                if "session" in key.lower() or "csrf" in key.lower() or "token" in key.lower():
                    print(f"  🔑 {key}: {str(value)[:50]}...")

            return storage

        return {}

    async def extract_cookies(self) -> List[Dict]:
        """Extract all cookies."""
        print("🍪 Extracting cookies...")

        result = await self.send_cdp("Network.getAllCookies")

        if "result" in result and "cookies" in result["result"]:
            cookies = result["result"]["cookies"]
            self.captured_tokens["cookies"] = cookies

            # Look for session/csrf cookies
            for cookie in cookies:
                name = cookie.get("name", "")
                if "session" in name.lower() or "csrf" in name.lower() or "token" in name.lower():
                    print(f"  🍪 {name}: {cookie.get('value', '')[:50]}...")

            return cookies

        return []

    async def extract_window_globals(self) -> Dict[str, Any]:
        """Extract window-level globals that might contain tokens."""
        print("🌐 Extracting window globals...")

        code = """
        (() => {
            const globals = {};

            // Common token locations
            const keys = [
                '__CASCADE_SESSION_ID__',
                '__CSRF_TOKEN__',
                '__WINDSURF_SESSION__',
                '__WINDSURF_CSRF__',
                'WINDSURF_SESSION_ID',
                'WINDSURF_CSRF_TOKEN'
            ];

            for (const key of keys) {
                if (window[key] !== undefined) {
                    globals[key] = window[key];
                }
            }

            // Check vscode namespace
            if (window.vscode) {
                globals.__vscode_available = true;
            }

            return globals;
        })();
        """

        result = await self.send_cdp("Runtime.evaluate", {
            "expression": code,
            "returnByValue": True
        })

        if "result" in result and "result" in result["result"]:
            globals_data = result["result"]["result"].get("value", {})

            for key, value in globals_data.items():
                print(f"  🌐 {key}: {str(value)[:50]}")

                if "session" in key.lower():
                    self.captured_tokens["sessionId"] = value
                if "csrf" in key.lower():
                    self.captured_tokens["csrfToken"] = value

            return globals_data

        return {}

    async def capture_network_headers(self, duration: float = 3.0):
        """Capture network request headers for cascade endpoints."""
        print(f"📡 Capturing network headers for {duration}s...")

        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < duration:
            try:
                resp_raw = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
                resp = json.loads(resp_raw)

                if "method" in resp and resp["method"] == "Network.requestWillBeSent":
                    params = resp.get("params", {})
                    request = params.get("request", {})
                    url = request.get("url", "")
                    headers = request.get("headers", {})

                    # Filter cascade-related requests
                    if any(keyword in url for keyword in ["StartCascade", "SendUserCascadeMessage", "cascade", "59602", "59599"]):
                        print(f"  🎯 Cascade request: {url}")

                        # Extract tokens from headers
                        for header_name, header_value in headers.items():
                            if "csrf" in header_name.lower() or "session" in header_name.lower() or "token" in header_name.lower():
                                print(f"    🔑 {header_name}: {header_value}")
                                self.captured_tokens["headers"][header_name] = header_value

                                if "csrf" in header_name.lower():
                                    self.captured_tokens["csrfToken"] = header_value
                                if "session" in header_name.lower():
                                    self.captured_tokens["sessionId"] = header_value

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                break

    async def extract_all_tokens(self) -> Dict[str, Any]:
        """Full extraction pipeline."""
        if not await self.connect():
            return {"error": "CONNECTION_FAILED"}

        await self.enable_domains()

        # Extract from all sources
        await self.extract_local_storage()
        await self.extract_session_storage()
        await self.extract_cookies()
        await self.extract_window_globals()

        # Capture network traffic
        await self.capture_network_headers(duration=3.0)

        self.captured_tokens["timestamp"] = datetime.now().isoformat()

        return self.captured_tokens

    async def close(self):
        """Close CDP connection."""
        if self.ws:
            await self.ws.close()


async def main():
    parser = argparse.ArgumentParser(description="Windsurf Token Extractor")
    parser.add_argument("--port", type=int, default=None, help="CDP debug port (auto-detect if not specified)")
    parser.add_argument("--extract-all", action="store_true", help="Extract all tokens")
    parser.add_argument("--output", default="windsurf_tokens.json", help="Output file")
    parser.add_argument("--watch", action="store_true", help="Watch for token changes")

    args = parser.parse_args()

    print("=" * 70)
    print("Windsurf Session Token Extractor — Enhanced CDP Capture")
    print("=" * 70)

    extractor = WindsurfTokenExtractor(debug_port=args.port)

    try:
        tokens = await extractor.extract_all_tokens()

        print("\n" + "=" * 70)
        print("📊 EXTRACTION RESULTS")
        print("=" * 70)

        # Summary
        print(f"\n🔑 Session ID: {tokens.get('sessionId') or '❌ NOT FOUND'}")
        print(f"🔑 CSRF Token: {tokens.get('csrfToken') or '❌ NOT FOUND'}")
        print(f"📦 localStorage keys: {len(tokens.get('localStorage', {}))}")
        print(f"📦 sessionStorage keys: {len(tokens.get('sessionStorage', {}))}")
        print(f"🍪 Cookies: {len(tokens.get('cookies', []))}")
        print(f"📡 Headers captured: {len(tokens.get('headers', {}))}")
        print(f"💬 WebSocket messages: {len(tokens.get('websocket_messages', []))}")

        # Save to file
        output_path = Path(args.output)
        output_path.write_text(json.dumps(tokens, indent=2))
        print(f"\n✔ Tokens saved to: {output_path}")

        # Detailed output
        print("\n" + "=" * 70)
        print("📋 DETAILED TOKENS")
        print("=" * 70)
        print(json.dumps(tokens, indent=2))

        # Validation
        print("\n" + "=" * 70)
        print("✅ VALIDATION")
        print("=" * 70)

        if tokens.get("sessionId") and tokens.get("csrfToken"):
            print("✅ Both sessionId and csrfToken captured!")
            print("\n🚀 You can now use these tokens to replay requests:")
            print(f"\n  python windsurf_direct_probe.py \\")
            print(f"    --session-id '{tokens['sessionId']}' \\")
            print(f"    --csrf-token '{tokens['csrfToken']}'")
        else:
            print("⚠️ Tokens not fully captured")
            print("\n💡 Troubleshooting:")
            print("  1. Open Cascade panel in Windsurf")
            print("  2. Send a message manually")
            print("  3. Re-run this script")
            print("  4. Check if tokens are in different storage location")

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await extractor.close()


if __name__ == "__main__":
    asyncio.run(main())
