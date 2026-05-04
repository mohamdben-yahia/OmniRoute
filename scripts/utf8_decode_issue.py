#!/usr/bin/env python3
"""Properly decode fields 30 and 32."""

har_metadata_hex = "0a0877696e64737572661206312e34382e321ac2bd01646576696e2d73657373696f6e2d746f6b656e2465794a68624763694f694a49557a49314e694973496e523563434936496b705856434a392e65794a7a5b584e7a6157397558326c6b496a6f6964326c755a484e31636d59746332567a63326c76626931684e6a6c69597a59354e5651794e3245304e57566a596d526d4e6a566d595749354d5751784f445a684e694a392e4b79614e674a38764d3667517377566a7335594d447a53623451376c463533313354426c565f747962714d2202656e3a06322e312e3332620877696e6473757266c2a20125757365722d3437626137313039366630623439386461616633306264316231316139623662c3b201030001030233646576696e2d7465616d246163636f756e742d616537393063383664623936346533663963303239363330376663663436393120013800"

data = bytes.fromhex(har_metadata_hex)

# We know:
# - Field 20 (userId) ends at byte 274
# - teamId starts at byte 283
# - Bytes 274-282: c3 b2 01 03 00 01 03 02 33

# Let's decode this sequence:
sequence = data[274:283]
print(f"Bytes between userId and teamId: {sequence.hex(' ')}")
print(f"Length: {len(sequence)} bytes")
print()

# c3 b2 could be a 2-byte varint tag, but let's check if it's actually:
# 0xf2 0x01 (field 30, wire type 2)
# But we have 0xc3 0xb2

# Wait! Let me check if the HAR hex has UTF-8 encoding issues
# 0xc3 0xb2 in UTF-8 is the character 'ò' (o with grave)
# This suggests the HAR might have been UTF-8 encoded!

print("Checking if 0xc3 0xb2 is UTF-8 encoded 0xf2...")
# In UTF-8, characters 0x80-0xFF are encoded as multi-byte sequences
# 0xf2 in UTF-8 would be: 0xc3 0xb2
# So the original byte was 0xf2!

print("0xf2 encoded as UTF-8: 0xc3 0xb2 ✓")
print()

# So the actual sequence is:
# 0xf2 0x01 = field 30, wire type 2
# 0x03 = length 3
# 0x00 0x01 0x03 = value
# 0x02 0x33 = ??? This doesn't match field 32 tag

# Wait, let me recalculate field 32 tag:
# Field 32, wire type 2: (32 << 3) | 2 = 258
# 258 as varint: 258 = 0x102
# In varint encoding: 0x82 0x02 (because 258 = 2 + 256 = 2 + (2 << 7))
# But we have 0x02 0x33

# Hmm, 0x02 alone would be field 0, wire type 2
# Let me check if there's UTF-8 encoding on 0x82 too

print("Checking if 0x82 is UTF-8 encoded...")
# 0x82 in UTF-8 would be: 0xc2 0x82
# But we have 0x02

# Let me look at the full sequence again more carefully
print("="*80)
print("Full sequence analysis:")
print("Position 274-282: c3 b2 01 03 00 01 03 02 33")
print()
print("If 0xc3 0xb2 is UTF-8 for 0xf2:")
print("  0xf2 0x01 = field 30, wire type 2")
print("  0x03 = length 3")
print("  0x00 0x01 0x03 = field 30 value")
print("  0x02 0x33 = next field tag and length")
print()
print("But 0x02 is field 0, wire type 2, which doesn't make sense")
print()
print("Alternative: maybe 0x02 is part of a multi-byte varint?")
print("  But 0x02 doesn't have continuation bit set")
print()
print("Let me check the bytes after teamId...")

team_pos = data.find(b"devin-team$")
team_len = 51  # "devin-team$account-ae790c86db964e3f9c0296307fcf4691"
team_end = team_pos + team_len

print(f"\nteamId position: {team_pos}")
print(f"teamId length: {team_len}")
print(f"teamId ends at: {team_end}")
print(f"Bytes after teamId: {data[team_end:team_end+5].hex(' ')}")

# The bytes after teamId are: 20 01 38 00
# 0x20 = field 4, wire type 0 (varint)
# 0x01 = value 1
# 0x38 = field 7, wire type 0 (varint)
# 0x00 = value 0

print("\nBytes after teamId decoded:")
print("  0x20 = field 4, wire type 0 (varint)")
print("  0x01 = value 1 (this is the top-level 'source' field!)")
print("  0x38 = field 7, wire type 0 (varint)")
print("  0x00 = value 0")

print("\n" + "="*80)
print("CONCLUSION:")
print("The HAR hex dump has UTF-8 encoding applied to non-ASCII bytes!")
print("We need to decode the UTF-8 first, then parse the protobuf.")
