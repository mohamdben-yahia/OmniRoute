#!/usr/bin/env python3
"""Final test of StartCascade with all metadata fields."""
import sys
import os
sys.path.insert(0, 'scripts')
import windsurf_direct_probe as p
import urllib.request

os.environ['WINDSURF_USER_ID'] = 'user-a0877fa492bb4eb3b0697a7c72bbb97b'
os.environ['WINDSURF_TEAM_ID'] = 'devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be'
os.environ['WINDSURF_METADATA_F'] = '000103'
os.environ['WINDSURF_SESSION_ID'] = '20924'
os.environ['WINDSURF_SWE_VERSION'] = 'swe-1-6'

token = p.resolve_auth_context_for_mode('ls_emulator')['token']
req, preview = p.build_start_cascade_probe_request(token)

print('Request verification:')
print('URL:', preview['url'])
print('Host header:', req.headers.get('Host'))
print('CSRF token:', req.headers.get('X-codeium-csrf-token')[:20] + '...')
print('Payload size:', len(req.data))
print('Metadata fields:', list(preview['metadata'].keys()))
print()
print('Attempting StartCascade...')

try:
    resp = urllib.request.urlopen(req)
    print('SUCCESS:', resp.status)
    body = resp.read()
    print('Response body:', body[:200])
except urllib.error.HTTPError as e:
    print('FAILED:', e.code, e.reason)
    body = e.read().decode('utf-8')
    print('Response:', body)
