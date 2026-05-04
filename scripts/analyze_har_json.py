#!/usr/bin/env python3
"""Check if field 32 can use a single-byte tag."""

# Single-byte tags work for field numbers 0-15
# For field 32, we need a multi-byte tag

# But wait - let me check the actual bytes in the sequence again
# The sequence after field 30 is: 02 33 64 65 76 69 6e 2d 74 65 61 6d
#                                  d  e  v  i  n  -  t  e  a  m

# 0x02 = field 0, wire type 2 (doesn't make sense)
# 0x33 = 51 decimal = 'd' in ASCII

# But "devin-team$..." is 51 bytes long!
# So maybe the structure is different

# What if field 32 uses a DIFFERENT tag encoding?
# Let me check: maybe it's 0x02 followed by a varint for the field number?

# OR... what if the HAR is showing the WRONG bytes?
# Let me go back to the original HAR JSON and check the exact text

print("Analyzing the HAR postData.text field...")
print()

# From the HAR: ...user-47ba71096f0b498daaf30bd1b11a9b6bò\u0001\u0003\u0000\u0001\u0003\u00023devin-team$...
# Let's decode this character by character:

har_text_fragment = r"user-47ba71096f0b498daaf30bd1b11a9b6bò\u0001\u0003\u0000\u0001\u0003\u00023devin-team$account-ae790c86db964e3f9c0296307fcf4691 \u00018\u0000"

print(f"HAR text fragment: {har_text_fragment}")
print()

# Decode it
decoded = har_text_fragment.encode('utf-8').decode('unicode_escape')
print(f"Decoded: {repr(decoded)}")
print(f"Decoded bytes: {decoded.encode('latin1').hex(' ')}")
print()

# Let's break it down:
# user-47ba71096f0b498daaf30bd1b11a9b6b = userId (37 bytes)
# ò = 0xf2
# \u0001 = 0x01
# \u0003 = 0x03
# \u0000 = 0x00
# \u0001 = 0x01
# \u0003 = 0x03
# \u0002 = 0x02
# 3 = 0x33
# devin-team$account-ae790c86db964e3f9c0296307fcf4691 = teamId (51 bytes)
# (space) = 0x20
# \u0001 = 0x01
# 8 = 0x38
# \u0000 = 0x00

print("Byte-by-byte breakdown:")
print("  userId: 37 bytes")
print("  0xf2 0x01 = field 30 tag")
print("  0x03 = length 3")
print("  0x00 0x01 0x03 = field 30 value")
print("  0x02 0x33 = ??? (should be field 32 tag)")
print("  'devin-team$...' = 51 bytes")
print("  0x20 = field 4 tag (top-level source field!)")
print("  0x01 = value 1")
print("  0x38 = field 7 tag")
print("  0x00 = value 0")
print()

print("="*80)
print("WAIT! I see it now!")
print()
print("The sequence '02 33' is NOT the field 32 tag!")
print("It's: \\u0002 followed by '3'")
print("\\u0002 = 0x02")
print("'3' = 0x33")
print()
print("But in the HAR JSON, it might actually be: \\u00823")
print("Which would be: 0x82 followed by '3' (0x33)")
print()
print("Let me check the ORIGINAL HAR file to see the exact JSON...")

# The issue is that when the HAR was saved, bytes 0x80-0xFF might have been
# encoded as \uXXXX escapes, and I'm not seeing them correctly

print("\nLet me try a different approach - assume field 32 tag is 0x82 0x02")
print("and manually construct the correct sequence:")
print()

correct_sequence = bytes.fromhex("f2 01 03 00 01 03 82 02 33")
print(f"Correct sequence: {correct_sequence.hex(' ')}")
print("  f2 01 = field 30 tag")
print("  03 = field 30 length")
print("  00 01 03 = field 30 value")
print("  82 02 = field 32 tag")
print("  33 = field 32 length (51 bytes)")
print()

print("="*80)
print("CONCLUSION:")
print("The HAR postData.text has the byte 0x82 encoded as \\u0082")
print("But when I decoded it, I only saw \\u0002")
print("This means the HAR JSON might have: ...\\u0003\\u0082\\u00023devin-team$...")
print("Not: ...\\u0003\\u00023devin-team$...")
