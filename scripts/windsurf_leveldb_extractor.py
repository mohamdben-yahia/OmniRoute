#!/usr/bin/env python3
"""
Windsurf LevelDB Token Extractor
Extracts authentication tokens from Windsurf's Local Storage LevelDB.
"""

import sys
import json
from pathlib import Path
import re

try:
    import plyvel
except ImportError:
    print("❌ Missing plyvel library. Install with:")
    print("   pip install plyvel")
    sys.exit(1)


def extract_tokens_from_leveldb(db_path: str) -> dict:
    """
    Extract authentication tokens from Windsurf's Local Storage LevelDB.
    
    Args:
        db_path: Path to the leveldb directory
        
    Returns:
        Dictionary containing extracted tokens
    """
    tokens = {
        "sessionId": None,
        "csrfToken": None,
        "authToken": None,
        "accessToken": None,
        "refreshToken": None,
        "all_keys": [],
        "raw_data": {}
    }
    
    try:
        # Open LevelDB in read-only mode
        db = plyvel.DB(db_path, create_if_missing=False)
        
        print(f"✅ Opened LevelDB: {db_path}")
        print("\n" + "=" * 70)
        print("Scanning for authentication tokens...")
        print("=" * 70 + "\n")
        
        # Iterate through all key-value pairs
        for key, value in db:
            try:
                # Decode key
                key_str = key.decode('utf-8', errors='ignore')
                tokens["all_keys"].append(key_str)
                
                # Decode value
                value_str = value.decode('utf-8', errors='ignore')
                
                # Store raw data for interesting keys
                if any(keyword in key_str.lower() for keyword in [
                    'session', 'csrf', 'token', 'auth', 'cascade', 'codeium'
                ]):
                    tokens["raw_data"][key_str] = value_str
                    print(f"🔍 Found key: {key_str}")
                    print(f"   Value preview: {value_str[:200]}")
                    print()
                
                # Try to parse as JSON
                try:
                    value_json = json.loads(value_str)
                    
                    # Look for specific token fields
                    if isinstance(value_json, dict):
                        if 'sessionId' in value_json:
                            tokens['sessionId'] = value_json['sessionId']
                            print(f"✅ Found sessionId: {tokens['sessionId']}")
                        
                        if 'csrfToken' in value_json:
                            tokens['csrfToken'] = value_json['csrfToken']
                            print(f"✅ Found csrfToken: {tokens['csrfToken']}")
                        
                        if 'authToken' in value_json:
                            tokens['authToken'] = value_json['authToken']
                            print(f"✅ Found authToken: {tokens['authToken'][:50]}...")
                        
                        if 'accessToken' in value_json:
                            tokens['accessToken'] = value_json['accessToken']
                            print(f"✅ Found accessToken: {tokens['accessToken'][:50]}...")
                        
                        if 'refreshToken' in value_json:
                            tokens['refreshToken'] = value_json['refreshToken']
                            print(f"✅ Found refreshToken: {tokens['refreshToken'][:50]}...")
                
                except json.JSONDecodeError:
                    # Not JSON, check for token patterns in raw string
                    if 'session' in key_str.lower():
                        # Look for UUID-like patterns
                        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
                        matches = re.findall(uuid_pattern, value_str, re.IGNORECASE)
                        if matches and not tokens['sessionId']:
                            tokens['sessionId'] = matches[0]
                            print(f"✅ Found sessionId (pattern): {tokens['sessionId']}")
                    
                    if 'csrf' in key_str.lower():
                        # CSRF tokens are often hex strings
                        csrf_pattern = r'[0-9a-f]{32,64}'
                        matches = re.findall(csrf_pattern, value_str, re.IGNORECASE)
                        if matches and not tokens['csrfToken']:
                            tokens['csrfToken'] = matches[0]
                            print(f"✅ Found csrfToken (pattern): {tokens['csrfToken']}")
            
            except Exception as e:
                # Skip problematic entries
                pass
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error reading LevelDB: {e}")
        return None
    
    return tokens


def main():
    print("=" * 70)
    print("Windsurf LevelDB Token Extractor")
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
    tokens = extract_tokens_from_leveldb(str(leveldb_path))
    
    if not tokens:
        return 1
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 70)
    print(f"\n🔑 Session ID: {tokens.get('sessionId') or '❌ NOT FOUND'}")
    print(f"🔑 CSRF Token: {tokens.get('csrfToken') or '❌ NOT FOUND'}")
    print(f"🔑 Auth Token: {tokens.get('authToken')[:50] + '...' if tokens.get('authToken') else '❌ NOT FOUND'}")
    print(f"🔑 Access Token: {tokens.get('accessToken')[:50] + '...' if tokens.get('accessToken') else '❌ NOT FOUND'}")
    print(f"🔑 Refresh Token: {tokens.get('refreshToken')[:50] + '...' if tokens.get('refreshToken') else '❌ NOT FOUND'}")
    print(f"\n📦 Total keys scanned: {len(tokens['all_keys'])}")
    print(f"📦 Interesting keys found: {len(tokens['raw_data'])}")
    
    # Save to file
    output_file = Path("windsurf_leveldb_tokens.json")
    output_file.write_text(json.dumps(tokens, indent=2))
    print(f"\n✅ Full data saved to: {output_file}")
    
    # Show interesting keys
    if tokens['raw_data']:
        print("\n" + "=" * 70)
        print("🔍 INTERESTING KEYS")
        print("=" * 70)
        for key in tokens['raw_data'].keys():
            print(f"  - {key}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
