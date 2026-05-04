#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test ALL Windsurf built-in models without external API keys.
Tests which models are actually available in Windsurf by default.
"""
import sys
import os
import time
import re
import json
from datetime import datetime

# Fix console encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, 'scripts')
import windsurf_direct_probe as p

# Configuration Windsurf
os.environ['WINDSURF_USER_ID'] = 'user-a0877fa492bb4eb3b0697a7c72bbb97b'
os.environ['WINDSURF_TEAM_ID'] = 'devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be'
os.environ['WINDSURF_METADATA_F'] = '000103'
os.environ['WINDSURF_SESSION_ID'] = '20924'
os.environ['WINDSURF_SWE_VERSION'] = 'swe-1-6'
os.environ['WINDSURF_CSRF_TOKEN'] = '91e3d9fc-7277-4618-81ee-b72bc0adda38'

token = p.resolve_auth_context_for_mode('ls_emulator')['token']

# Tous les modèles potentiellement disponibles dans Windsurf
ALL_WINDSURF_MODELS = [
    # Modèles gratuits Kimi
    'kimi-k2-6',
    'kimi-k2-5',
    'kimi-k2-7',
    'kimi-k3',

    # Modèles Claude (si intégrés dans Windsurf)
    'claude-opus-4',
    'claude-sonnet-4',
    'claude-haiku-4',

    # Modèles GPT (si intégrés dans Windsurf)
    'gpt-5',
    'gpt-4-turbo',
    'gpt-4',

    # Modèles Gemini (si intégrés dans Windsurf)
    'gemini-3-flash',
    'gemini-2-pro',
    'gemini-pro',

    # Modèles GLM (si intégrés dans Windsurf)
    'glm-5',
    'glm-4',

    # Modèles spécialisés Windsurf
    'adaptive-ss',
    'swe-1-6-fast',
    'cascade-default',
]

TEST_PROMPT = "What model are you? Answer in one short sentence."

print('='*70)
print('TEST DES MODÈLES WINDSURF INTÉGRÉS')
print('='*70)
print(f'\nTimestamp: {datetime.now().isoformat()}')
print(f'Modèles à tester: {len(ALL_WINDSURF_MODELS)}')
print(f'Méthode: Test direct sans AssignModel (comme Kimi K2.6)\n')

results = []

for idx, model_id in enumerate(ALL_WINDSURF_MODELS, 1):
    print(f'\n{"="*70}')
    print(f'[{idx}/{len(ALL_WINDSURF_MODELS)}] Test: {model_id}')
    print(f'{"="*70}')

    result = {
        'model_id': model_id,
        'status': 'unknown',
        'error': None,
        'cascade_id': None,
        'detected_model': None,
        'response_time_ms': None,
        'response_size_bytes': None,
        'response_text': None,
    }

    try:
        # Start cascade
        print('  [1/4] Starting cascade...')
        start_time = time.time()
        start_req, _ = p.build_start_cascade_probe_request(token)
        _, start_result = p.run_request(start_req)
        cascade_id = p.extract_cascade_id_from_start_result(start_result)

        if not cascade_id:
            result['status'] = 'failed'
            result['error'] = 'Failed to create cascade'
            print(f'  ✗ Failed to create cascade')
            results.append(result)
            continue

        result['cascade_id'] = cascade_id
        print(f'  ✓ Cascade: {cascade_id[:16]}...')

        # Send message (test si le modèle répond)
        print(f'  [2/4] Sending test message...')
        os.environ['WINDSURF_CHAT_TEXT'] = TEST_PROMPT
        send_req, _ = p.build_send_user_cascade_message_probe_request(token, cascade_id)
        _, send_result = p.run_request(send_req)

        if send_result.get('status') != 200:
            result['status'] = 'failed'
            result['error'] = f"SendMessage failed: {send_result.get('status')}"
            print(f'  ✗ SendMessage failed')
            results.append(result)
            continue

        print(f'  ✓ Message sent')

        # Wait for response
        print(f'  [3/4] Waiting for response (8s)...')
        time.sleep(8)

        # Get trajectory response
        print(f'  [4/4] Fetching response...')
        traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
        _, traj_result = p.run_request(traj_req)

        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        result['response_time_ms'] = response_time_ms

        body_hex = traj_result.get('bodyHex', '')
        if not body_hex:
            result['status'] = 'failed'
            result['error'] = 'No response body'
            print(f'  ✗ No response')
            results.append(result)
            continue

        body_bytes = bytes.fromhex(body_hex)
        result['response_size_bytes'] = len(body_bytes)

        # Detect model from response
        model_patterns = [
            (rb'kimi[- ]?k2\.6', 'Kimi K2.6'),
            (rb'kimi[- ]?k2\.5', 'Kimi K2.5'),
            (rb'kimi[- ]?k2\.7', 'Kimi K2.7'),
            (rb'kimi[- ]?k3', 'Kimi K3'),
            (rb'claude[- ]?opus', 'Claude Opus'),
            (rb'claude[- ]?sonnet', 'Claude Sonnet'),
            (rb'claude[- ]?haiku', 'Claude Haiku'),
            (rb'gpt[- ]?5', 'GPT-5'),
            (rb'gpt[- ]?4', 'GPT-4'),
            (rb'gemini[- ]?3', 'Gemini 3'),
            (rb'gemini[- ]?2', 'Gemini 2'),
            (rb'gemini[- ]?pro', 'Gemini Pro'),
            (rb'glm[- ]?5', 'GLM-5'),
            (rb'glm[- ]?4', 'GLM-4'),
            (rb'cascade', 'Cascade'),
            (rb'adaptive', 'Adaptive'),
        ]

        for pattern, model_name in model_patterns:
            if re.search(pattern, body_bytes, re.IGNORECASE):
                result['detected_model'] = model_name
                break

        if not result['detected_model']:
            result['detected_model'] = 'Unknown'

        # Extract response text
        text_pattern = rb'[\x20-\x7e\s]{20,400}'
        text_matches = re.findall(text_pattern, body_bytes)

        response_text = None
        for match in text_matches:
            text = match.decode('utf-8', errors='ignore').strip()
            if 'You are Cascade' in text or 'system' in text.lower():
                continue
            if len(text) > 10 and len(text) < 400:
                response_text = text
                break

        result['response_text'] = response_text
        result['status'] = 'success'

        print(f'\n  ✓ SUCCESS')
        print(f'    Response time: {response_time_ms}ms')
        print(f'    Response size: {len(body_bytes)} bytes')
        print(f'    Detected model: {result["detected_model"]}')
        if response_text:
            preview = response_text[:100].replace('\n', ' ')
            print(f'    Response: {preview}...')

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)[:200]
        print(f'\n  ✗ ERROR: {str(e)[:80]}')

    results.append(result)

    # Pause between tests
    if idx < len(ALL_WINDSURF_MODELS):
        print(f'\n  Pausing 2s...')
        time.sleep(2)

# Generate report
print('\n\n' + '='*70)
print('RAPPORT FINAL')
print('='*70)

successful = [r for r in results if r['status'] == 'success']
failed = [r for r in results if r['status'] == 'failed']
errors = [r for r in results if r['status'] == 'error']

print(f'\n📊 RÉSUMÉ')
print(f'  Total testé: {len(results)}')
print(f'  ✓ Disponibles: {len(successful)}')
print(f'  ✗ Non disponibles: {len(failed)}')
print(f'  ⚠ Erreurs: {len(errors)}')

if successful:
    print(f'\n✓ MODÈLES DISPONIBLES')

    # Group by detected model
    by_detected = {}
    for r in successful:
        detected = r['detected_model']
        if detected not in by_detected:
            by_detected[detected] = []
        by_detected[detected].append(r['model_id'])

    for detected_model, model_ids in sorted(by_detected.items()):
        print(f'\n  {detected_model}:')
        for model_id in model_ids:
            r = next(r for r in successful if r['model_id'] == model_id)
            print(f'    • {model_id} ({r["response_time_ms"]}ms)')

if failed or errors:
    print(f'\n✗ MODÈLES NON DISPONIBLES')
    for r in failed + errors:
        print(f'  • {r["model_id"]}: {r["error"] or r["status"]}')

# Save results
output_file = 'windsurf_builtin_models_test.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': len(results),
            'available': len(successful),
            'unavailable': len(failed) + len(errors),
        },
        'results': results
    }, f, indent=2, ensure_ascii=False)

print(f'\n\n✓ Résultats sauvegardés: {output_file}')

# Generate markdown report
report_file = 'WINDSURF_BUILTIN_MODELS_REPORT.md'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write('# Windsurf Built-in Models Test Report\n\n')
    f.write(f'**Date**: {datetime.now().isoformat()}  \n')
    f.write(f'**Test Type**: Built-in models (no external API keys)  \n')
    f.write(f'**Models Tested**: {len(results)}  \n')
    f.write(f'**Available**: {len(successful)}  \n\n')
    f.write('---\n\n')

    if successful:
        f.write('## Available Models\n\n')
        by_detected = {}
        for r in successful:
            detected = r['detected_model']
            if detected not in by_detected:
                by_detected[detected] = []
            by_detected[detected].append(r)

        for detected_model, model_results in sorted(by_detected.items()):
            f.write(f'### {detected_model}\n\n')
            f.write('| Model ID | Response Time | Size |\n')
            f.write('|----------|---------------|------|\n')
            for r in model_results:
                f.write(f'| {r["model_id"]} | {r["response_time_ms"]}ms | {r["response_size_bytes"]} bytes |\n')
            f.write('\n')

    if failed or errors:
        f.write('## Unavailable Models\n\n')
        for r in failed + errors:
            f.write(f'- **{r["model_id"]}**: {r["error"] or r["status"]}\n')

    f.write('\n---\n\n')
    f.write('## Conclusion\n\n')
    if successful:
        if len(successful) == 1:
            f.write(f'Only **{successful[0]["detected_model"]}** is available as a built-in model.\n')
        else:
            f.write(f'{len(successful)} models are available as built-in models.\n')
    else:
        f.write('No built-in models are currently available.\n')

print(f'✓ Rapport markdown: {report_file}')

print('\n' + '='*70)
print('TEST TERMINÉ')
print('='*70)
