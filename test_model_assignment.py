#!/usr/bin/env python3
"""Test different models by trying to assign them explicitly."""
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

print('=== TEST DES MODELES DISPONIBLES ===\n')

# List of models to test
models_to_test = [
    'claude-opus-4',
    'claude-sonnet-4',
    'claude-sonnet-3-5',
    'claude-haiku-3-5',
    'gpt-4',
    'gpt-4-turbo',
    'gpt-3.5-turbo',
    'gemini-pro',
    'gemini-1.5-pro',
    'kimi-k2-6',
    'kimi-k2-6-e',
]

results = []

for model_name in models_to_test:
    print(f'\n--- Test: {model_name} ---')

    try:
        # Start cascade
        start_req, _ = p.build_start_cascade_probe_request(token)
        _, start_result = p.run_request(start_req)
        cascade_id = p.extract_cascade_id_from_start_result(start_result)

        if not cascade_id:
            print(f'  ✗ Echec creation cascade')
            continue

        print(f'  Cascade: {cascade_id}')

        # Get initial trajectory to get modelRouterUid
        time.sleep(1)
        traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
        _, traj_result = p.run_request(traj_req)

        body_hex = traj_result.get('bodyHex', '')
        if not body_hex:
            print(f'  ✗ Pas de trajectoire')
            continue

        body_bytes = bytes.fromhex(body_hex)
        model_router_uid = p.extract_model_router_uid_from_trajectory_body(body_bytes)

        if not model_router_uid:
            print(f'  ✗ Pas de modelRouterUid')
            continue

        print(f'  Model Router UID: {model_router_uid}')

        # Try to assign the specific model
        # Note: AssignModel requires specific model identifiers that may differ from display names
        # We'll try with the model name as-is first

        # Build AssignModel request
        try:
            # This will likely fail with 500 due to DEVIN_TOKEN_EXCHANGE_PSK
            # but we can see if the model name is recognized
            assign_req, _ = p.build_assign_model_probe_request(
                token=token,
                cascade_id=cascade_id,
                model_router_uid=model_router_uid,
                model_uid=model_name  # Try with model name
            )

            _, assign_result = p.run_request(assign_req)

            status = assign_result.get('status')
            error = assign_result.get('error')

            if status == 200:
                print(f'  ✓ Modele assigne avec succes!')
                results.append({'model': model_name, 'status': 'success'})
            elif status == 500:
                # Check error message
                body = assign_result.get('body', '')
                if 'DEVIN_TOKEN_EXCHANGE_PSK' in body:
                    print(f'  ~ Modele reconnu (erreur serveur PSK)')
                    results.append({'model': model_name, 'status': 'recognized'})
                elif 'not found' in body.lower() or 'invalid' in body.lower():
                    print(f'  ✗ Modele non reconnu')
                    results.append({'model': model_name, 'status': 'not_found'})
                else:
                    print(f'  ? Erreur: {body[:100]}')
                    results.append({'model': model_name, 'status': 'error', 'message': body[:100]})
            else:
                print(f'  ? Status {status}')
                results.append({'model': model_name, 'status': f'status_{status}'})

        except Exception as e:
            print(f'  ✗ Erreur AssignModel: {e}')
            results.append({'model': model_name, 'status': 'exception', 'error': str(e)})

        # Send a test message to see what model actually responds
        os.environ['WINDSURF_CHAT_TEXT'] = f'Say: testing {model_name}'
        send_req, _ = p.build_send_user_cascade_message_probe_request(token, cascade_id)
        _, send_result = p.run_request(send_req)

        # Wait for response
        time.sleep(5)
        traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
        _, traj_result = p.run_request(traj_req)

        body_hex = traj_result.get('bodyHex', '')
        if body_hex:
            body_bytes = bytes.fromhex(body_hex)

            # Check which model actually responded
            detected_models = []
            for pattern in [rb'kimi-[a-z0-9-]+', rb'claude-[a-z0-9-]+', rb'gpt-[a-z0-9-]+', rb'gemini-[a-z0-9-]+']:
                matches = re.findall(pattern, body_bytes, re.IGNORECASE)
                for match in matches:
                    detected_models.append(match.decode('utf-8', errors='ignore'))

            if detected_models:
                actual_model = detected_models[0]
                print(f'  Modele qui a repondu: {actual_model}')
                if model_name.lower() in actual_model.lower():
                    print(f'  ✓ Correspondance!')
                else:
                    print(f'  ✗ Modele different (attendu: {model_name})')

    except Exception as e:
        print(f'  ✗ Erreur generale: {e}')
        results.append({'model': model_name, 'status': 'failed', 'error': str(e)})

    time.sleep(2)  # Pause between tests

print('\n\n=== RESUME DES TESTS ===\n')
print(f'{"Modele":<25} {"Status":<20}')
print('-' * 50)
for result in results:
    status = result.get('status', 'unknown')
    print(f'{result["model"]:<25} {status:<20}')

print('\n=== MODELES DISPONIBLES ===\n')
available = [r for r in results if r.get('status') in ['success', 'recognized']]
if available:
    for r in available:
        print(f'  ✓ {r["model"]}')
else:
    print('  Aucun modele alternatif detecte')
    print('  Windsurf semble utiliser exclusivement Kimi K2-6')
