#!/usr/bin/env python3
"""
Windsurf Token Validator

This script validates captured authentication tokens by making
test requests to the Windsurf Cascade API.

Requirements:
    pip install requests

Usage:
    python validate_windsurf_tokens.py windsurf_tokens.json

Author: Investigation Team
Date: 2026-05-03
"""

import json
import sys
import requests
from pathlib import Path
from typing import Dict, List, Optional


class WindsurfTokenValidator:
    """Validates captured Windsurf authentication tokens."""
    
    def __init__(self, tokens_file: str):
        self.tokens_file = Path(tokens_file)
        self.api_base = "https://server.self-serve.windsurf.com"
        self.inference_base = "https://inference.codeium.com"
        
        if not self.tokens_file.exists():
            raise FileNotFoundError(f"Tokens file not found: {tokens_file}")
        
        with open(self.tokens_file, 'r', encoding='utf-8') as f:
            self.captures = json.load(f)
        
        print(f"✅ Loaded {len(self.captures)} captured requests")
    
    def extract_auth_headers(self) -> List[Dict[str, str]]:
        """Extract unique sets of authentication headers."""
        
        auth_sets = []
        seen = set()
        
        for capture in self.captures:
            auth_headers = capture.get('auth_headers', {})
            if not auth_headers:
                continue
            
            # Create a signature for deduplication
            signature = json.dumps(sorted(auth_headers.items()))
            if signature in seen:
                continue
            
            seen.add(signature)
            auth_sets.append({
                'headers': auth_headers,
                'url': capture['url'],
                'timestamp': capture['timestamp']
            })
        
        return auth_sets
    
    def test_chat_completion(self, headers: Dict[str, str]) -> Optional[Dict]:
        """Test chat completion endpoint with captured headers."""
        
        print(f"\n{'='*70}")
        print("🧪 Testing Chat Completion Endpoint")
        print(f"{'='*70}")
        
        # Common endpoint paths to try
        endpoints = [
            "/v1/chat/completions",
            "/chat/completions",
            "/v1/completions",
            "/api/v1/chat/completions",
            "/cascade/chat",
        ]
        
        test_payload = {
            "model": "cascade",
            "messages": [
                {"role": "user", "content": "Hello, this is a test message."}
            ],
            "stream": False,
            "max_tokens": 50
        }
        
        for endpoint in endpoints:
            url = f"{self.api_base}{endpoint}"
            print(f"\n📡 Testing: {url}")
            
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=test_payload,
                    timeout=10
                )
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ SUCCESS!")
                    try:
                        data = response.json()
                        print(f"   Response: {json.dumps(data, indent=2)[:500]}")
                        return {'url': url, 'response': data}
                    except:
                        print(f"   Response: {response.text[:500]}")
                        return {'url': url, 'response': response.text}
                
                elif response.status_code == 401:
                    print(f"   ❌ Unauthorized - Token may be expired")
                
                elif response.status_code == 403:
                    print(f"   ❌ Forbidden - Token may be invalid")
                
                elif response.status_code == 404:
                    print(f"   ⚠️  Not Found - Wrong endpoint")
                
                else:
                    print(f"   ⚠️  Unexpected status: {response.text[:200]}")
                    
            except requests.exceptions.Timeout:
                print(f"   ⏱️  Timeout")
            except requests.exceptions.ConnectionError:
                print(f"   ❌ Connection Error")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        return None
    
    def test_inference_api(self, headers: Dict[str, str]) -> Optional[Dict]:
        """Test inference API endpoint."""
        
        print(f"\n{'='*70}")
        print("🧪 Testing Inference API Endpoint")
        print(f"{'='*70}")
        
        endpoints = [
            "/v1/chat/completions",
            "/exa.language_server_pb.LanguageServerService/GetCompletions",
        ]
        
        for endpoint in endpoints:
            url = f"{self.inference_base}{endpoint}"
            print(f"\n📡 Testing: {url}")
            
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json={"model": "cascade", "prompt": "test"},
                    timeout=10
                )
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ SUCCESS!")
                    return {'url': url, 'response': response.text[:500]}
                else:
                    print(f"   Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        return None
    
    def validate_all(self):
        """Validate all captured token sets."""
        
        print(f"\n{'='*70}")
        print("🔍 WINDSURF TOKEN VALIDATION")
        print(f"{'='*70}")
        
        auth_sets = self.extract_auth_headers()
        
        if not auth_sets:
            print("\n❌ No authentication headers found in captures!")
            print("\nMake sure:")
            print("  1. mitmproxy captured actual API requests")
            print("  2. You sent a Cascade message while capturing")
            print("  3. The proxy was properly configured")
            return
        
        print(f"\n✅ Found {len(auth_sets)} unique authentication header sets")
        
        results = []
        
        for i, auth_set in enumerate(auth_sets, 1):
            print(f"\n{'='*70}")
            print(f"Testing Auth Set #{i}")
            print(f"{'='*70}")
            print(f"Source URL: {auth_set['url']}")
            print(f"Timestamp: {auth_set['timestamp']}")
            print(f"\nHeaders:")
            for key, value in auth_set['headers'].items():
                print(f"  {key}: {value[:50]}{'...' if len(value) > 50 else ''}")
            
            # Test chat completion
            result = self.test_chat_completion(auth_set['headers'])
            if result:
                results.append({
                    'auth_set': i,
                    'type': 'chat_completion',
                    'success': True,
                    'result': result
                })
                print(f"\n🎉 WORKING TOKEN SET FOUND!")
                break
            
            # Test inference API
            result = self.test_inference_api(auth_set['headers'])
            if result:
                results.append({
                    'auth_set': i,
                    'type': 'inference',
                    'success': True,
                    'result': result
                })
                print(f"\n🎉 WORKING TOKEN SET FOUND!")
                break
        
        # Save results
        results_file = self.tokens_file.parent / "validation_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{'='*70}")
        print("📊 VALIDATION SUMMARY")
        print(f"{'='*70}")
        
        if results:
            print(f"✅ Found {len(results)} working token set(s)")
            print(f"📁 Results saved to: {results_file}")
            
            for result in results:
                print(f"\n✅ Auth Set #{result['auth_set']} - {result['type']}")
                print(f"   URL: {result['result']['url']}")
        else:
            print("❌ No working tokens found")
            print("\nPossible reasons:")
            print("  1. Tokens may have expired (try capturing fresh tokens)")
            print("  2. Wrong API endpoints (Windsurf may use different paths)")
            print("  3. Additional authentication required (cookies, etc.)")
            print("\nNext steps:")
            print("  1. Capture tokens again with fresh Cascade messages")
            print("  2. Check captured request bodies for additional auth data")
            print("  3. Try different API endpoint paths")


def main():
    """Main entry point."""
    
    if len(sys.argv) < 2:
        print("Usage: python validate_windsurf_tokens.py <tokens_file.json>")
        print("\nExample:")
        print("  python validate_windsurf_tokens.py windsurf_tokens.json")
        sys.exit(1)
    
    tokens_file = sys.argv[1]
    
    try:
        validator = WindsurfTokenValidator(tokens_file)
        validator.validate_all()
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
