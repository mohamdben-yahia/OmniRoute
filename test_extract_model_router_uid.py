#!/usr/bin/env python3
"""Extract modelRouterUid from GetCascadeTrajectory protobuf response."""
import re

def extract_model_router_uid_from_trajectory_body(body_bytes: bytes) -> str | None:
    """
    Extract modelRouterUid from GetCascadeTrajectory response body.

    The trajectory response contains a protobuf structure where modelRouterUid
    appears as a UUID string (field 12) before the assignedModelUid field.

    Strategy: Search for UUID patterns in the response and return the first one
    that appears before a known model identifier pattern.
    """
    if not body_bytes:
        return None

    # Find all UUID patterns in the response
    uuid_pattern = rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    uuid_matches = list(re.finditer(uuid_pattern, body_bytes))

    if not uuid_matches:
        return None

    # Look for model identifier patterns (e.g., "kimi-k2-6", "claude-", "gpt-")
    model_patterns = [
        rb'kimi-[a-z0-9-]+',
        rb'claude-[a-z0-9-]+',
        rb'gpt-[a-z0-9-]+',
        rb'gemini-[a-z0-9-]+',
    ]

    model_match = None
    for pattern in model_patterns:
        match = re.search(pattern, body_bytes)
        if match:
            model_match = match
            break

    if not model_match:
        # No model identifier found, return first UUID
        return uuid_matches[0].group(0).decode('utf-8')

    # Find the UUID that appears closest before the model identifier
    model_offset = model_match.start()
    candidate_uuids = [m for m in uuid_matches if m.start() < model_offset]

    if not candidate_uuids:
        # No UUID before model identifier, return first UUID
        return uuid_matches[0].group(0).decode('utf-8')

    # Return the UUID closest to (but before) the model identifier
    closest_uuid = max(candidate_uuids, key=lambda m: m.start())
    return closest_uuid.group(0).decode('utf-8')


# Test with known trajectory response
test_hex = '0ad3330a2465343165343332612d323830662d346533382d393732632d363264663164303438656164124b082220032a420a0b08868ddecf0610fce3ca451805420b08868ddecf0610c0c2895b622434333037386330622d376565642d343237612d616436662d626132633065643631663938da0200125c080e20032a410a0b08868ddecf0610bc91c2551804622434333037386330622d376565642d343237612d616436662d626132633065643631663938e201096b696d692d6b322d36'
test_body = bytes.fromhex(test_hex)

result = extract_model_router_uid_from_trajectory_body(test_body)
print(f'Extracted modelRouterUid: {result}')
print(f'Expected: 43078c0b-7eed-427a-ad6f-ba2c0ed61f98')
print(f'Match: {result == "43078c0b-7eed-427a-ad6f-ba2c0ed61f98"}')
