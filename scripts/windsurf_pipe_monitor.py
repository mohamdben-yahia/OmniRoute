#!/usr/bin/env python3
"""
Windsurf Named Pipe Monitor
Monitors communication through the named pipe between Windsurf and language_server.
"""

import sys
import time
import json
from pathlib import Path

try:
    import win32pipe
    import win32file
    import pywintypes
except ImportError:
    print("❌ Missing pywin32 library. Install with:")
    print("   pip install pywin32")
    sys.exit(1)


def monitor_named_pipe(pipe_name, duration_seconds=60):
    """
    Monitor a named pipe for communications.
    
    Args:
        pipe_name: Name of the pipe (e.g., '\\\\.\\pipe\\server_e2008e0d467af35d')
        duration_seconds: How long to monitor
    """
    print("=" * 70)
    print("Windsurf Named Pipe Monitor")
    print("=" * 70)
    print(f"\nPipe: {pipe_name}")
    print(f"Duration: {duration_seconds} seconds")
    print()
    
    captured_messages = []
    
    try:
        # Try to open the pipe for reading
        print("Attempting to connect to named pipe...")
        
        handle = win32file.CreateFile(
            pipe_name,
            win32file.GENERIC_READ,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )
        
        print("✅ Connected to named pipe!")
        print("📡 Monitoring communications...")
        print()
        
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            try:
                # Try to read from pipe
                result, data = win32file.ReadFile(handle, 4096)
                
                if data:
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] Received {len(data)} bytes")
                    
                    # Try to decode as text
                    try:
                        text = data.decode('utf-8', errors='ignore')
                        print(f"  Content: {text[:200]}")
                        
                        # Try to parse as JSON
                        try:
                            json_data = json.loads(text)
                            print(f"  JSON: {json.dumps(json_data, indent=2)[:300]}")
                            
                            # Look for auth tokens
                            if any(key in str(json_data).lower() for key in ['session', 'csrf', 'token', 'auth']):
                                print("  🔑 CONTAINS AUTH DATA!")
                                captured_messages.append({
                                    'timestamp': timestamp,
                                    'data': json_data
                                })
                        except json.JSONDecodeError:
                            pass
                    except:
                        print(f"  Binary data: {data[:50].hex()}")
                    
                    print()
                
                time.sleep(0.1)
                
            except pywintypes.error as e:
                if e.winerror == 109:  # ERROR_BROKEN_PIPE
                    print("⚠️  Pipe closed by server")
                    break
                elif e.winerror == 232:  # ERROR_NO_DATA
                    time.sleep(0.1)
                    continue
                else:
                    raise
        
        win32file.CloseHandle(handle)
        
    except pywintypes.error as e:
        if e.winerror == 2:  # ERROR_FILE_NOT_FOUND
            print(f"❌ Pipe not found: {pipe_name}")
            print("   The pipe may have a different name or may not exist yet")
        elif e.winerror == 5:  # ERROR_ACCESS_DENIED
            print(f"❌ Access denied to pipe: {pipe_name}")
            print("   The pipe is already in use or requires elevated privileges")
        else:
            print(f"❌ Error: {e}")
        return None
    
    # Save captured messages
    if captured_messages:
        output_file = Path("windsurf_pipe_capture.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(captured_messages, f, indent=2)
        
        print("=" * 70)
        print("📊 CAPTURE SUMMARY")
        print("=" * 70)
        print(f"\n🔑 Messages with auth data: {len(captured_messages)}")
        print(f"✅ Saved to: {output_file}")
    
    return captured_messages


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor Windsurf named pipe communications")
    parser.add_argument("--pipe", default=r"\\.\pipe\server_e2008e0d467af35d", help="Named pipe path")
    parser.add_argument("--duration", type=int, default=60, help="Monitoring duration in seconds")
    
    args = parser.parse_args()
    
    print("⚠️  NOTE: This requires the pipe to not be exclusively locked")
    print("   If access is denied, the pipe is already in use by Windsurf")
    print()
    
    messages = monitor_named_pipe(args.pipe, args.duration)
    
    if messages:
        print()
        print("💡 Found authentication data in pipe communications!")
        return 0
    else:
        print()
        print("⚠️  No auth data captured")
        print("   The pipe may be exclusively locked or use a different protocol")
        return 1


if __name__ == "__main__":
    sys.exit(main())
