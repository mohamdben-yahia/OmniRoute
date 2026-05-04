#!/usr/bin/env python3
"""Check raw trajectory response."""
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
time.sleep(2)
traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
_, traj_result = p.run_request(traj_req)

print(f'Status: {traj_result.get("status")}')
print(f'Body bytes: {traj_result.get("bodyBytes")}')
print(f'Body hex (first 200 bytes): {traj_result.get("bodyHex", "")[:400]}')
print(f'Decoded proto keys: {list(traj_result.get("decodedUnaryProto", {}).keys())}')

decoded = traj_result.get('decodedUnaryProto', {})
if 'trajectory' in decoded:
    traj = decoded['trajectory']
    print(f'Trajectory type: {type(traj)}')
    print(f'Trajectory keys: {list(traj.keys()) if isinstance(traj, dict) else "not a dict"}')
