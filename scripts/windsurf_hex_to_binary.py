#!/usr/bin/env python3
"""
Windsurf Hex to Binary Converter
Converts hex dump to binary payload file.
"""

import sys
import re

def hex_to_binary(hex_string, output_file):
    """Convert hex string to binary file."""
    # Clean the hex string
    hex_clean = re.sub(r'[^0-9a-fA-F]', '', hex_string)
    
    print("=" * 60)
    print("  HEX TO BINARY CONVERTER")
    print("=" * 60)
    print(f"\n📝 Input hex length: {len(hex_clean)} characters")
    print(f"📦 Output binary length: {len(hex_clean) // 2} bytes")
    print(f"💾 Output file: {output_file}\n")
    
    # Convert to bytes
    try:
        binary_data = bytes.fromhex(hex_clean)
        
        # Save to file
        with open(output_file, "wb") as f:
            f.write(binary_data)
        
        print(f"✅ Successfully converted!")
        print(f"📦 First 50 bytes (hex): {binary_data[:50].hex()}")
        print(f"📦 First 50 bytes (ascii): {binary_data[:50].decode('ascii', errors='ignore')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("  WINDSURF HEX TO BINARY CONVERTER")
    print("=" * 60)
    
    # Check if hex file exists
    hex_files = [
        "captured_payload.hex",
        "captured_start_cascade.hex",
        "captured_send_message.hex",
        "captured_assign_model.hex"
    ]
    
    found = False
    for hex_file in hex_files:
        try:
            with open(hex_file, "r", encoding="utf-8") as f:
                hex_content = f.read()
            
            # Determine output filename
            output_file = hex_file.replace(".hex", ".bin")
            
            print(f"\n📂 Found: {hex_file}")
            if hex_to_binary(hex_content, output_file):
                print(f"\n✅ Created: {output_file}")
                print(f"   You can now use: python windsurf_replay_payload.py")
                found = True
        except FileNotFoundError:
            continue
    
    if not found:
        print("\n⚠️  No .hex files found!")
        print("\nExpected files:")
        for f in hex_files:
            print(f"   - {f}")
        
        print("\n📝 How to create a .hex file:")
        print("\n1. Open Windsurf DevTools (Ctrl+Shift+I)")
        print("2. Go to Network tab")
        print("3. Send a Cascade message")
        print("4. Click on the request (e.g., SendUserCascadeMessage)")
        print("5. Go to 'Payload' tab")
        print("6. Copy the hex data")
        print("7. Paste into a file: captured_send_message.hex")
        print("8. Run this script again")
        
        print("\n💡 Example hex format:")
        print("   0a 24 64 38 66 32 37 38 37 66 2d 35 37 65 61")
        print("   or")
        print("   0a2464386632373837662d35376561")
        print("   (spaces are optional)")
        
        print("\n📋 Or paste hex directly:")
        print("   python windsurf_hex_to_binary.py <hex_string> <output.bin>")
    
    print()

if __name__ == "__main__":
    if len(sys.argv) == 3:
        # Direct conversion from command line
        hex_string = sys.argv[1]
        output_file = sys.argv[2]
        hex_to_binary(hex_string, output_file)
    else:
        # Scan for .hex files
        main()
