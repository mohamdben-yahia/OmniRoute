#!/usr/bin/env python3
"""Debug what URL the probe is actually using."""
import sys
import os
sys.path.insert(0, 'scripts')
import windsurf_direct_probe as p

os.environ['WINDSURF_USER_ID'] = 'user-a0877fa492bb4eb3b0697a7c72bbb97b'
os.environ['WINDSURF_TEAM_ID'] = 'devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be'
os.environ['WINDSURF_METADATA_F'] = '000103'
os.environ['WINDSURF_SESSION_ID'] = '20924'
os.environ['WINDSURF_SWE_VERSION'] = 'swe-1-6'
os.environ['WINDSURF_CSRF_TOKEN'] = 'a5d004fc-a32d-49ab-ab4d-3d27db4167f9'

token = p.resolve_auth_context_for_mode('ls_emulator')['token']

print('=== Bootstrap State ===')
bootstrap = p.get_local_language_server_bootstrap_state()
print(f'languageServerUrl: {bootstrap.get("languageServerUrl")}')
print(f'csrfToken: {bootstrap.get("csrfToken")}')

print('\n=== Building Request ===')
start_req, preview = p.build_start_cascade_probe_request(token)
print(f'URL: {start_req.full_url}')
print(f'Host header: {start_req.headers.get("Host")}')
print(f'Preview URL: {preview.get("url")}')
