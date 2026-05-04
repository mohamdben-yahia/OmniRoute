#!/usr/bin/env python3
"""Decode protobuf structure around modelRouterUid."""

# Context bytes around kimi-k2-6
body_hex = '0610bc91c2551804622434333037386330622d376565642d343237612d616436662d626132633065643631663938e201096b696d692d6b322d36'
body = bytes.fromhex(body_hex)

print('Decoding protobuf structure:')
print(f'Total bytes: {len(body)}')
print()

idx = 0
while idx < len(body):
    if idx >= len(body):
        break

    b = body[idx]
    field_num = b >> 3
    wire_type = b & 0x07

    print(f'Offset {idx}: 0x{b:02x} -> field {field_num}, wire type {wire_type}', end='')

    if wire_type == 0:  # varint
        idx += 1
        value = 0
        shift = 0
        while idx < len(body):
            byte = body[idx]
            value |= (byte & 0x7f) << shift
            idx += 1
            shift += 7
            if (byte & 0x80) == 0:
                break
        print(f' (varint: {value})')
    elif wire_type == 2:  # length-delimited
        idx += 1
        if idx >= len(body):
            break
        length = body[idx]
        idx += 1
        if idx + length > len(body):
            print(f' (length: {length}, TRUNCATED)')
            break
        value = body[idx:idx+length]
        print(f' (length: {length})')
        try:
            decoded = value.decode('utf-8')
            print(f'    UTF-8: "{decoded}"')
        except:
            print(f'    Hex: {value.hex()}')
        idx += length
    else:
        print(f' (unknown wire type)')
        idx += 1

    if idx > 100:
        print('...')
        break

print()
print('Field 98 (0x62) = modelRouterUid: 43078c0b-7eed-427a-ad6f-ba2c0ed61f98')
print('Field 226 (0xe2) = assignedModelUid: kimi-k2-6')
