#!/usr/bin/env python3
"""Test GetCascadeTrajectory to extract modelRouterUid."""
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
print('Starting cascade...')
start_req, start_preview = p.build_start_cascade_probe_request(token)
start_exit, start_result = p.run_request(start_req)
cascade_id = p.extract_cascade_id_from_start_result(start_result)
print(f'Cascade ID: {cascade_id}')
print(f'Start status: {start_result.get("status")}')

if start_exit != 0 or not cascade_id:
    print('StartCascade failed')
    sys.exit(1)

# Send message
print('\nSending message...')
send_req, send_preview = p.build_send_user_cascade_message_probe_request(token, cascade_id)
send_exit, send_result = p.run_request(send_req)
print(f'Send status: {send_result.get("status")}')

# Poll trajectory
print('\nPolling trajectory for modelRouterUid...')
for attempt in range(10):
    time.sleep(1)
    traj_req, traj_preview = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
    traj_exit, traj_result = p.run_request(traj_req)

    decoded = traj_result.get('decodedUnaryProto', {})
    trajectory = decoded.get('trajectory', {})
    model_info = trajectory.get('modelAssignmentInfo', {})

    print(f'\nAttempt {attempt + 1}:')
    print(f'  Status: {traj_result.get("status")}')
    print(f'  Trajectory keys: {list(trajectory.keys())}')
    print(f'  modelAssignmentInfo: {model_info}')

    model_router_uid = model_info.get('modelRouterUid')
    if model_router_uid:
        print(f'\n✓ Found modelRouterUid: {model_router_uid}')
        break

    if p.is_terminal_cascade_trajectory(trajectory):
        print('\n✗ Trajectory terminal but no modelRouterUid')
        break
else:
    print('\n✗ Timeout waiting for modelRouterUid')
