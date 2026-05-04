#!/usr/bin/env python3
"""
Windsurf LevelDB Token Extractor (Binary Parser)
Extracts authentication tokens from Windsurf's Local Storage LevelDB files
without requiring plyvel (uses binary parsing instead).
"""

import sys
import json
from pathlib import Path
import re


def extract_tokens_from_ldb_files(leveldb_dir: Path) -> dict:
    """
    Extract tokens by reading .ldb and .log files as binary and searching for patterns.
    
    Args:
        leveldb_dir: Path to the leveldb directory
        
    Returns:
        Dictionary containing extracted tokens
    """
    tokens = {
        "sessionId": None,
        "csrfToken": None,
        "authToken": None,
        "accessToken": None,
        "refreshToken": None,
        "codeiumToken": None,
        "cascadeSession": None,
        "interesting_data": []
    }
    
    # Get all .ldb and .log files
    ldb_files = list(leveldb_dir.glob("*.ldb")) + list(leveldb_dir.glob("*.log"))
    
    if not ldb_files:
        print("❌ No LevelDB files found")
        return tokens
    
    print(f"📂 Found {len(ldb_files)} LevelDB files to scan")
    print()
    
    # Patterns to search for
    patterns = {
        'sessionId': [
            rb'sessionId["\s:]+([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})',
            rb'"sessionId":"([^"]+)"',
        ],
        'csrfToken': [
            rb'csrfToken["\s:]+([0-9a-f]{32,64})',
            rb'"csrfToken":"([^"]+)"',
        ],
        'authToken': [
            rb'"authToken":"([^"]+)"',
            rb'authToken["\s:]+([A-Za-z0-9_\-\.]{20,})',
        ],
        'accessToken': [
            rb'"accessToken":"([^"]+)"',
            rb'access_token["\s:]+([A-Za-z0-9_\-\.]{20,})',
        ],
        'refreshToken': [
            rb'"refreshToken":"([^"]+)"',
            rb'refresh_token["\s:]+([A-Za-z0-9_\-\.]{20,})',
        ],
        'codeiumToken': [
            rb'"codeium[^"]*token":"([^"]+)"',
            rb'codeium[^:]*:["\s]*([A-Za-z0-9_\-\.]{20,})',
        ],
        'cascadeSession': [
            rb'"cascade[^"]*session":"([^"]+)"',
            rb'cascade[^:]*:["\s]*([0-9a-f\-]{20,})',
        ]
    }
    
    # Scan each file
    for ldb_file in ldb_files:
        try:
            print(f"🔍 Scanning: {ldb_file.name} ({ldb_file.stat().st_size} bytes)")
            
            with open(ldb_file, 'rb') as f:
                content = f.read()
            
            # Search for each token type
            for token_name, token_patterns in patterns.items():
                if tokens[token_name]:
                    continue  # Already found
                
                for pattern in token_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Take the first match
                        token_value = matches[0].decode('utf-8', errors='ignore')
                        tokens[token_name] = token_value
                        print(f"   ✅ Found {token_name}: {token_value[:50]}{'...' if len(token_value) > 50 else ''}")
                        break
            
            # Look for any JSON-like structures with interesting keywords
            json_pattern = rb'\{[^}]{0,500}(?:session|csrf|token|auth|cascade|codeium)[^}]{0,500}\}'
            json_matches = re.findall(json_pattern, content, re.IGNORECASE)
            
            for match in json_matches[:10]:  # Limit to first 10 matches per file
                try:
                    match_str = match.decode('utf-8', errors='ignore')
                    # Try to parse as JSON
                    try:
                        json_obj = json.loads(match_str)
                        if isinstance(json_obj, dict):
                            tokens['interesting_data'].append({
                                'file': ldb_file.name,
                                'data': json_obj
                            })
                    except json.JSONDecodeError:
                        # Not valid JSON, but might contain useful info
                        if len(match_str) < 500:
                            tokens['interesting_data'].append({
                                'file': ldb_file.name,
                                'raw': match_str
                            })
                except:
                    pass
        
        except Exception as e:
            print(f"   ⚠️  Error reading {ldb_file.name}: {e}")
    
    return tokens


def main():
    print("=" * 70)
    print("Windsurf LevelDB Token Extractor (Binary Parser)")
    print("=" * 70)
    print()
    
    # Default path to Windsurf Local Storage
    appdata = Path.home() / "AppData" / "Roaming" / "Windsurf"
    leveldb_path = appdata / "Local Storage" / "leveldb"
    
    if not leveldb_path.exists():
        print(f"❌ LevelDB not found at: {leveldb_path}")
        print("   Make sure Windsurf is installed and has been run at least once")
        return 1
    
    print(f"📂 LevelDB path: {leveldb_path}")
    print()
    
    # Extract tokens
    tokens = extract_tokens_from_ldb_files(leveldb_path)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 70)
    print(f"\n🔑 Session ID: {tokens.get('sessionId') or '❌ NOT FOUND'}")
    print(f"🔑 CSRF Token: {tokens.get('csrfToken') or '❌ NOT FOUND'}")
    print(f"🔑 Auth Token: {(tokens.get('authToken')[:50] + '...') if tokens.get('authToken') else '❌ NOT FOUND'}")
    print(f"🔑 Access Token: {(tokens.get('accessToken')[:50] + '...') if tokens.get('accessToken') else '❌ NOT FOUND'}")
    print(f"🔑 Refresh Token: {(tokens.get('refreshToken')[:50] + '...') if tokens.get('refreshToken') else '❌ NOT FOUND'}")
    print(f"🔑 Codeium Token: {(tokens.get('codeiumToken')[:50] + '...') if tokens.get('codeiumToken') else '❌ NOT FOUND'}")
    print(f"🔑 Cascade Session: {tokens.get('cascadeSession') or '❌ NOT FOUND'}")
    print(f"\n📦 Interesting data blocks found: {len(tokens['interesting_data'])}")
    
    # Save to file
    output_file = Path("windsurf_leveldb_tokens.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Full data saved to: {output_file}")
    
    # Show sample of interesting data
    if tokens['interesting_data']:
        print("\n" + "=" * 70)
        print("🔍 SAMPLE INTERESTING DATA (first 3 blocks)")
        print("=" * 70)
        for i, data in enumerate(tokens['interesting_data'][:3]):
            print(f"\nBlock {i+1} from {data.get('file', 'unknown')}:")
            if 'data' in data:
                print(json.dumps(data['data'], indent=2)[:500])
            elif 'raw' in data:
                print(data['raw'][:500])
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
