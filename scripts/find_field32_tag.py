#!/usr/bin/env python3
"""Correctly identify field 32 tag in the sequence."""

# We know:
# Field 30: f2 01 03 00 01 03
#   - Tag: f2 01 (field 30, wire type 2)
#   - Length: 03
#   - Value: 00 01 03
# Next should be field 32

# Field 32, wire type 2: (32 << 3) | 2 = 258
# 258 in varint encoding:
# 258 = 2 + 256 = 2 + (2 * 128)
# First byte: (2 | 0x80) = 0x82
# Second byte: 2
# So: 0x82 0x02

# But the sequence shows: f2 01 03 00 01 03 02 33 64 65 76 69 6e
# After field 30 value (00 01 03), we have: 02 33 64 65 76 69 6e
# 02 33 doesn't match 82 02

# WAIT! Maybe the UTF-8 conversion missed 0x82?
# Let me check: 0x82 in UTF-8 would be 0xc2 0x82
# And in the original hex dump, we should see c2 82

# Let me search the original hex for c2 82
original_hex = "0ac38c020a0877696e64737572661206312e34382e321ac2bd01646576696e2d73657373696f6e2d746f6b656e2465794a68624763694f694a49557a49314e694973496e523563434936496b705856434a392e65794a7a5b584e7a6157397558326c6b496a6f6964326c755a484e31636d59746332567a63326c76626931684e6a6c69597a59354e5651794e3245304e57566a596d526d4e6a566d595749354d5651784f445a684e694a392e4b79614e674a38764d3667517377566a7335594d447a53623451376c463533313354426c565f747962714d2202656e3a06322e312e3332620877696e6473757266c2a20125757365722d3437626137313039366630623439386461616633306264316231316139623662c3b201030001030233646576696e2d7465616d246163636f756e742d616537393063383664623936346533663963303239363330376663663436393120013800"

print("Searching for c2 82 in original hex...")
if "c282" in original_hex:
    print("Found c2 82!")
    pos = original_hex.index("c282")
    print(f"Position: {pos // 2}")
    print(f"Context: {original_hex[pos-10:pos+20]}")
else:
    print("NOT found - field 32 tag is not UTF-8 encoded as c2 82")

print("\nSearching for 82 02 pattern...")
if "8202" in original_hex:
    print("Found 82 02!")
    pos = original_hex.index("8202")
    print(f"Position: {pos // 2}")
    print(f"Context: {original_hex[pos-10:pos+20]}")
else:
    print("NOT found - field 32 tag 82 02 is not in the hex")

print("\n" + "="*80)
print("Let me check the sequence after field 30 more carefully...")
print()

# The sequence is: f2 01 03 00 01 03 02 33 64 65 76 69 6e 2d 74 65 61 6d
# f2 01 = field 30 tag
# 03 = length 3
# 00 01 03 = value
# 02 = next byte
# 33 = next byte (0x33 = 51 decimal)

# Wait! What if 0x02 is a single-byte tag?
# 0x02 = field 0, wire type 2
# That doesn't make sense

# OR... what if the field 32 tag is actually: 82 02 but it got corrupted?
# Let me check if there's a pattern like: 03 82 02 33

print("Checking if the sequence should be: 00 01 03 82 02 33...")
print("That would mean:")
print("  Field 30 value: 00 01 03")
print("  Field 32 tag: 82 02")
print("  Field 32 length: 33 (51 bytes)")
print()

# But the hex shows: 03 00 01 03 02 33
# Not: 03 00 01 03 82 02 33

# UNLESS... the 0x82 got UTF-8 encoded and I didn't catch it!
# Let me check what c2 82 decodes to
test_bytes = bytes.fromhex("c282")
print(f"c2 82 as UTF-8: {test_bytes}")
print(f"c2 82 decoded: 0x{test_bytes[0]:02x} 0x{test_bytes[1]:02x}")

# c2 82 in UTF-8 represents the character U+0082
# When decoded as latin1, it becomes 0x82

# So if the original had 0x82, it would be encoded as c2 82 in UTF-8
# Let me search for "030001c28202" in the original hex

print("\nSearching for '030001c28202' (field 30 value + UTF-8 encoded field 32 tag)...")
if "030001c28202" in original_hex:
    print("Found! The field 32 tag IS UTF-8 encoded!")
    pos = original_hex.index("030001c28202")
    print(f"Position: {pos // 2}")
else:
    print("Not found")

print("\nSearching for '0300010382' (field 30 value + field 32 tag without UTF-8)...")
if "0300010382" in original_hex:
    print("Found! But this means 03 82, not 82 02")
else:
    print("Not found")

print("\n" + "="*80)
print("CONCLUSION:")
print("The sequence '03 00 01 03 02 33' suggests:")
print("  - Field 30 length: 03")
print("  - Field 30 value: 00 01 03")
print("  - Next byte: 02 (this should be part of field 32 tag)")
print("  - Next byte: 33 (this should be field 32 length)")
print()
print("But field 32 tag should be 82 02, not 02 33")
print("This means the HAR hex dump is MISSING the 0x82 byte!")
print("OR the field 32 tag is encoded differently than expected")
