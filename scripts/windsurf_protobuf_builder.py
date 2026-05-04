#!/usr/bin/env python3
"""
Windsurf Protobuf Message Builder
Constructs proper Protobuf messages for Windsurf API calls.
"""

import struct
import uuid

def encode_varint(value):
    """Encode an integer as a protobuf varint."""
    result = bytearray()
    while value > 0x7f:
        result.append((value & 0x7f) | 0x80)
        value >>= 7
    result.append(value & 0x7f)
    return bytes(result)

def encode_string(field_number, value):
    """Encode a string field in protobuf format."""
    if isinstance(value, str):
        value = value.encode('utf-8')
    
    # Field tag: (field_number << 3) | wire_type
    # Wire type 2 = length-delimited (for strings)
    tag = (field_number << 3) | 2
    
    result = encode_varint(tag)
    result += encode_varint(len(value))
    result += value
    
    return result

def encode_message(field_number, message_bytes):
    """Encode a nested message field."""
    tag = (field_number << 3) | 2
    result = encode_varint(tag)
    result += encode_varint(len(message_bytes))
    result += message_bytes
    return result

def build_metadata():
    """Build the metadata message required by all requests."""
    metadata = b""
    
    # Field 1: ide_name = "windsurf"
    metadata += encode_string(1, "windsurf")
    
    # Field 2: ide_version = "1.48.2"
    metadata += encode_string(2, "1.48.2")
    
    # Field 3: extension_version = "2.1.32"
    metadata += encode_string(3, "2.1.32")
    
    # Field 822: swe_version = "swe-1-6"
    metadata += encode_string(822, "swe-1-6")
    
    return metadata

def build_start_cascade_request():
    """Build a StartCascade request."""
    request = b""
    
    # Add metadata (field number from error message)
    metadata = build_metadata()
    request += encode_message(1, metadata)  # Assuming metadata is field 1
    
    return request

def build_send_user_cascade_message_request(cascade_id, message_text):
    """Build a SendUserCascadeMessage request."""
    request = b""
    
    # Field 1: cascade_id (UUID string)
    request += encode_string(1, cascade_id)
    
    # Field 2: message text
    request += encode_string(2, message_text)
    
    # Add metadata
    metadata = build_metadata()
    request += encode_message(10, metadata)  # Guessing field number
    
    return request

def main():
    print("=" * 60)
    print("  WINDSURF PROTOBUF MESSAGE BUILDER")
    print("=" * 60)
    
    # Build StartCascade request
    print("\n📦 Building StartCascade request...")
    start_cascade_payload = build_start_cascade_request()
    print(f"   Length: {len(start_cascade_payload)} bytes")
    print(f"   Hex: {start_cascade_payload.hex()[:100]}...")
    
    # Save to file
    with open("windsurf_start_cascade.bin", "wb") as f:
        f.write(start_cascade_payload)
    print(f"   ✅ Saved to: windsurf_start_cascade.bin")
    
    # Build SendUserCascadeMessage request
    print("\n📦 Building SendUserCascadeMessage request...")
    cascade_id = str(uuid.uuid4())
    message = "Hello from Python!"
    send_message_payload = build_send_user_cascade_message_request(cascade_id, message)
    print(f"   Cascade ID: {cascade_id}")
    print(f"   Message: {message}")
    print(f"   Length: {len(send_message_payload)} bytes")
    print(f"   Hex: {send_message_payload.hex()[:100]}...")
    
    # Save to file
    with open("windsurf_send_message.bin", "wb") as f:
        f.write(send_message_payload)
    print(f"   ✅ Saved to: windsurf_send_message.bin")
    
    print("\n" + "=" * 60)
    print("  NEXT STEP")
    print("=" * 60)
    print("\nUse these binary payloads with windsurf_grpc_test.py")
    print("to test the actual API calls.\n")

if __name__ == "__main__":
    main()
