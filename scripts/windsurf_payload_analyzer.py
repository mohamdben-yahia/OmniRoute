#!/usr/bin/env python3
"""
Windsurf Payload Analyzer
Analyzes the captured payload to understand the Protobuf structure.
"""

# Captured payload from browser (hex representation)
captured_hex = """
24 64 38 66 32 37 38 37 66 2d 35 37 65 61 2d 34 37 33 64 2d 39 66 64 61 2d 61 33 36 35 31 64 32 35 38 61 33 31 09
64 6c 62 6a 20 73 64 cc 09
77 69 6e 64 73 75 72 66 31 2e 34 38 2e 32 bd 64 65 76 69 6e 2d 73 65 73 73 69 6f 6e 2d 74 6f 6b 65 6e 24 65 79 4a 68 62 47 63 69 4f 69 4a 49 55 7a 49 31 4e 69 49 73 49 6e 52 35 63 43 49 36 49 6b 70 58 56 43 4a 39 2e 65 79 4a 7a 5a 58 4e 7a 61 57 39 75 58 32 6c 6b 49 6a 6f 69 64 32 6c 75 5a 48 4e 31 63 6d 59 74 63 32 56 7a 63 32 6c 76 62 69 31 68 4e 6a 6c 69 59 7a 59 35 4e 57 51 79 4e 32 45 30 4e 57 56 6a 59 6d 52 6d 4e 6a 56 6d 59 57 49 35 4d 57 51 78 4f 44 5a 68 4e 69 4a 39 2e 4b 79 61 4e 67 4a 38 76 4d 36 67 51 73 77 56 6a 73 35 59 4d 44 7a 53 62 34 51 37 6c 46 35 33 31 33 54 42 6c 56 5f 74 79 62 71 4d 22 65 6e 3a 32 2e 31 2e 33 32 62 77 69 6e 64 73 75 72 66 a2 25 75 73 65 72 2d 61 30 38 37 37 66 61 34 39 32 62 62 34 65 62 33 62 30 36 39 37 61 37 63 37 32 62 62 62 39 37 62 f2 33 64 65 76 69 6e 2d 74 65 61 6d 24 61 63 63 6f 75 6e 74 2d 32 61 32 62 64 37 61 63 39 61 34 65 34 37 65 65 38 33 31 34 30 65 61 63 65 31 39 32 63 39 62 65 2a 2d 0a 20 6a 73 77 65 2d 31 2d 36 3a 32 32 72 4d 4f 44 45 4c 5f 55 4e 53 50 45 43 49 46 49 45 44
"""

def parse_hex_string(hex_str):
    """Convert hex string to bytes."""
    hex_clean = hex_str.replace('\n', '').replace(' ', '')
    return bytes.fromhex(hex_clean)

def analyze_protobuf(data):
    """Analyze protobuf structure."""
    print("=" * 60)
    print("  PROTOBUF PAYLOAD ANALYSIS")
    print("=" * 60)
    
    print(f"\n📦 Total length: {len(data)} bytes")
    print(f"📦 Hex: {data.hex()[:100]}...\n")
    
    # Try to find readable strings
    print("🔍 Readable strings found:")
    current_string = bytearray()
    strings_found = []
    
    for byte in data:
        if 32 <= byte <= 126:  # Printable ASCII
            current_string.append(byte)
        else:
            if len(current_string) > 3:
                strings_found.append(current_string.decode('ascii'))
            current_string = bytearray()
    
    if len(current_string) > 3:
        strings_found.append(current_string.decode('ascii'))
    
    for i, s in enumerate(strings_found, 1):
        print(f"   {i}. {s}")
    
    # Look for UUIDs
    print("\n🔍 UUIDs found:")
    text = data.decode('ascii', errors='ignore')
    import re
    uuids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text)
    for uuid in uuids:
        print(f"   - {uuid}")
    
    # Analyze field structure
    print("\n🔍 Protobuf field analysis:")
    pos = 0
    field_num = 1
    
    while pos < min(len(data), 200):  # Analyze first 200 bytes
        if pos >= len(data):
            break
            
        byte = data[pos]
        wire_type = byte & 0x07
        field_number = byte >> 3
        
        if field_number > 0 and field_number < 1000:
            wire_type_name = {
                0: "varint",
                1: "64-bit",
                2: "length-delimited",
                3: "start group",
                4: "end group",
                5: "32-bit"
            }.get(wire_type, "unknown")
            
            print(f"   Field {field_number}: {wire_type_name} (byte {pos})")
            
            if wire_type == 2:  # Length-delimited
                pos += 1
                if pos < len(data):
                    length = data[pos]
                    if length < 128:
                        preview = data[pos+1:pos+1+min(length, 20)]
                        try:
                            preview_str = preview.decode('ascii', errors='ignore')
                            print(f"      Length: {length}, Preview: {preview_str[:30]}")
                        except:
                            print(f"      Length: {length}, Hex: {preview.hex()}")
        
        pos += 1
        field_num += 1

def main():
    # Parse the captured payload
    payload = parse_hex_string(captured_hex)
    
    # Analyze it
    analyze_protobuf(payload)
    
    print("\n" + "=" * 60)
    print("  KEY FINDINGS")
    print("=" * 60)
    print("\nBased on the analysis, the payload contains:")
    print("1. Cascade ID (UUID)")
    print("2. Message text")
    print("3. IDE info: windsurf, version 1.48.2")
    print("4. Session token (JWT)")
    print("5. Extension version: 2.1.32")
    print("6. User ID")
    print("7. Team/account ID")
    print("8. SWE version: swe-1-6")
    print("\nWe need to match this exact structure in our Protobuf builder.\n")

if __name__ == "__main__":
    main()
