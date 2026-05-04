#!/usr/bin/env python3
"""Extract userId, f, and teamId from HAR metadata for use in probe."""

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

# HAR full message - need to extract field 1 (metadata) first
har_hex = "0ac38c020a0877696e64737572661206312e34382e321ac2bd01646576696e2d73657373696f6e2d746f6b656e2465794a68624763694f694a49557a49314e694973496e523563434936496b705856434a392e65794a7a5a584e7a6157397558326c6b496a6f6964326c755a484e31636d59746332567a63326c76626931684e6a6c69597a59354e5751794e3245304e57566a596d526d4e6a566d595749354d5751784f445a684e694a392e4b79614e674a38764d3667517377566a7335594d447a53623451376c463533313354426c565f747962714d2202656e3a06322e312e3332620877696e6473757266c2a20125757365722d3437626137313039366630623439386461616633306264316231316139623662c3b201030001030233646576696e2d7465616d246163636f756e742d616537393063383664623936346533663963303239363330376663663436393120013800"
har_full = bytes.fromhex(har_hex)

# Decode top level to get field 1 (metadata)
top_fields = decode_metadata(har_full)
if 1 not in top_fields or top_fields[1]['type'] != 'string':
    print("ERROR: Could not find metadata field (field 1)")
    sys.exit(1)

# The metadata field is itself a protobuf message, decode it
metadata_bytes = top_fields[1]['value'].encode('latin1')
har_fields = decode_metadata(metadata_bytes)

print("HAR Metadata Fields:")
for field_num in sorted(har_fields.keys()):
    field = har_fields[field_num]
    if field['type'] == 'string':
        print(f"  Field {field_num}: {repr(field['value'])}")
    elif field['type'] == 'bytes':
        print(f"  Field {field_num}: bytes({field['value']})")
    else:
        print(f"  Field {field_num}: {field}")

print("\n" + "="*80)
print("EXTRACTED VALUES FOR PROBE:")
print(f"export WINDSURF_USER_ID='{har_fields.get(20, {}).get('value', '')}'")
f_value = har_fields.get(30, {}).get('value', '')
if f_value:
    f_hex = ''.join(f'\\x{b:02x}' for b in f_value.encode('latin1'))
    print(f"export WINDSURF_METADATA_F=$'{f_hex}'")
else:
    print(f"export WINDSURF_METADATA_F=''")
# teamId is field 32, but may appear as field 0 due to decode issue
team_id = har_fields.get(32, {}).get('value', '') or har_fields.get(0, {}).get('value', '')
print(f"export WINDSURF_TEAM_ID='{team_id}'")

print("\n" + "="*80)
print("FIELD 30 (f) ANALYSIS:")
if 30 in har_fields:
    f_field = har_fields[30]
    if f_field['type'] == 'bytes':
        f_bytes = bytes.fromhex(f_field['value'])
        print(f"  Raw bytes: {f_bytes.hex(' ')}")
        print(f"  Length: {len(f_bytes)} bytes")
        print(f"  As integers: {list(f_bytes)}")
        print(f"  This appears to be a binary feature flag field")
