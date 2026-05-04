#!/usr/bin/env python3
"""Test with a different model to avoid rate limit."""
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
os.environ['WINDSURF_CSRF_TOKEN'] = 'a5d004fc-a32d-49ab-ab4d-3d27db4167f9'
os.environ['WINDSURF_CHAT_TEXT'] = 'hello, respond with a short greeting'

token = p.resolve_auth_context_for_mode('ls_emulator')['token']

# Start cascade
print('=== Starting Cascade ===')
start_req, _ = p.build_start_cascade_probe_request(token)
_, start_result = p.run_request(start_req)
cascade_id = p.extract_cascade_id_from_start_result(start_result)
print(f'Cascade ID: {cascade_id}')

if not cascade_id:
    print('Failed to create cascade')
    sys.exit(1)

# Get trajectory to see what model was assigned
print('\n=== Getting Initial Trajectory ===')
traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
_, traj_result = p.run_request(traj_req)

# Try to extract model info
body_hex = traj_result.get('bodyHex', '')
if body_hex:
    body_bytes = bytes.fromhex(body_hex)
    model_router_uid = p.extract_model_router_uid_from_trajectory_body(body_bytes)
    print(f'Model Router UID: {model_router_uid}')

# Send message
print('\n=== Sending Message ===')
send_req, _ = p.build_send_user_cascade_message_probe_request(token, cascade_id)
_, send_result = p.run_request(send_req)
print(f'Status: {send_result.get("status")}')

# Wait for response
print('\n=== Waiting for Response ===')
time.sleep(3)

traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
_, traj_result = p.run_request(traj_req)

# Save response
body_hex = traj_result.get('bodyHex', '')
if body_hex:
    body_bytes = bytes.fromhex(body_hex)
    with open('windsurf_response_new.bin', 'wb') as f:
        f.write(body_bytes)
    print(f'Response saved: {len(body_bytes)} bytes')

    # Try to extract readable text
    import re
    text_pattern = rb'[\x20-\x7e\s]{30,}'
    matches = re.findall(text_pattern, body_bytes)

    print('\n=== Looking for Model Response ===')
    for match in matches:
        text = match.decode('utf-8', errors='ignore').strip()
        # Skip system prompts and tool definitions
        if 'You are Cascade' not in text and 'permission_denied' not in text and len(text) > 50:
            print(f'\nPotential response:\n{text[:300]}...\n')
            break
