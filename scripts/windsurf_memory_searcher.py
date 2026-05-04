#!/usr/bin/env python3
"""
Windsurf Process Memory Token Searcher
Searches for authentication tokens in language_server process memory.
"""

import subprocess
import re
import json
from pathlib import Path
from datetime import datetime


def get_language_server_pid():
    """Get the PID of language_server_windows_x64.exe."""
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
            if pid.isdigit():
                return int(pid)
    except Exception as e:
        print(f"Error getting language server PID: {e}")
    
    return None


def dump_process_strings(pid):
    """
    Dump readable strings from process memory using PowerShell.
    This is a lightweight alternative to procdump.
    """
    print(f"🔍 Extracting strings from process memory (PID: {pid})...")
    print("   This may take a minute...")
    
    # PowerShell script to read process memory
    ps_script = f"""
    $process = Get-Process -Id {pid}
    $handle = $process.Handle
    
    # Try to read process memory regions
    # Note: This is limited and may not work for all memory regions
    try {{
        $modules = $process.Modules
        Write-Output "Found $($modules.Count) modules"
        
        foreach ($module in $modules) {{
            Write-Output "Module: $($module.ModuleName)"
        }}
    }} catch {{
        Write-Output "Error accessing process memory: $_"
    }}
    """
    
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=30
        )
        
        return result.stdout
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return ""


def search_for_token_patterns(text):
    """Search for token patterns in text."""
    tokens = {
        "sessionId_candidates": [],
        "csrfToken_candidates": [],
        "authToken_candidates": [],
        "jwt_candidates": [],
        "api_keys": []
    }
    
    # UUID pattern (common for sessionId)
    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    uuids = re.findall(uuid_pattern, text, re.IGNORECASE)
    tokens["sessionId_candidates"] = list(set(uuids))[:10]  # Limit to 10
    
    # Hex tokens (common for CSRF)
    hex_pattern = r'\b[0-9a-f]{32,64}\b'
    hex_tokens = re.findall(hex_pattern, text, re.IGNORECASE)
    tokens["csrfToken_candidates"] = list(set(hex_tokens))[:10]
    
    # JWT pattern
    jwt_pattern = r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'
    jwts = re.findall(jwt_pattern, text)
    tokens["jwt_candidates"] = list(set(jwts))[:5]
    
    # API key patterns (various formats)
    api_key_patterns = [
        r'sk-[A-Za-z0-9]{32,}',  # OpenAI style
        r'Bearer [A-Za-z0-9_\-\.]{20,}',  # Bearer tokens
        r'token["\s:]+([A-Za-z0-9_\-\.]{20,})',  # Generic token
    ]
    
    for pattern in api_key_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        tokens["api_keys"].extend(matches)
    
    tokens["api_keys"] = list(set(tokens["api_keys"]))[:10]
    
    return tokens


def alternative_memory_search():
    """
    Alternative approach: Search in language_server working directory
    and temporary files for tokens.
    """
    print("\n🔍 Searching alternative locations...")
    
    locations = [
        Path.home() / "AppData" / "Local" / "Temp",
        Path.home() / "AppData" / "Roaming" / "Windsurf",
    ]
    
    found_files = []
    
    for location in locations:
        if location.exists():
            # Search for recently modified files
            try:
                for file in location.rglob("*"):
                    if file.is_file() and file.suffix in ['.log', '.txt', '.json', '.tmp']:
                        # Check if file was modified recently (last hour)
                        if (datetime.now().timestamp() - file.stat().st_mtime) < 3600:
                            found_files.append(file)
            except Exception:
                pass
    
    print(f"   Found {len(found_files)} recent files to search")
    
    all_tokens = {
        "sessionId_candidates": [],
        "csrfToken_candidates": [],
        "jwt_candidates": []
    }
    
    for file in found_files[:20]:  # Limit to 20 files
        try:
            content = file.read_text(encoding='utf-8', errors='ignore')
            
            # Search for token patterns
            if 'sessionId' in content or 'csrfToken' in content or 'Bearer' in content:
                print(f"   ✅ Found potential tokens in: {file.name}")
                
                tokens = search_for_token_patterns(content)
                all_tokens["sessionId_candidates"].extend(tokens["sessionId_candidates"])
                all_tokens["csrfToken_candidates"].extend(tokens["csrfToken_candidates"])
                all_tokens["jwt_candidates"].extend(tokens["jwt_candidates"])
        except Exception:
            pass
    
    # Deduplicate
    for key in all_tokens:
        all_tokens[key] = list(set(all_tokens[key]))[:10]
    
    return all_tokens


def main():
    print("=" * 70)
    print("Windsurf Process Memory Token Searcher")
    print("=" * 70)
    print()
    
    # Get language server PID
    print("Step 1: Finding language_server_windows_x64.exe...")
    pid = get_language_server_pid()
    
    if not pid:
        print("❌ language_server_windows_x64.exe not found")
        print("   Make sure Windsurf is running")
        return 1
    
    print(f"✅ Found language_server_windows_x64.exe (PID: {pid})")
    print()
    
    # Try to dump process info
    print("Step 2: Analyzing process memory...")
    memory_dump = dump_process_strings(pid)
    
    if memory_dump:
        print(f"   Extracted {len(memory_dump)} characters")
        tokens = search_for_token_patterns(memory_dump)
    else:
        tokens = {
            "sessionId_candidates": [],
            "csrfToken_candidates": [],
            "jwt_candidates": [],
            "api_keys": []
        }
    
    # Alternative search
    alt_tokens = alternative_memory_search()
    
    # Merge results
    for key in alt_tokens:
        if key in tokens:
            tokens[key].extend(alt_tokens[key])
            tokens[key] = list(set(tokens[key]))[:10]
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 SEARCH RESULTS")
    print("=" * 70)
    print()
    
    print(f"🔑 Session ID candidates: {len(tokens.get('sessionId_candidates', []))}")
    for sid in tokens.get('sessionId_candidates', [])[:5]:
        print(f"   - {sid}")
    
    print(f"\n🔑 CSRF Token candidates: {len(tokens.get('csrfToken_candidates', []))}")
    for csrf in tokens.get('csrfToken_candidates', [])[:5]:
        print(f"   - {csrf}")
    
    print(f"\n🔑 JWT candidates: {len(tokens.get('jwt_candidates', []))}")
    for jwt in tokens.get('jwt_candidates', [])[:3]:
        print(f"   - {jwt[:80]}...")
    
    print(f"\n🔑 API Key candidates: {len(tokens.get('api_keys', []))}")
    for key in tokens.get('api_keys', [])[:3]:
        print(f"   - {key[:80]}...")
    
    # Save results
    output_file = Path("windsurf_memory_tokens.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")
    
    print("\n" + "=" * 70)
    print("💡 NEXT STEPS")
    print("=" * 70)
    print()
    print("If no tokens were found, try:")
    print("1. Send a Cascade message to trigger API calls")
    print("2. Run this script again immediately after")
    print("3. Use Process Explorer to inspect language_server memory")
    print("4. Set up HTTP proxy (mitmproxy) to capture traffic")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
