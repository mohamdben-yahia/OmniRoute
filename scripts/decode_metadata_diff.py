#!/usr/bin/env python3
"""Decode both metadata messages to find missing fields."""

import sys
sys.path.insert(0, 'scripts')

def decode_varint(data, offset):
    """Decode a varint from data starting at offset."""
    result = 0
    shift = 0
    while offset < len(data):
        byte = data[offset]
        offset += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return result, offset
        shift += 7
    return result, offset

def decode_metadata(data):
    """Decode metadata message fields."""
    offset = 0
    fields = {}

    while offset < len(data):
        if offset >= len(data):
            break

        tag, offset = decode_varint(data, offset)
        field_number = tag >> 3
        wire_type = tag & 0x7

        if wire_type == 0:  # Varint
            value, offset = decode_varint(data, offset)
            fields[field_number] = {"type": "varint", "value": value}
        elif wire_type == 2:  # Length-delimited (string/bytes)
            length, offset = decode_varint(data, offset)
            value = data[offset:offset+length]
            offset += length
            try:
                str_value = value.decode('utf-8')
                fields[field_number] = {"type": "string", "value": str_value}
            except:
                fields[field_number] = {"type": "bytes", "value": value.hex()}

    return fields

# HAR metadata
har_hex = "0ac38c020a0877696e64737572661206312e34382e321ac2bd01646576696e2d73657373696f6e2d746f6b656e2465794a68624763694f694a49557a49314e694973496e523563434936496b705856434a392e65794a7a5a584e7a6157397558326c6b496a6f6964326c755a484e31636d59746332567a63326c76626931684e6a6c69597a59354e5751794e3245304e57566a596d526d4e6a566d595749354d5751784f445a684e694a392e4b79614e674a38764d3667517377566a7335594d447a53623451376c463533313354426c565f747962714d2202656e3a06322e312e3332620877696e6473757266c2a20125757365722d3437626137313039366630623439386461616633306264316231316139623662c3b201030001030233646576696e2d7465616d246163636f756e742d616537393063383664623936346533663963303239363330376663663436393120013800"
har_body = bytes.fromhex(har_hex)

# Extract metadata from HAR (skip field 1 tag and length)
har_metadata_length_bytes = []
offset = 1
while offset < len(har_body):
    byte = har_body[offset]
    har_metadata_length_bytes.append(byte)
    offset += 1
    if not (byte & 0x80):
        break

har_metadata_length = 0
shift = 0
for byte in har_metadata_length_bytes:
    har_metadata_length |= (byte & 0x7F) << shift
    shift += 7

har_metadata = har_body[offset:offset+har_metadata_length]

# Probe metadata
probe_hex = "0a80020a0877696e64737572661207312e3130382e321abd01646576696e2d73657373696f6e2d746f6b656e2465794a68624763694f694a49557a49314e694973496e523563434936496b705856434a392e65794a7a5a584e7a6157397558326c6b496a6f6964326c755a484e31636d59746332567a63326c76626931684e6a6c69597a59354e5751794e3245304e57566a596d526d4e6a566d595749354d5751784f445a684e694a392e4b79614e674a38764d3667517377566a7335594d447a53623451376c463533313354426c565f747962714d2202656e3a07312e3130382e3352146f627365727665642d73657373696f6e2d616263620877696e64737572662001"
probe_body = bytes.fromhex(probe_hex)

probe_metadata_length_bytes = []
offset = 1
while offset < len(probe_body):
    byte = probe_body[offset]
    probe_metadata_length_bytes.append(byte)
    offset += 1
    if not (byte & 0x80):
        break

probe_metadata_length = 0
shift = 0
for byte in probe_metadata_length_bytes:
    probe_metadata_length |= (byte & 0x7F) << shift
    shift += 7

probe_metadata = probe_body[offset:offset+probe_metadata_length]

print("HAR Metadata Fields:")
har_fields = decode_metadata(har_metadata)
for field_num in sorted(har_fields.keys()):
    field = har_fields[field_num]
    if field['type'] == 'string':
        print(f"  Field {field_num}: {repr(field['value'][:50])}..." if len(field['value']) > 50 else f"  Field {field_num}: {repr(field['value'])}")
    else:
        print(f"  Field {field_num}: {field}")

print("\nProbe Metadata Fields:")
probe_fields = decode_metadata(probe_metadata)
for field_num in sorted(probe_fields.keys()):
    field = probe_fields[field_num]
    if field['type'] == 'string':
        print(f"  Field {field_num}: {repr(field['value'][:50])}..." if len(field['value']) > 50 else f"  Field {field_num}: {repr(field['value'])}")
    else:
        print(f"  Field {field_num}: {field}")

print("\n" + "="*80)
print("MISSING FIELDS IN PROBE:")
missing = set(har_fields.keys()) - set(probe_fields.keys())
for field_num in sorted(missing):
    field = har_fields[field_num]
    if field['type'] == 'string':
        print(f"  Field {field_num}: {repr(field['value'][:50])}..." if len(field['value']) > 50 else f"  Field {field_num}: {repr(field['value'])}")
    else:
        print(f"  Field {field_num}: {field}")

print("\n" + "="*80)
print("FIELD MAPPING:")
print("  Field 1: ideName")
print("  Field 2: extensionVersion")
print("  Field 3: apiKey (session token)")
print("  Field 4: locale")
print("  Field 7: ideVersion")
print("  Field 12: extensionName")
print("  Field 20: userId")
print("  Field 30: f (feature flags?)")
print("  Field 32: teamId")
