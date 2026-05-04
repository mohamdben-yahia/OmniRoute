#!/usr/bin/env python3
"""Properly decode the HAR body with UTF-8 decoding."""

# From the HAR file, the postData.text field contains:
har_body_text = r"\nÌ\u0002\n\bwindsurf\u0012\u00061.48.2\u001a½\u0001devin-session-token$eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uX2lkIjoid2luZHN1cmYtc2Vzc2lvbi1hNjliYzY5NWQyN2E0NWVjYmRmNjVmYWI5MWQxODZhNiJ9.KyaNgJ8vM6gQswVjs5YMDzSb4Q7lF5313TBlV_tybqM\"\u0002en:\u00062.1.32b\bwindsurf¢\u0001%user-47ba71096f0b498daaf30bd1b11a9b6bò\u0001\u0003\u0000\u0001\u0003\u00023devin-team$account-ae790c86db964e3f9c0296307fcf4691 \u00018\u0000"

# Decode unicode escapes to get the actual bytes
har_body = har_body_text.encode('utf-8').decode('unicode_escape').encode('latin1')

print(f"HAR body length: {len(har_body)} bytes")
print(f"HAR body hex: {har_body.hex()}")
print()

# Now let's find field 30 and 32
print("="*80)
print("Searching for fields in properly decoded body...")

# Find userId
user_pos = har_body.find(b"user-")
print(f"\nField 20 (userId) at byte {user_pos}")
print(f"Value: user-47ba71096f0b498daaf30bd1b11a9b6b")

# After userId (37 bytes), we should find field 30
userid_end = user_pos + 37
print(f"\nBytes after userId: {har_body[userid_end:userid_end+10].hex(' ')}")

# Decode field 30
if userid_end < len(har_body):
    tag_byte1 = har_body[userid_end]
    tag_byte2 = har_body[userid_end + 1]
    print(f"Tag bytes: 0x{tag_byte1:02x} 0x{tag_byte2:02x}")
    
    tag_value = (tag_byte1 & 0x7F) | ((tag_byte2 & 0x7F) << 7)
    field_num = tag_value >> 3
    wire_type = tag_value & 0x7
    print(f"Field {field_num}, wire type {wire_type}")
    
    if wire_type == 2:
        length = har_body[userid_end + 2]
        value = har_body[userid_end + 3:userid_end + 3 + length]
        print(f"Length: {length}")
        print(f"Value (hex): {value.hex(' ')}")
        print(f"Value (bytes): {list(value)}")
        
        # Next field after field 30
        next_pos = userid_end + 3 + length
        print(f"\nNext field at byte {next_pos}:")
        print(f"Bytes: {har_body[next_pos:next_pos+5].hex(' ')}")
        
        tag_byte1 = har_body[next_pos]
        tag_byte2 = har_body[next_pos + 1]
        print(f"Tag bytes: 0x{tag_byte1:02x} 0x{tag_byte2:02x}")
        
        tag_value = (tag_byte1 & 0x7F) | ((tag_byte2 & 0x7F) << 7)
        field_num = tag_value >> 3
        wire_type = tag_value & 0x7
        print(f"Field {field_num}, wire type {wire_type}")
        
        if wire_type == 2:
            length = har_body[next_pos + 2]
            value = har_body[next_pos + 3:next_pos + 3 + length]
            print(f"Length: {length}")
            print(f"Value: {value.decode('utf-8')}")

print("\n" + "="*80)
print("FINAL EXTRACTED VALUES:")
print("export WINDSURF_USER_ID='user-47ba71096f0b498daaf30bd1b11a9b6b'")
print("export WINDSURF_TEAM_ID='devin-team$account-ae790c86db964e3f9c0296307fcf4691'")
print("export WINDSURF_METADATA_F='000103'  # hex bytes")
