#!/usr/bin/env python3
"""Analyze the HAR hex dump byte by byte."""

# From the hex dump output
hex_dump = "0ac38c020a0877696e64737572661206312e34382e321ac2bd01646576696e2d73657373696f6e2d746f6b656e2465794a68624763694f694a49557a49314e694973496e523563434936496b705856434a392e65794a7a5a584e7a6157397558326c6b496a6f6964326c755a484e31636d59746332567a63326c76626931684e6a6c69597a59354e5751794e3245304e57566a596d526d4e6a566d595749354d5751784f445a684e694a392e4b79614e674a38764d3667517377566a7335594d447a53623451376c463533313354426c565f747962714d2202656e3a06322e312e3332620877696e6473757266c2a20125757365722d3437626137313039366630623439386461616633306264316231316139623662c3b201030001030233646576696e2d7465616d246163636f756e742d616537393063383664623936346533663963303239363330376663663436393120013800"

data = bytes.fromhex(hex_dump)
print(f"Total length: {len(data)} bytes\n")

# Let me manually parse this
print("Manual parsing:")
print(f"Byte 0: 0x{data[0]:02x} = {data[0]:08b}b")
print(f"  Field number: {data[0] >> 3} = 1")
print(f"  Wire type: {data[0] & 0x7} = 2 (length-delimited)")

# The next bytes are the length as a varint
# 0x0a = field 1, wire type 2
# Next should be length
print(f"\nByte 1: 0x{data[1]:02x} = {data[1]:08b}b = {data[1]}")
print(f"  MSB set? {bool(data[1] & 0x80)}")

# Wait, let me look at the pattern differently
# The hex starts with: 0a c3 8c 02
# 0x0a = field 1, wire type 2
# But c3 8c 02 looks wrong for a length

# Let me check if this is UTF-8 encoded wrongly
print("\n" + "="*80)
print("Checking if the hex is actually correct...")
print(f"First 20 bytes: {data[:20].hex(' ')}")
print(f"First 20 bytes as raw: {data[:20]}")

# The HAR shows Content-Length: 339, but we have 342 bytes
# Let me try a different approach - look for the pattern that should be there
print("\n" + "="*80)
print("Looking for field 4 (source) pattern...")
print("Field 4 with varint value 1 would be: 0x20 0x01")
print("Searching for 0x20 0x01 in the data...")

for i in range(len(data) - 1):
    if data[i] == 0x20 and data[i+1] == 0x01:
        print(f"Found at byte {i}: 0x20 0x01")
        print(f"Context: ...{data[max(0,i-5):i+5].hex(' ')}...")

print("\nSearching for 0x20 0x00 (source=0)...")
for i in range(len(data) - 1):
    if data[i] == 0x20 and data[i+1] == 0x00:
        print(f"Found at byte {i}: 0x20 0x00")
        print(f"Context: ...{data[max(0,i-5):i+5].hex(' ')}...")

print("\nLast 10 bytes of data:")
print(data[-10:].hex(' '))
print(f"Last bytes decoded: {data[-10:]}")
