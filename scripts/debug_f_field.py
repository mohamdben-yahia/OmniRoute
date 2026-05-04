#!/usr/bin/env python3
"""Debug script to verify f field encoding."""
import sys
import os
sys.path.insert(0, 'scripts')
import windsurf_direct_probe as m

# Set the same env vars as the test
os.environ['WINDSURF_USER_ID'] = 'user-47ba71096f0b498daaf30bd1b11a9b6b'
os.environ['WINDSURF_METADATA_F'] = '\x00\x01\x03'
os.environ['WINDSURF_TEAM_ID'] = 'devin-team$account-ae790c86db964e3f9c0296307fcf4691'
os.environ['WINDSURF_SESSION_ID'] = '20924'

token = m.resolve_auth_context_for_mode('ls_emulator')['token']
metadata = m.get_metadata_payload(token)
body, preview = m.build_start_cascade_request(token)

print(f"Metadata f value: {repr(metadata.get('f'))}")
print(f"Metadata f type: {type(metadata.get('f'))}")
print(f"Body length: {len(body)} bytes")
print(f"Body hex: {body.hex()}")
print()

# Check if f field bytes appear in body
f_value = metadata.get('f')
if f_value:
    if isinstance(f_value, str):
        f_bytes = f_value.encode('latin1')
    else:
        f_bytes = bytes(f_value)
    print(f"Looking for f field bytes: {f_bytes.hex()}")
    if f_bytes.hex() in body.hex():
        print("✓ f field IS present in body")
    else:
        print("✗ f field NOT found in body")
