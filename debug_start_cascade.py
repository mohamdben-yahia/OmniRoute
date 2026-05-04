#!/usr/bin/env python3
"""Debug StartCascade response to see why cascadeId extraction fails."""
import sys
import os
import json
sys.path.insert(0, 'scripts')
import windsurf_direct_probe as p

os.environ['WINDSURF_USER_ID'] = 'user-a0877fa492bb4eb3b0697a7c72bbb97b'
os.environ['WINDSURF_TEAM_ID'] = 'devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be'
os.environ['WINDSURF_METADATA_F'] = '000103'
os.environ['WINDSURF_SESSION_ID'] = '20924'
os.environ['WINDSURF_SWE_VERSION'] = 'swe-1-6'
os.environ['WINDSURF_CSRF_TOKEN'] = 'd1dfed32-5615-4751-9a46-f08c30e9700b'

token = p.resolve_auth_context_for_mode('ls_emulator')['token']

print('=== Starting Cascade ===')
start_req, _ = p.build_start_cascade_probe_request(token)
_, start_result = p.run_request(start_req)

print('\n=== Full Start Result ===')
print(json.dumps(start_result, indent=2, default=str))

print('\n=== Attempting Extraction ===')
cascade_id = p.extract_cascade_id_from_start_result(start_result)
print(f'Extracted cascadeId: {cascade_id}')
