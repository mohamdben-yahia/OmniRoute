#!/usr/bin/env python3
"""Run Windsurf probe and wait for streaming model response."""
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
os.environ['WINDSURF_CHAT_TEXT'] = 'hello'

token = p.resolve_auth_context_for_mode('ls_emulator')['token']

print('=== Starting Windsurf Cascade ===')
start_req, _ = p.build_start_cascade_probe_request(token)
_, start_result = p.run_request(start_req)
cascade_id = p.extract_cascade_id_from_start_result(start_result)
print(f'Cascade ID: {cascade_id}')
print(f'Status: {start_result.get("status")}')

if start_result.get('status') != 200:
    print('StartCascade failed')
    sys.exit(1)

print('\n=== Sending Message ===')
send_req, _ = p.build_send_user_cascade_message_probe_request(token, cascade_id)
_, send_result = p.run_request(send_req)
print(f'Status: {send_result.get("status")}')

print('\n=== Polling for Model Response ===')
for attempt in range(30):
    time.sleep(2)
    traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
    _, traj_result = p.run_request(traj_req)

    body_text = traj_result.get('bodyText', '')

    # Look for text content in the response
    if 'Hello' in body_text or 'hello' in body_text or len(body_text) > 1000:
        print(f'\n=== Model Response (Attempt {attempt + 1}) ===')
        print(f'Body length: {len(body_text)} chars')
        print(f'First 500 chars:\n{body_text[:500]}')

        # Try to extract readable text
        import re
        text_matches = re.findall(r'[A-Za-z][A-Za-z\s,\.!?]{20,}', body_text)
        if text_matches:
            print(f'\n=== Extracted Text ===')
            for match in text_matches[:5]:
                print(f'  {match}')
        break

    print(f'Attempt {attempt + 1}: Body length {len(body_text)} chars, waiting...')
else:
    print('\nTimeout waiting for model response')
