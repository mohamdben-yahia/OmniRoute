#!/usr/bin/env python3
"""Decode the exact bytes after userId."""

# From the context output:
# ...75 73 65 72 2d 34 37 62 61 37 31 30 39 36 66 30 62 34 39 38 64 61 61 66 33 30 62 64 31 62 31 31 61 39 62 36 62 c3 b2 01 03 00 01 03 02 33 64 65 76 69 6e...
#    u  s  e  r  -  4  7  b  a  7  1  0  9  6  f  0  b  4  9  8  d  a  a  f  3  0  b  d  1  b  1  1  a  9  b  6  b  ?? ?? ?? ?? ?? ?? ?? ?? 3  d  e  v  i  n

# The bytes after userId (37 bytes) are: c3 b2 01 03 00 01 03 02
# Let's decode these:

bytes_after_userid = bytes.fromhex("c3b201030001030233")

print("Bytes after userId:")
print(f"Hex: {bytes_after_userid.hex(' ')}")
print()

# c3 b2 01 could be a multi-byte varint tag
# Let's decode it:
# 0xc3 = 11000011b -> value = 0x43 (67), continue bit set
# 0xb2 = 10110010b -> value = 0x32 (50), continue bit set  
# 0x01 = 00000001b -> value = 0x01 (1), continue bit NOT set

# Varint value = 67 | (50 << 7) | (1 << 14) = 67 | 6400 | 16384 = 22851
# Field number = 22851 >> 3 = 2856
# Wire type = 22851 & 0x7 = 3

# That doesn't make sense. Let me try a different interpretation.

# Maybe it's:
# 0xc3 0xb2 = two-byte varint
# (0xc3 & 0x7F) | ((0xb2 & 0x7F) << 7) = 67 | 4096 = 4163
# Hmm, that's also weird.

# Wait, let me look at the pattern differently. Maybe:
# 0xa2 0x01 = field 20 tag (we know this works)
# 0x25 = length 37
# [37 bytes of userId]
# 0xf2 0x01 = field 30 tag
# 0x03 = length 3
# 0x00 0x01 0x03 = value

# But the hex shows c3 b2 01, not f2 01

# Let me check if c3 b2 could be part of the userId string
har_metadata_hex = "0a0877696e64737572661206312e34382e321ac2bd01646576696e2d73657373696f6e2d746f6b656e2465794a68624763694f694a49557a49314e694973496e523563434936496b705856434a392e65794a7a5a584e7a6157397558326c6b496a6f6964326c755a484e31636d59746332567a63326c76626931684e6a6c69597a59354e5751794e3245304e57566a596d526d4e6a566d595749354d5751784f445a684e694a392e4b79614e674a38764d3667517377566a7335594d447a53623451376c463533313354426c565f747962714d2202656e3a06322e312e3332620877696e6473757266c2a20125757365722d3437626137313039366630623439386461616633306264316231316139623662c3b201030001030233646576696e2d7465616d246163636f756e742d616537393063383664623936346533663963303239363330376663663436393120013800"

data = bytes.fromhex(har_metadata_hex)

# Find userId position
user_pos = data.find(b"user-")
print(f"userId starts at byte {user_pos}")

# The tag should be 2 bytes before (0xa2 0x01)
# The length should be 1 byte before (0x25 = 37)
tag_pos = user_pos - 3
length_pos = user_pos - 1

print(f"Tag at byte {tag_pos}: {data[tag_pos:tag_pos+2].hex(' ')}")
print(f"Length at byte {length_pos}: {data[length_pos]} (0x{data[length_pos]:02x})")

# userId should be 37 bytes
userid_end = user_pos + 37
print(f"userId ends at byte {userid_end}")
print(f"userId value: {data[user_pos:userid_end].decode('utf-8')}")

# Next field should start at userid_end
print(f"\nBytes after userId (next 10 bytes):")
print(f"Hex: {data[userid_end:userid_end+10].hex(' ')}")

# Decode the next tag
next_tag_bytes = data[userid_end:userid_end+2]
print(f"\nNext tag bytes: {next_tag_bytes.hex(' ')}")

# Try decoding as 2-byte varint
if len(next_tag_bytes) == 2:
    tag_value = (next_tag_bytes[0] & 0x7F) | ((next_tag_bytes[1] & 0x7F) << 7)
    field_num = tag_value >> 3
    wire_type = tag_value & 0x7
    print(f"Tag value: {tag_value} (0x{tag_value:04x})")
    print(f"Field number: {field_num}")
    print(f"Wire type: {wire_type}")
    
    if wire_type == 2:  # Length-delimited
        length = data[userid_end + 2]
        value = data[userid_end + 3:userid_end + 3 + length]
        print(f"Length: {length}")
        print(f"Value (hex): {value.hex(' ')}")
        print(f"Value (bytes): {list(value)}")
