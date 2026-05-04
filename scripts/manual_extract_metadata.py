#!/usr/bin/env python3
"""Manually parse HAR metadata to extract userId, f, and teamId."""

# From the HAR analysis, we know:
# - Field 20 (userId) appears at some point
# - Field 30 (f) appears with bytes 0x00 0x01 0x03
# - Field 32 (teamId) appears with "devin-team$account-ae790c86db964e3f9c0296307fcf4691"

# Let's search the hex for these patterns
har_metadata_hex = "0a0877696e64737572661206312e34382e321ac2bd01646576696e2d73657373696f6e2d746f6b656e2465794a68624763694f694a49557a49314e694973496e523563434936496b705856434a392e65794a7a5a584e7a6157397558326c6b496a6f6964326c755a484e31636d59746332567a63326c76626931684e6a6c69597a59354e5651794e3245304e57566a596d526d4e6a566d595749354d5751784f445a684e694a392e4b79614e674a38764d3667517377566a7335594d447a53623451376c463533313354426c565f747962714d2202656e3a06322e312e3332620877696e6473757266c2a20125757365722d3437626137313039366630623439386461616633306264316231316139623662c3b201030001030233646576696e2d7465616d246163636f756e742d616537393063383664623936346533663963303239363330376663663436393120013800"

data = bytes.fromhex(har_metadata_hex)

print("Searching for field markers in metadata...")
print(f"Total metadata length: {len(data)} bytes\n")

# Field 20 = 0xa0 0x01 (tag for field 20, wire type 2)
# Field 30 = 0xf0 0x01 (tag for field 30, wire type 2) or 0xf2 0x01
# Field 32 = 0x80 0x02 (tag for field 32, wire type 2) or 0x82 0x02

# Let's search for "user-" pattern
user_pattern = b"user-"
user_pos = data.find(user_pattern)
if user_pos >= 0:
    print(f"Found 'user-' at byte {user_pos}")
    # Look backwards for the length and tag
    print(f"Context: {data[max(0, user_pos-5):user_pos+50].hex(' ')}")

    # Extract the full userId
    # The pattern should be: tag + length + "user-..."
    # Let's find the length byte before "user-"
    if user_pos >= 2:
        length_byte = data[user_pos - 1]
        tag_byte = data[user_pos - 2]
        print(f"Tag byte: 0x{tag_byte:02x} = field {tag_byte >> 3}, wire type {tag_byte & 0x7}")
        print(f"Length byte: 0x{length_byte:02x} = {length_byte}")

        if length_byte < 100:  # Reasonable length
            user_id = data[user_pos:user_pos+length_byte].decode('utf-8')
            print(f"Extracted userId: {user_id}")

print("\n" + "="*80)

# Search for "devin-team$" pattern
team_pattern = b"devin-team$"
team_pos = data.find(team_pattern)
if team_pos >= 0:
    print(f"Found 'devin-team$' at byte {team_pos}")
    print(f"Context: {data[max(0, team_pos-5):team_pos+60].hex(' ')}")

    # Extract the full teamId
    if team_pos >= 2:
        length_byte = data[team_pos - 1]
        tag_byte = data[team_pos - 2]
        print(f"Tag byte: 0x{tag_byte:02x} = field {tag_byte >> 3}, wire type {tag_byte & 0x7}")
        print(f"Length byte: 0x{length_byte:02x} = {length_byte}")

        if length_byte < 100:
            team_id = data[team_pos:team_pos+length_byte].decode('utf-8')
            print(f"Extracted teamId: {team_id}")

print("\n" + "="*80)

# Search for field 30 (f) - look for the pattern 0xf2 0x01 (field 30, wire type 2)
# or 0xf0 0x01 (field 30, wire type 0)
print("Searching for field 30 (f)...")
for i in range(len(data) - 1):
    tag = data[i]
    field_num = tag >> 3
    wire_type = tag & 0x7

    if field_num == 30:
        print(f"Found field 30 at byte {i}")
        print(f"Tag: 0x{tag:02x}, wire type: {wire_type}")

        if wire_type == 2:  # Length-delimited
            length = data[i + 1]
            value = data[i + 2:i + 2 + length]
            print(f"Length: {length}")
            print(f"Value (hex): {value.hex(' ')}")
            print(f"Value (bytes): {list(value)}")

print("\n" + "="*80)
print("SUMMARY:")
print("export WINDSURF_USER_ID='user-47ba71096f0b498daaf30bd1b11a9b6b'")
print("export WINDSURF_TEAM_ID='devin-team$account-ae790c86db964e3f9c0296307fcf4691'")
print("# Field 30 (f) is binary data: 0x00 0x01 0x03")
