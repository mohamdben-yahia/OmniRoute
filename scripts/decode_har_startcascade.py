#!/usr/bin/env python3
"""Decode StartCascade body from HAR to understand the exact structure."""

import sys

# HAR body (from fiddler/new.har StartCascade request)
har_body_escaped = r"\nÌ\u0002\n\bwindsurf\u0012\u00061.48.2\u001a½\u0001devin-session-token$eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uX2lkIjoid2luZHN1cmYtc2Vzc2lvbi1hNjliYzY5NWQyN2E0NWVjYmRmNjVmYWI5MWQxODZhNiJ9.KyaNgJ8vM6gQswVjs5YMDzSb4Q7lF5313TBlV_tybqM\"\u0002en:\u00062.1.32b\bwindsurf¢\u0001%user-47ba71096f0b498daaf30bd1b11a9b6bò\u0001\u0003\u0000\u0001\u0003\u00023devin-team$account-ae790c86db964e3f9c0296307fcf4691 \u00018\u0000"

# Decode unicode escapes
har_body = har_body_escaped.encode('utf-8').decode('unicode_escape').encode('latin1')

print("HAR StartCascade body analysis:")
print(f"Total length: {len(har_body)} bytes")
print(f"Hex dump:\n{har_body.hex()}")
print()

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

def decode_field(data, offset):
    """Decode a protobuf field."""
    if offset >= len(data):
        return None

    tag, offset = decode_varint(data, offset)
    field_number = tag >> 3
    wire_type = tag & 0x7

    if wire_type == 0:  # Varint
        value, offset = decode_varint(data, offset)
        return {"field": field_number, "type": "varint", "value": value}, offset
    elif wire_type == 2:  # Length-delimited
        length, offset = decode_varint(data, offset)
        value = data[offset:offset+length]
        offset += length
        # Try to decode as string
        try:
            str_value = value.decode('utf-8')
            return {"field": field_number, "type": "string", "value": str_value, "raw": value.hex()}, offset
        except:
            return {"field": field_number, "type": "bytes", "length": length, "raw": value.hex()}, offset
    else:
        return {"field": field_number, "type": f"wire_{wire_type}", "value": "unknown"}, offset

# Decode all fields
offset = 0
fields = []
while offset < len(har_body):
    field, offset = decode_field(har_body, offset)
    if field:
        fields.append(field)

print("Decoded top-level fields:")
for i, field in enumerate(fields):
    print(f"{i+1}. Field {field['field']} (wire type {field['type']})")
    if field.get('type') == 'varint':
        print(f"   Value: {field['value']}")
    elif field.get('type') == 'string':
        print(f"   String value: {repr(field['value'][:100])}..." if len(field['value']) > 100 else f"   String value: {repr(field['value'])}")
        # If it looks like nested protobuf, decode it
        if field['field'] == 1:  # metadata field
            print(f"   Decoding nested metadata message...")
            nested_data = field['value'].encode('latin1')
            nested_offset = 0
            nested_fields = []
            while nested_offset < len(nested_data):
                nested_field, nested_offset = decode_field(nested_data, nested_offset)
                if nested_field:
                    nested_fields.append(nested_field)
            if nested_fields:
                print(f"   Metadata nested fields:")
                for nf in nested_fields:
                    if nf.get('type') == 'string':
                        print(f"      Field {nf['field']}: {repr(nf['value'])}")
                    else:
                        print(f"      Field {nf['field']}: {nf}")

print("\n" + "="*80)
print("Key observations:")
print("- Top-level structure:")
for field in fields:
    print(f"  Field {field['field']}: {field['type']}")
print("\n- Metadata (Field 1) contains:")
print("  Field 1: ideName = 'windsurf'")
print("  Field 2: extensionVersion = '1.48.2'")
print("  Field 3: apiKey = 'devin-session-token$...'")
print("  Field 4: locale = 'en'")
print("  Field 7: ideVersion = '2.1.32'")
print("  Field 12: extensionName = 'windsurf'")
print("  Field 20: userId = 'user-...'")
print("  Field 30: f = bytes")
print("  Field 32: teamId = 'devin-team$...'")
print("\n- Expected top-level Field 4 (source) not found in initial decode!")
print("- This suggests the HAR body might have only Field 1 (metadata)")
print("- Let me check if there are more bytes after Field 1...")

# Check if there are more top-level fields
print(f"\nTotal HAR body length: {len(har_body)} bytes")
print(f"Number of top-level fields decoded: {len(fields)}")
if len(fields) == 1:
    print("WARNING: Only 1 top-level field found! Expected Field 1 (metadata) and Field 4 (source)")
    print("The HAR might be showing an incomplete request or the source field is missing")
else:
    print(f"Found {len(fields)} top-level fields")
