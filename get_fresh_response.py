#!/usr/bin/env python3
"""Get fresh model response."""
import sys
import os
import time
import re
sys.path.insert(0, 'scripts')
import windsurf_direct_probe as p

os.environ['WINDSURF_USER_ID'] = 'user-a0877fa492bb4eb3b0697a7c72bbb97b'
os.environ['WINDSURF_TEAM_ID'] = 'devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be'
os.environ['WINDSURF_METADATA_F'] = '000103'
os.environ['WINDSURF_SESSION_ID'] = '20924'
os.environ['WINDSURF_SWE_VERSION'] = 'swe-1-6'
os.environ['WINDSURF_CSRF_TOKEN'] = 'a5d004fc-a32d-49ab-ab4d-3d27db4167f9'
os.environ['WINDSURF_CHAT_TEXT'] = 'Say hello in French'

token = p.resolve_auth_context_for_mode('ls_emulator')['token']

print('=== NOUVEAU CASCADE ===')
start_req, _ = p.build_start_cascade_probe_request(token)
_, start_result = p.run_request(start_req)
cascade_id = p.extract_cascade_id_from_start_result(start_result)
print(f'Cascade ID: {cascade_id}\n')

if not cascade_id:
    print('Echec creation cascade')
    sys.exit(1)

print('=== ENVOI MESSAGE ===')
send_req, _ = p.build_send_user_cascade_message_probe_request(token, cascade_id)
_, send_result = p.run_request(send_req)
print(f'Status: {send_result.get("status")}\n')

print('=== ATTENTE REPONSE (10 secondes) ===')
time.sleep(10)

traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
_, traj_result = p.run_request(traj_req)

body_hex = traj_result.get('bodyHex', '')
if not body_hex:
    print('Pas de reponse')
    sys.exit(1)

body_bytes = bytes.fromhex(body_hex)
print(f'Reponse recue: {len(body_bytes)} bytes\n')

# Save for analysis
with open('windsurf_hello_french.bin', 'wb') as f:
    f.write(body_bytes)

print('=== EXTRACTION TEXTE ===\n')

# Extract readable text
text_pattern = rb'[\x20-\x7e\s]{20,}'
matches = re.findall(text_pattern, body_bytes)

# Look for French greeting or actual response
for match in matches:
    text = match.decode('utf-8', errors='ignore').strip()

    # Skip system content
    if any(skip in text for skip in ['You are Cascade', '$schema', 'github.com', 'permission_denied']):
        continue

    # Look for French words or greeting
    if any(word in text.lower() for word in ['bonjour', 'salut', 'french', 'greeting', 'hello']):
        if len(text) < 500:
            print(f'>>> {text}\n')

print('\n=== TOUS LES SEGMENTS COURTS (< 300 chars) ===\n')
for i, match in enumerate(matches[:50]):
    text = match.decode('utf-8', errors='ignore').strip()
    if 50 < len(text) < 300 and 'You are Cascade' not in text and '$schema' not in text:
        print(f'{i+1}. {text}\n')
