#!/usr/bin/env python3
"""
Windsurf CDP Injection — Real Cascade Session Capture
======================================================

Strategy:
1. Attach to Windsurf renderer via CDP
2. Inject SendUserCascadeMessage through real UI context
3. Capture live sessionId + csrfToken from network/runtime
4. Intercept StartCascade with valid auth

This bypasses the 401 by using the actual runtime session.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import argparse

try:
    import websockets
    import aiohttp
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("   pip install websockets aiohttp")
    sys.exit(1)


class WindsurfCDPInjector:
    """CDP-based cascade message injector with session capture."""
    
    def __init__(self, debug_port: int = 9222):
        self.debug_port = debug_port
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.msg_id = 0
        self.captured_session: Dict[str, Any] = {}
        self.network_requests: list = []
        
    async def connect(self) -> bool:
        """Connect to Windsurf CDP endpoint."""
        try:
            # Get list of targets
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://127.0.0.1:{self.debug_port}/json") as resp:
                    if resp.status != 200:
                        print(f"❌ CDP not available on port {self.debug_port}")
                        return False
                    
                    targets = await resp.json()
                    
            # Find main renderer target
            renderer = None
            for target in targets:
                if target.get("type") == "page" and "windsurf" in target.get("url", "").lower():
                    renderer = target
                    break
            
            if not renderer:
                print("❌ No Windsurf renderer found")
                print(f"Available targets: {json.dumps(targets, indent=2)}")
                return False
            
            ws_url = renderer["webSocketDebuggerUrl"]
            print(f"✔ Found renderer: {renderer['title']}")
            print(f"✔ Connecting to: {ws_url}")
            
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
        
        # Wait for response with matching id
        while True:
            resp_raw = await self.ws.recv()
            resp = json.loads(resp_raw)
            
            # Store network events
            if "method" in resp and resp["method"].startswith("Network."):
                self.network_requests.append(resp)
            
            # Check for session tokens in console/network
            if "method" in resp and resp["method"] == "Runtime.consoleAPICalled":
                self._extract_tokens_from_console(resp)
            
            if resp.get("id") == self.msg_id:
                return resp
    
    def _extract_tokens_from_console(self, event: Dict):
        """Extract sessionId/csrfToken from console logs."""
        try:
            args = event.get("params", {}).get("args", [])
            for arg in args:
                value = arg.get("value", "")
                if isinstance(value, str):
                    if "sessionId" in value or "csrfToken" in value:
                        print(f"🔍 Token hint in console: {value[:100]}")
                        # Try to parse as JSON
                        try:
                            data = json.loads(value)
                            if "sessionId" in data:
                                self.captured_session["sessionId"] = data["sessionId"]
                            if "csrfToken" in data:
                                self.captured_session["csrfToken"] = data["csrfToken"]
                        except:
                            pass
        except Exception as e:
            pass
    
    async def enable_domains(self):
        """Enable CDP domains for monitoring."""
        print("🔧 Enabling CDP domains...")
        await self.send_cdp("Network.enable")
        await self.send_cdp("Runtime.enable")
        await self.send_cdp("Console.enable")
        print("✔ Domains enabled")
    
    async def inject_cascade_message(self, message: str = "hello_probe_001") -> Dict:
        """
        Inject a cascade message through the renderer context.
        
        This simulates a real user message, triggering the full cascade flow.
        """
        print(f"💉 Injecting cascade message: {message}")
        
        # JavaScript to inject into renderer
        injection_code = f"""
        (async () => {{
            // Try to find the cascade send function
            const cascadeAPI = window.__WINDSURF_CASCADE_API__ || 
                              window.vscode?.postMessage ||
                              window.parent?.postMessage;
            
            if (!cascadeAPI) {{
                return {{ error: "CASCADE_API_NOT_FOUND" }};
            }}
            
            // Send message through real API
            const payload = {{
                type: "SendUserCascadeMessage",
                message: "{message}",
                timestamp: Date.now()
            }};
            
            // Capture session context
            const sessionContext = {{
                sessionId: window.__CASCADE_SESSION_ID__ || "unknown",
                csrfToken: window.__CSRF_TOKEN__ || "unknown",
                timestamp: Date.now()
            }};
            
            console.log("CASCADE_SESSION_CONTEXT:", JSON.stringify(sessionContext));
            
            // Send message
            if (typeof cascadeAPI === 'function') {{
                cascadeAPI(payload);
            }} else {{
                cascadeAPI.postMessage(payload, "*");
            }}
            
            return {{ success: true, context: sessionContext }};
        }})();
        """
        
        result = await self.send_cdp("Runtime.evaluate", {
            "expression": injection_code,
            "awaitPromise": True,
            "returnByValue": True
        })
        
        if "result" in result and "result" in result["result"]:
            return result["result"]["result"]["value"]
        
        return {"error": "INJECTION_FAILED", "raw": result}
    
    async def capture_network_flow(self, duration: float = 5.0):
        """Capture network requests for a duration."""
        print(f"📡 Capturing network flow for {duration}s...")
        
        start_time = asyncio.get_event_loop().time()
        captured_requests = []
        
        while asyncio.get_event_loop().time() - start_time < duration:
            try:
                resp_raw = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
                resp = json.loads(resp_raw)
                
                # Filter cascade-related requests
                if "method" in resp and resp["method"].startswith("Network."):
                    params = resp.get("params", {})
                    request = params.get("request", {})
                    url = request.get("url", "")
                    
                    if "StartCascade" in url or "SendUserCascadeMessage" in url:
                        captured_requests.append({
                            "method": resp["method"],
                            "url": url,
                            "headers": request.get("headers", {}),
                            "timestamp": asyncio.get_event_loop().time()
                        })
                        print(f"🎯 Captured cascade request: {url}")
                        
                        # Extract tokens from headers
                        headers = request.get("headers", {})
                        if "x-csrf-token" in headers:
                            self.captured_session["csrfToken"] = headers["x-csrf-token"]
                        if "x-session-id" in headers:
                            self.captured_session["sessionId"] = headers["x-session-id"]
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"⚠️ Network capture error: {e}")
                break
        
        return captured_requests
    
    async def run_injection_flow(self, message: str = "hello_probe_001") -> Dict:
        """Full injection + capture flow."""
        if not await self.connect():
            return {"error": "CONNECTION_FAILED"}
        
        await self.enable_domains()
        
        # Start network capture in background
        capture_task = asyncio.create_task(self.capture_network_flow(duration=5.0))
        
        # Wait a bit for domains to stabilize
        await asyncio.sleep(0.5)
        
        # Inject message
        injection_result = await self.inject_cascade_message(message)
        
        # Wait for network capture to complete
        network_flow = await capture_task
        
        return {
            "injection": injection_result,
            "captured_session": self.captured_session,
            "network_flow": network_flow,
            "status": "SUCCESS" if self.captured_session else "PARTIAL"
        }
    
    async def close(self):
        """Close CDP connection."""
        if self.ws:
            await self.ws.close()


async def main():
    parser = argparse.ArgumentParser(description="Windsurf CDP Cascade Injector")
    parser.add_argument("--port", type=int, default=9222, help="CDP debug port")
    parser.add_argument("--message", default="hello_probe_001", help="Message to inject")
    parser.add_argument("--output", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Windsurf CDP Injection — Real Session Capture")
    print("=" * 60)
    
    injector = WindsurfCDPInjector(debug_port=args.port)
    
    try:
        result = await injector.run_injection_flow(message=args.message)
        
        print("\n" + "=" * 60)
        print("📊 RESULTS")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(json.dumps(result, indent=2))
            print(f"\n✔ Results saved to: {output_path}")
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 CAPTURED SESSION TOKENS")
        print("=" * 60)
        if result.get("captured_session"):
            for key, value in result["captured_session"].items():
                print(f"{key}: {value}")
        else:
            print("❌ No tokens captured")
            print("\n💡 Possible reasons:")
            print("   1. Windsurf not running with --remote-debugging-port=9222")
            print("   2. No active cascade session")
            print("   3. Tokens stored in different location")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await injector.close()


if __name__ == "__main__":
    asyncio.run(main())
