#!/usr/bin/env python3
"""Compare HAR StartCascade with our probe's StartCascade."""

import sys
sys.path.insert(0, 'scripts')

# Import the probe's builder
from windsurf_direct_probe import build_start_cascade_request, get_metadata_payload

# Build what our probe sends
token = "devin-session-token$eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uX2lkIjoid2luZHN1cmYtc2Vzc2lvbi1hNjliYzY5NWQyN2E0NWVjYmRmNjVmYWI5MWQxODZhNiJ9.KyaNgJ8vM6gQswVjs5YMDzSb4Q7lF5313TBlV_tybqM"
probe_body, preview = build_start_cascade_request(token)

print("="*80)
print("PROBE'S StartCascade body:")
print(f"Length: {len(probe_body)} bytes")
print(f"Hex: {probe_body.hex()}")
print()

# HAR body
har_hex = "0ac38c020a0877696e64737572661206312e34382e321ac2bd01646576696e2d73657373696f6e2d746f6b656e2465794a68624763694f694a49557a49314e694973496e523563434936496b705856434a392e65794a7a5a584e7a6157397558326c6b496a6f6964326c755a484e31636d59746332567a63326c76626931684e6a6c69597a59354e5751794e3245304e57566a596d526d4e6a566d595749354d5751784f445a684e694a392e4b79614e674a38764d3667517377566a7335594d447a53623451376c463533313354426c565f747962714d2202656e3a06322e312e3332620877696e6473757266c2a20125757365722d3437626137313039366630623439386461616633306264316231316139623662c3b201030001030233646576696e2d7465616d246163636f756e742d616537393063383664623936346533663963303239363330376663663436393120013800"
har_body = bytes.fromhex(har_hex)

print("="*80)
print("HAR's StartCascade body:")
print(f"Length: {len(har_body)} bytes")
print(f"Hex: {har_body.hex()}")
print()

print("="*80)
print("COMPARISON:")
print(f"Probe length: {len(probe_body)} bytes")
print(f"HAR length: {len(har_body)} bytes")
print(f"Difference: {len(har_body) - len(probe_body)} bytes")
print()

if probe_body == har_body:
    print("✅ IDENTICAL! The bodies match perfectly.")
else:
    print("❌ DIFFERENT! Let's find the differences...")

    # Find first difference
    min_len = min(len(probe_body), len(har_body))
    first_diff = None
    for i in range(min_len):
        if probe_body[i] != har_body[i]:
            first_diff = i
            break

    if first_diff is not None:
        print(f"\nFirst difference at byte {first_diff}:")
        start = max(0, first_diff - 10)
        end = min(min_len, first_diff + 10)
        print(f"Probe [{start}:{end}]: {probe_body[start:end].hex(' ')}")
        print(f"HAR   [{start}:{end}]: {har_body[start:end].hex(' ')}")
    elif len(probe_body) != len(har_body):
        print(f"\nBodies match up to byte {min_len}, but lengths differ")
        if len(probe_body) > len(har_body):
            print(f"Probe has extra bytes: {probe_body[min_len:].hex(' ')}")
        else:
            print(f"HAR has extra bytes: {har_body[min_len:].hex(' ')}")

print("\n" + "="*80)
print("KEY FINDINGS:")
print("- HAR has Field 4 (source) at byte 338 with value 1")
print("- HAR has Field 7 at byte 340 with value 0")
print("- HAR metadata length is approximately 336 bytes")
print("- Our probe should match this structure exactly")
