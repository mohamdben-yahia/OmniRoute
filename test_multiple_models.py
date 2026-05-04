#!/usr/bin/env python3
"""Test different models - simplified version."""
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
os.environ['WINDSURF_CSRF_TOKEN'] = '91e3d9fc-7277-4618-81ee-b72bc0adda38'

token = p.resolve_auth_context_for_mode('ls_emulator')['token']

print('=== TEST MODELES MULTIPLES ===\n')

# Create multiple cascades and see what models are assigned
test_prompts = [
    'Say: test1',
    'Say: test2',
    'Say: test3',
    'Say: test4',
    'Say: test5',
]

detected_models = []

for i, prompt in enumerate(test_prompts, 1):
    print(f'\n--- Cascade {i} ---')

    try:
        # Start cascade
        start_req, _ = p.build_start_cascade_probe_request(token)
        _, start_result = p.run_request(start_req)
        cascade_id = p.extract_cascade_id_from_start_result(start_result)

        if not cascade_id:
            print(f'  Echec creation')
            continue

        print(f'  ID: {cascade_id[:20]}...')

        # Send message
        os.environ['WINDSURF_CHAT_TEXT'] = prompt
        send_req, _ = p.build_send_user_cascade_message_probe_request(token, cascade_id)
        _, send_result = p.run_request(send_req)

        # Wait for response
        time.sleep(5)
        traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
        _, traj_result = p.run_request(traj_req)

        body_hex = traj_result.get('bodyHex', '')
        if not body_hex:
            print(f'  Pas de reponse')
            continue

        body_bytes = bytes.fromhex(body_hex)

        # Extract model name
        model_patterns = [
            rb'kimi-[a-z0-9-]+',
            rb'claude-[a-z0-9.-]+',
            rb'gpt-[a-z0-9.-]+',
            rb'gemini-[a-z0-9.-]+',
        ]

        found = None
        for pattern in model_patterns:
            matches = re.findall(pattern, body_bytes, re.IGNORECASE)
            if matches:
                found = matches[0].decode('utf-8', errors='ignore')
                break

        if found:
            print(f'  Modele: {found}')
            detected_models.append(found)
        else:
            print(f'  Modele: Unknown')

    except Exception as e:
        print(f'  Erreur: {str(e)[:50]}')

    time.sleep(1)

print('\n\n=== RESUME ===\n')
print(f'Cascades testees: {len(test_prompts)}')
print(f'Modeles detectes: {len(set(detected_models))}')

if detected_models:
    print('\nModeles utilises:')
    for model in sorted(set(detected_models)):
        count = detected_models.count(model)
        print(f'  - {model} ({count}x)')
else:
    print('\nAucun modele detecte')

print('\n=== CONCLUSION ===\n')
if len(set(detected_models)) == 1:
    print(f'Windsurf utilise exclusivement: {detected_models[0]}')
elif len(set(detected_models)) > 1:
    print('Windsurf peut utiliser plusieurs modeles:')
    for model in sorted(set(detected_models)):
        print(f'  - {model}')
else:
    print('Impossible de determiner les modeles disponibles')
