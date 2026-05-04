#!/usr/bin/env python3
"""Test all available LLM models in Windsurf."""
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

print('=== LISTE DES MODELES DISPONIBLES ===\n')

# Try to get model statuses
try:
    # Build GetModelStatuses request
    base_url = p.get_local_language_server_url()
    url = f"{base_url}/exa.language_server_pb.LanguageServerService/GetModelStatuses"

    headers = p.build_local_ls_headers(method_name="GetModelStatuses")

    # Empty protobuf message for GetModelStatuses
    payload = bytearray()
    metadata_msg = p.build_metadata_message(token)
    payload.extend(p.encode_message(1, metadata_msg))

    import urllib.request
    req = urllib.request.Request(url, data=bytes(payload), headers=headers, method="POST")

    with urllib.request.urlopen(req, timeout=10) as response:
        body = response.read()
        print(f'Response: {len(body)} bytes')

        # Try to extract model names from response
        text_pattern = rb'[\x20-\x7e]{5,50}'
        matches = re.findall(text_pattern, body)

        print('\nModeles detectes:')
        models = set()
        for match in matches:
            text = match.decode('utf-8', errors='ignore')
            # Look for model name patterns
            if any(pattern in text.lower() for pattern in ['claude', 'gpt', 'gemini', 'kimi', 'sonnet', 'opus', 'haiku']):
                models.add(text)

        for model in sorted(models):
            print(f'  - {model}')

except Exception as e:
    print(f'Erreur GetModelStatuses: {e}')

print('\n=== TEST DES MODELES COMMUNS ===\n')

# Test with different prompts to trigger different models
test_cases = [
    {
        'prompt': 'Say "test 1" in one word',
        'description': 'Test modele par defaut'
    },
    {
        'prompt': 'Respond with exactly: test2',
        'description': 'Test modele alternatif'
    },
    {
        'prompt': 'Reply: test3',
        'description': 'Test troisieme modele'
    }
]

results = []

for i, test in enumerate(test_cases, 1):
    print(f'\n--- Test {i}: {test["description"]} ---')
    print(f'Prompt: {test["prompt"]}')

    try:
        # Start cascade
        start_req, _ = p.build_start_cascade_probe_request(token)
        _, start_result = p.run_request(start_req)
        cascade_id = p.extract_cascade_id_from_start_result(start_result)

        if not cascade_id:
            print('  Echec creation cascade')
            continue

        print(f'  Cascade: {cascade_id}')

        # Get initial trajectory to see assigned model
        time.sleep(1)
        traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
        _, traj_result = p.run_request(traj_req)

        body_hex = traj_result.get('bodyHex', '')
        if body_hex:
            body_bytes = bytes.fromhex(body_hex)
            model_router_uid = p.extract_model_router_uid_from_trajectory_body(body_bytes)

            # Try to find model name in response
            text_matches = re.findall(rb'[a-z0-9-]{5,30}', body_bytes)
            model_name = None
            for match in text_matches:
                text = match.decode('utf-8', errors='ignore')
                if any(pattern in text for pattern in ['claude', 'gpt', 'gemini', 'kimi', 'sonnet', 'opus', 'haiku']):
                    model_name = text
                    break

            print(f'  Model Router UID: {model_router_uid}')
            print(f'  Model Name: {model_name or "Unknown"}')

            results.append({
                'test': i,
                'cascade_id': cascade_id,
                'model_router_uid': model_router_uid,
                'model_name': model_name
            })

        # Send message
        os.environ['WINDSURF_CHAT_TEXT'] = test['prompt']
        send_req, _ = p.build_send_user_cascade_message_probe_request(token, cascade_id)
        _, send_result = p.run_request(send_req)

        # Wait for response
        time.sleep(5)
        traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
        _, traj_result = p.run_request(traj_req)

        body_hex = traj_result.get('bodyHex', '')
        if body_hex:
            body_bytes = bytes.fromhex(body_hex)

            # Extract response
            text_pattern = rb'[\x20-\x7e\s]{20,200}'
            matches = re.findall(text_pattern, body_bytes)

            for match in matches:
                text = match.decode('utf-8', errors='ignore').strip()
                if 'test' in text.lower() and len(text) < 100:
                    print(f'  Reponse: {text}')
                    break

    except Exception as e:
        print(f'  Erreur: {e}')

    time.sleep(2)  # Pause between tests

print('\n\n=== RESUME DES MODELES TESTES ===\n')
for result in results:
    print(f"Test {result['test']}:")
    print(f"  Model Router UID: {result['model_router_uid']}")
    print(f"  Model Name: {result['model_name']}")
    print()
