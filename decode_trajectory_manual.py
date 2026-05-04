#!/usr/bin/env python3
"""Manually decode trajectory response to find modelRouterUid."""
import sys
import os
import time
sys.path.insert(0, 'scripts')
import windsurf_direct_probe as p

os.environ['WINDSURF_USER_ID'] = 'user-a0877fa492bb4eb3b0697a7c72bbb97b'
os.environ['WINDSURF_TEAM_ID'] = 'devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be'
os.environ['WINDSURF_METADATA_F'] = '000103'
os.environ['WINDSURF_SESSION_ID'] = '20924'
os.environ['WINDSURF_SWE_VERSION'] = 'swe-1-6'
os.environ['WINDSURF_CSRF_TOKEN'] = 'd1dfed32-5615-4751-9a46-f08c30e9700b'

token = p.resolve_auth_context_for_mode('ls_emulator')['token']

# Start cascade
start_req, _ = p.build_start_cascade_probe_request(token)
_, start_result = p.run_request(start_req)
cascade_id = p.extract_cascade_id_from_start_result(start_result)
print(f'Cascade ID: {cascade_id}')

# Send message
send_req, _ = p.build_send_user_cascade_message_probe_request(token, cascade_id)
p.run_request(send_req)

# Wait and get trajectory
time.sleep(3)
traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
_, traj_result = p.run_request(traj_req)

body_hex = traj_result.get('bodyHex', '')
body_bytes = bytes.fromhex(body_hex)

print(f'Body size: {len(body_bytes)} bytes')
print(f'First 200 bytes hex: {body_hex[:400]}')
print()

# Search for "kimi-k2-6" which is the requested model
if b'kimi-k2-6' in body_bytes:
    idx = body_bytes.index(b'kimi-k2-6')
    print(f'Found "kimi-k2-6" at byte offset {idx}')
    print(f'Context (50 bytes before): {body_bytes[max(0, idx-50):idx].hex()}')
    print(f'Context (50 bytes after): {body_bytes[idx:idx+50].hex()}')
    print()

# Search for UUID patterns (modelRouterUid format)
import re
uuid_pattern = rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
matches = list(re.finditer(uuid_pattern, body_bytes))
print(f'Found {len(matches)} UUID patterns:')
for i, match in enumerate(matches[:5]):
    uuid_str = match.group(0).decode('utf-8')
    print(f'  {i+1}. {uuid_str} at offset {match.start()}')
