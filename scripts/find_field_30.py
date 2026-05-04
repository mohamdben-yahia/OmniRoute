#!/usr/bin/env python3
"""Decode the bytes around userId to find field 30 (f)."""

# From the context: c2 a2 01 25 75 73 65 72 ... c3 b2 01 03 00 01 03 02 33 64 65 76 69 6e

# c2 a2 01 = tag for field 20 (userId)
#   0xa2 = 162 = 10100010b
#   With continuation: 0xc2 0xa2 0x01
#   Let's decode: (0xc2 & 0x7F) | ((0xa2 & 0x7F) << 7) | ((0x01 & 0x7F) << 14)
#   = 0x42 | (0x22 << 7) | (0x01 << 14)
#   = 66 | 4352 | 16384 = 20802
#   Field number = 20802 >> 3 = 2600, wire type = 2
#   That's wrong...

# Let me try a different approach - field 20 with wire type 2 should be:
# (20 << 3) | 2 = 162 = 0xa2
# But we have 0xc2 0xa2 0x01 which is a multi-byte varint

# Actually, looking at the pattern:
# 0xa2 0x01 could be: (0xa2 & 0x7F) | ((0x01 & 0x7F) << 7) = 34 | 128 = 162
# Field 162 >> 3 = 20, wire type = 162 & 0x7 = 2 ✓

# So the pattern is:
# 0xa2 0x01 = field 20, wire type 2 (userId)
# 0x25 = length 37
# "user-47ba71096f0b498daaf30bd1b11a9b6b"
# 0xf2 0x01 = field 30, wire type 2 (f)
# 0x03 = length 3
# 0x00 0x01 0x03 = the f value

# Let's verify:
print("Field 20 (userId) tag calculation:")
print(f"  (20 << 3) | 2 = {(20 << 3) | 2} = 0x{(20 << 3) | 2:02x}")
print(f"  As varint: 0xa2 0x01")
print()

print("Field 30 (f) tag calculation:")
print(f"  (30 << 3) | 2 = {(30 << 3) | 2} = 0x{(30 << 3) | 2:02x}")
print(f"  As varint: 0xf2 0x01")
print()

print("Field 32 (teamId) tag calculation:")
print(f"  (32 << 3) | 2 = {(32 << 3) | 2} = 0x{(32 << 3) | 2:02x}")
print(f"  As varint: 0x82 0x02")
print()

# Now let's search for 0xf2 0x01 in the metadata
har_metadata_hex = "0a0877696e64737572661206312e34382e321ac2bd01646576696e2d73657373696f6e2d746f6b656e2465794a68624763694f694a49557a49314e694973496e523563434936496b705856434a392e65794a7a5b584e7a6157397558326c6b496a6f6964326c755a484e31636d59746332567a63326c76626931684e6a6c69597a59354e5751794e3245304e57566a596d526d4e6a566d595749354d5751784f445a684e694a392e4b79614e674a38764d3667517377566a7335594d447a53623451376c463533313354426c565f747962714d2202656e3a06322e312e3332620877696e6473757266c2a20125757365722d3437626137313039366630623439386461616633306264316231316139623662c3b201030001030233646576696e2d7465616d246163636f756e742d616537393063383664623936346533663963303239363330376663663436393120013800"

data = bytes.fromhex(har_metadata_hex)

print("Searching for field 30 (0xf2 0x01)...")
for i in range(len(data) - 1):
    if data[i] == 0xf2 and data[i+1] == 0x01:
        print(f"Found at byte {i}")
        length = data[i+2]
        value = data[i+3:i+3+length]
        print(f"Length: {length}")
        print(f"Value: {value.hex(' ')}")
        print(f"Value as list: {list(value)}")
        break

print("\nSearching for field 32 (0x82 0x02)...")
for i in range(len(data) - 1):
    if data[i] == 0x82 and data[i+1] == 0x02:
        print(f"Found at byte {i}")
        length = data[i+2]
        value = data[i+3:i+3+length]
        print(f"Length: {length}")
        print(f"Value: {value.decode('utf-8')}")
        break

print("\n" + "="*80)
print("FINAL VALUES:")
print("export WINDSURF_USER_ID='user-47ba71096f0b498daaf30bd1b11a9b6b'")
print("export WINDSURF_TEAM_ID='devin-team$account-ae790c86db964e3f9c0296307fcf4691'")
print("# For field 30 (f), we need to set it as hex bytes in the probe")
