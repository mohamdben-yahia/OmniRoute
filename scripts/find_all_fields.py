#!/usr/bin/env python3
"""Check if userId length includes extra bytes."""

har_metadata_hex = "0a0877696e64737572661206312e34382e321ac2bd01646576696e2d73657373696f6e2d746f6b656e2465794a68624763694f694a49557a49314e694973496e523563434936496b705856434a392e65794a7a5a584e7a6157397558326c6b496a6f6964326c755a484e31636d59746332567a63326c76626931684e6a6c69597a59354e5751794e3245304e57566a596d526d4e6a566d595749354d5751784f445a684e694a392e4b79614e674a38764d3667517377566a7335594d447a53623451376c463533313354426c565f747962714d2202656e3a06322e312e3332620877696e6473757266c2a20125757365722d3437626137313039366630623439386461616633306264316231316139623662c3b201030001030233646576696e2d7465616d246163636f756e742d616537393063383664623936346533663963303239363330376663663436393120013800"

data = bytes.fromhex(har_metadata_hex)

# Find the 0xa2 0x01 pattern (field 20 tag)
for i in range(len(data) - 1):
    if data[i] == 0xa2 and data[i+1] == 0x01:
        print(f"Found field 20 tag at byte {i}")
        length_byte = data[i+2]
        print(f"Length byte: {length_byte} (0x{length_byte:02x})")
        
        value_start = i + 3
        value_end = value_start + length_byte
        value = data[value_start:value_end]
        
        print(f"Value ({length_byte} bytes): {value}")
        try:
            print(f"As string: {value.decode('utf-8')}")
        except:
            print(f"As hex: {value.hex(' ')}")
        
        print(f"\nNext bytes after this field:")
        print(f"Bytes {value_end} to {value_end+10}: {data[value_end:value_end+10].hex(' ')}")
        
        # Try to decode the next field
        if value_end < len(data):
            next_byte = data[value_end]
            print(f"\nNext byte: 0x{next_byte:02x} = {next_byte}")
            
            # Check if it's a valid tag
            if next_byte & 0x80:  # Continuation bit set
                # Multi-byte varint tag
                next_byte2 = data[value_end + 1]
                tag_value = (next_byte & 0x7F) | ((next_byte2 & 0x7F) << 7)
                field_num = tag_value >> 3
                wire_type = tag_value & 0x7
                print(f"Multi-byte tag: 0x{next_byte:02x} 0x{next_byte2:02x}")
                print(f"Tag value: {tag_value}, field: {field_num}, wire type: {wire_type}")
            else:
                # Single-byte tag
                field_num = next_byte >> 3
                wire_type = next_byte & 0x7
                print(f"Single-byte tag: field {field_num}, wire type {wire_type}")
        
        break

print("\n" + "="*80)
print("Let me search for field 30 and 32 by their expected tag patterns...")

# Field 30, wire type 2: (30 << 3) | 2 = 242 = 0xf2
# As 2-byte varint: 0xf2 0x01
print("\nSearching for 0xf2 0x01 (field 30)...")
for i in range(len(data) - 1):
    if data[i] == 0xf2 and data[i+1] == 0x01:
        print(f"Found at byte {i}")

# Field 32, wire type 2: (32 << 3) | 2 = 258 = 0x102
# As 2-byte varint: 0x82 0x02
print("\nSearching for 0x82 0x02 (field 32)...")
for i in range(len(data) - 1):
    if data[i] == 0x82 and data[i+1] == 0x02:
        print(f"Found at byte {i}")

# Maybe the encoding is different. Let me search for the teamId string
print("\n" + "="*80)
print("Searching for teamId string...")
team_pos = data.find(b"devin-team$")
if team_pos >= 0:
    print(f"Found 'devin-team$' at byte {team_pos}")
    # Look back for tag and length
    print(f"Bytes before teamId: {data[team_pos-5:team_pos].hex(' ')}")
    
    # The pattern should be: tag (1-2 bytes) + length (1 byte) + value
    # Let's try different offsets
    for offset in [2, 3, 4]:
        tag_start = team_pos - offset
        if tag_start >= 0:
            print(f"\nTrying tag at byte {tag_start}:")
            print(f"  Bytes: {data[tag_start:team_pos].hex(' ')}")
