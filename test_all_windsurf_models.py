#!/usr/bin/env python3
"""Test all available models in Windsurf by creating multiple cascades."""
import sys
import os
import time
import re
import json
sys.path.insert(0, 'scripts')
import windsurf_direct_probe as p

os.environ['WINDSURF_USER_ID'] = 'user-a0877fa492bb4eb3b0697a7c72bbb97b'
os.environ['WINDSURF_TEAM_ID'] = 'devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be'
os.environ['WINDSURF_METADATA_F'] = '000103'
os.environ['WINDSURF_SESSION_ID'] = '20924'
os.environ['WINDSURF_SWE_VERSION'] = 'swe-1-6'
os.environ['WINDSURF_CSRF_TOKEN'] = '91e3d9fc-7277-4618-81ee-b72bc0adda38'

token = p.resolve_auth_context_for_mode('ls_emulator')['token']

print('=== TEST DE TOUS LES MODELES WINDSURF ===\n')
print('Modeles a tester:')
print('  - Adaptive SS')
print('  - Claude Opus 4 BYOK Beta')
print('  - Claude Opus 4 Thinking BYOK Beta')
print('  - Claude Sonnet 4 BYOK')
print('  - Claude Sonnet 4 Thinking BYOK')
print('  - GLM4.7 Beta')
print('  - GLM-5')
print('  - SWE-1.6Fast')
print('  - Gemini 3 Flash Low')
print('  - GLM-5.1')
print('  - GPT-5.2 Low Thinking')
print('  - Kimi K2.5')
print('  - Kimi K2.6')
print()

# Test message
test_message = 'Respond with exactly: "Model test OK" and your model name'

# Number of cascades to test
num_tests = 15

results = []
detected_models = {}

for i in range(1, num_tests + 1):
    print(f'\n--- Test {i}/{num_tests} ---')

    try:
        # Start cascade
        start_req, _ = p.build_start_cascade_probe_request(token)
        _, start_result = p.run_request(start_req)
        cascade_id = p.extract_cascade_id_from_start_result(start_result)

        if not cascade_id:
            print(f'  X Echec creation cascade')
            continue

        print(f'  Cascade: {cascade_id[:20]}...')

        # Send message
        os.environ['WINDSURF_CHAT_TEXT'] = test_message
        send_req, _ = p.build_send_user_cascade_message_probe_request(token, cascade_id)
        _, send_result = p.run_request(send_req)

        if send_result.get('status') != 200:
            print(f'  X Echec envoi message')
            continue

        # Wait for response
        print(f'  Attente reponse...')
        time.sleep(6)

        traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
        _, traj_result = p.run_request(traj_req)

        body_hex = traj_result.get('bodyHex', '')
        if not body_hex:
            print(f'  X Pas de reponse')
            continue

        body_bytes = bytes.fromhex(body_hex)
        print(f'  Reponse: {len(body_bytes)} bytes')

        # Extract model router UID
        model_router_uid = p.extract_model_router_uid_from_trajectory_body(body_bytes)

        # Search for model names in response
        model_patterns = [
            rb'adaptive[- ]?ss',
            rb'claude[- ]?opus[- ]?4',
            rb'claude[- ]?sonnet[- ]?4',
            rb'glm[- ]?4\.7',
            rb'glm[- ]?5\.1',
            rb'glm[- ]?5',
            rb'swe[- ]?1\.6',
            rb'gemini[- ]?3',
            rb'gpt[- ]?5\.2',
            rb'kimi[- ]?k2\.5',
            rb'kimi[- ]?k2\.6',
            rb'kimi-k2-5',
            rb'kimi-k2-6',
        ]

        found_models = []
        for pattern in model_patterns:
            matches = re.findall(pattern, body_bytes, re.IGNORECASE)
            for match in matches:
                model_name = match.decode('utf-8', errors='ignore')
                if model_name not in found_models:
                    found_models.append(model_name)

        # Extract readable response text
        text_pattern = rb'[\x20-\x7e\s]{30,300}'
        text_matches = re.findall(text_pattern, body_bytes)

        response_text = None
        for match in text_matches:
            text = match.decode('utf-8', errors='ignore').strip()
            if 'Model test OK' in text or 'model' in text.lower():
                if len(text) < 200 and 'You are Cascade' not in text:
                    response_text = text
                    break

        # Determine model
        if found_models:
            model = found_models[0]
        else:
            model = 'Unknown'

        print(f'  Modele detecte: {model}')
        if response_text:
            print(f'  Reponse: {response_text[:100]}...')

        # Store result
        result = {
            'test': i,
            'cascade_id': cascade_id,
            'model_router_uid': model_router_uid,
            'detected_model': model,
            'response_size': len(body_bytes),
            'response_text': response_text
        }
        results.append(result)

        # Count model occurrences
        if model in detected_models:
            detected_models[model] += 1
        else:
            detected_models[model] = 1

    except Exception as e:
        print(f'  X Erreur: {str(e)[:80]}')

    # Pause between tests to avoid rate limiting
    time.sleep(2)

print('\n\n' + '='*60)
print('RAPPORT FINAL - MODELES DETECTES')
print('='*60 + '\n')

print(f'Tests executes: {len(results)}/{num_tests}')
print(f'Modeles uniques detectes: {len(detected_models)}\n')

if detected_models:
    print('Distribution des modeles:\n')
    for model, count in sorted(detected_models.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(results)) * 100
        bar = '█' * int(percentage / 5)
        print(f'  {model:<30} {count:>2}x ({percentage:>5.1f}%) {bar}')
else:
    print('Aucun modele detecte')

print('\n' + '='*60)
print('ANALYSE')
print('='*60 + '\n')

if len(detected_models) == 1:
    model_name = list(detected_models.keys())[0]
    print(f'✓ Windsurf utilise EXCLUSIVEMENT: {model_name}')
    print(f'  Tous les {len(results)} tests ont utilise le meme modele')
elif len(detected_models) > 1:
    print(f'✓ Windsurf peut utiliser {len(detected_models)} modeles differents:')
    for model in sorted(detected_models.keys()):
        print(f'  - {model}')
else:
    print('X Impossible de determiner les modeles disponibles')

print('\n' + '='*60)
print('MODELES DISPONIBLES VS TESTES')
print('='*60 + '\n')

expected_models = [
    'Adaptive SS',
    'Claude Opus 4 BYOK Beta',
    'Claude Opus 4 Thinking BYOK Beta',
    'Claude Sonnet 4 BYOK',
    'Claude Sonnet 4 Thinking BYOK',
    'GLM4.7 Beta',
    'GLM-5',
    'SWE-1.6Fast',
    'Gemini 3 Flash Low',
    'GLM-5.1',
    'GPT-5.2 Low Thinking',
    'Kimi K2.5',
    'Kimi K2.6',
]

detected_lower = [m.lower() for m in detected_models.keys()]

for expected in expected_models:
    found = any(expected.lower() in d for d in detected_lower)
    status = '✓' if found else 'X'
    print(f'{status} {expected}')

# Save detailed results
with open('windsurf_all_models_test_results.json', 'w', encoding='utf-8') as f:
    json.dump({
        'timestamp': '2026-05-03T23:39:00Z',
        'tests_executed': len(results),
        'models_detected': detected_models,
        'results': results
    }, f, indent=2, ensure_ascii=False)

print(f'\n\nResultats detailles sauvegardes dans: windsurf_all_models_test_results.json')
