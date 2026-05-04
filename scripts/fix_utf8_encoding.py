#!/usr/bin/env python3
"""Decode HAR body as raw bytes, not UTF-8."""

# The HAR shows these unicode escapes in the JSON:
# ¢\u0001 = 0xa2 0x01 (field 20 tag)
# ò\u0001 = 0xf2 0x01 (field 30 tag)

# Let's manually construct the correct byte sequence
# From the HAR text, after userId we have: ò\u0001\u0003\u0000\u0001\u0003\u00023devin-team$...

# ò = 0xf2 in latin1
# \u0001 = 0x01
# \u0003 = 0x03
# \u0000 = 0x00
# \u0001 = 0x01
# \u0003 = 0x03
# \u0002 = 0x02
# 3 = 0x33

# So the sequence is: f2 01 03 00 01 03 02 33
# f2 01 = field 30, wire type 2
# 03 = length 3
# 00 01 03 = value
# 02 33 = next field tag and length

# But 0x02 is field 0, wire type 2, which is wrong
# Unless... 0x02 0x33 is part of a longer varint?

# Let me check: field 32, wire type 2 = (32 << 3) | 2 = 258
# 258 in varint = 0x82 0x02
# But we have 0x02 0x33

# Wait! Maybe the HAR has: \u0082\u00023
# Let me check the original HAR text more carefully

har_text = r"\nÌ\u0002\n\bwindsurf\u0012\u00061.48.2\u001a½\u0001devin-session-token$eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uX2lkIjoid2luZHN1cmYtc2Vzc2lvbi1hNjliYzY5NWQyN2E0NWVjYmRmNjVmYWI5MWQxODZhNiJ9.KyaNgJ8vM6gQswVjs5YMDzSb4Q7lF5313TBlV_tybqM\"\u0002en:\u00062.1.32b\bwindsurf¢\u0001%user-47ba71096f0b498daaf30bd1b11a9b6bò\u0001\u0003\u0000\u0001\u0003\u00023devin-team$account-ae790c86db964e3f9c0296307fcf4691 \u00018\u0000"

# Let me extract just the part after userId:
# ...user-47ba71096f0b498daaf30bd1b11a9b6bò\u0001\u0003\u0000\u0001\u0003\u00023devin-team$...

# ò = 0xf2
# \u0001 = 0x01
# \u0003 = 0x03
# \u0000 = 0x00
# \u0001 = 0x01
# \u0003 = 0x03
# \u0002 = 0x02
# 3 = 0x33 (ASCII '3')

# So after field 30 value (00 01 03), we have:
# 0x02 0x33 = tag and length for next field
# But 0x02 alone is field 0, wire type 2

# WAIT! Maybe it's: \u0082 not \u0002!
# Let me check if the HAR has \u0082 or \u0002

print("Checking the HAR text for field 32 tag...")
print()

# The HAR shows: \u00023
# This is \u0002 followed by '3'
# So it's 0x02 0x33

# But that doesn't make sense for field 32
# Unless... the field 32 tag is encoded differently

# Let me recalculate: field 32, wire type 2
# (32 << 3) | 2 = 256 + 2 = 258
# 258 in varint:
# 258 = 2 + 256 = 2 + (2 << 7)
# So: first byte = 0x82 (2 | 0x80), second byte = 0x02

# But the HAR shows \u0002, not \u0082
# This suggests the HAR might have the wrong encoding

# Let me try a different approach - use the hex dump we already have
hex_dump = "0ac38c020a0877696e64737572661206312e34382e321ac2bd01646576696e2d73657373696f6e2d746f6b656e2465794a68624763694f694a49557a49314e694973496e523563434936496b705856434a392e65794a7a5b584e7a6157397558326c6b496a6f6964326c755a484e31636d59746332567a63326c76626931684e6a6c69597a59354e5651794e3245304e57566a596d526d4e6a566d595749354d5751784f445a684e694a392e4b79614e674a38764d3667517377566a7335594d447a53623451376c463533313354426c565f747962714d2202656e3a06322e312e3332620877696e6473757266c2a20125757365722d3437626137313039366630623439386461616633306264316231316139623662c3b201030001030233646576696e2d7465616d246163636f756e742d616537393063383664623936346533663963303239363330376663663436393120013800"

data = bytes.fromhex(hex_dump)

# The hex shows: c3 b2 01 03 00 01 03 02 33
# c3 b2 is UTF-8 for 0xf2
# So the original bytes should be: f2 01 03 00 01 03 82 02 33

# Let me manually fix the UTF-8 encoding
print("Converting UTF-8 encoded bytes back to original...")
print()

# Find all UTF-8 encoded bytes and convert them back
original_bytes = bytearray()
i = 0
while i < len(data):
    if i < len(data) - 1 and data[i] == 0xc3:
        # UTF-8 two-byte sequence for 0x80-0xBF
        # 0xc3 0xb2 = 0xf2
        # 0xc3 0x82 = 0xc2
        # Formula: original = ((0xc3 & 0x1f) << 6) | (next_byte & 0x3f)
        # But simpler: 0xc3 0xXX = 0xC0 + XX
        original_byte = 0xc0 + (data[i+1] & 0x3f)
        original_bytes.append(original_byte)
        i += 2
    elif i < len(data) - 1 and data[i] == 0xc2:
        # UTF-8 two-byte sequence for 0x80-0xBF
        # 0xc2 0xa2 = 0xa2
        original_byte = data[i+1]
        original_bytes.append(original_byte)
        i += 2
    else:
        original_bytes.append(data[i])
        i += 1

print(f"Original bytes length: {len(original_bytes)}")
print(f"Original hex: {original_bytes.hex()}")
print()

# Now find field 30 and 32
user_pos = original_bytes.find(b"user-")
userid_end = user_pos + 37

print(f"Bytes after userId: {original_bytes[userid_end:userid_end+15].hex(' ')}")

# Decode field 30
tag1 = original_bytes[userid_end]
tag2 = original_bytes[userid_end + 1]
tag_value = (tag1 & 0x7F) | ((tag2 & 0x7F) << 7)
field_num = tag_value >> 3
wire_type = tag_value & 0x7

print(f"\nField 30:")
print(f"  Tag: 0x{tag1:02x} 0x{tag2:02x}")
print(f"  Field number: {field_num}, wire type: {wire_type}")

length = original_bytes[userid_end + 2]
value = original_bytes[userid_end + 3:userid_end + 3 + length]
print(f"  Length: {length}")
print(f"  Value (hex): {value.hex(' ')}")

# Decode field 32
next_pos = userid_end + 3 + length
tag1 = original_bytes[next_pos]
tag2 = original_bytes[next_pos + 1]
tag_value = (tag1 & 0x7F) | ((tag2 & 0x7F) << 7)
field_num = tag_value >> 3
wire_type = tag_value & 0x7

print(f"\nField 32:")
print(f"  Tag: 0x{tag1:02x} 0x{tag2:02x}")
print(f"  Field number: {field_num}, wire type: {wire_type}")

length = original_bytes[next_pos + 2]
value = original_bytes[next_pos + 3:next_pos + 3 + length]
print(f"  Length: {length}")
print(f"  Value: {value.decode('utf-8')}")

print("\n" + "="*80)
print("FINAL VALUES:")
print("export WINDSURF_USER_ID='user-47ba71096f0b498daaf30bd1b11a9b6b'")
print("export WINDSURF_TEAM_ID='devin-team$account-ae790c86db964e3f9c0296307fcf4691'")
print(f"export WINDSURF_METADATA_F='{value.hex()}'  # from field 30")
