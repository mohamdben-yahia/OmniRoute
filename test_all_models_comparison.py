#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test ALL Windsurf models (free + pro) with performance comparison.
Tests each model with AssignModel and measures execution metrics.
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

# Configuration
os.environ['WINDSURF_USER_ID'] = 'user-a0877fa492bb4eb3b0697a7c72bbb97b'
os.environ['WINDSURF_TEAM_ID'] = 'devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be'
os.environ['WINDSURF_METADATA_F'] = '000103'
os.environ['WINDSURF_SESSION_ID'] = '20924'
os.environ['WINDSURF_SWE_VERSION'] = 'swe-1-6'
os.environ['WINDSURF_CSRF_TOKEN'] = '91e3d9fc-7277-4618-81ee-b72bc0adda38'

token = p.resolve_auth_context_for_mode('ls_emulator')['token']

# All models to test (free + pro)
MODELS_TO_TEST = [
    # Free models
    {'id': 'kimi-k2-6', 'name': 'Kimi K2.6', 'type': 'free', 'provider': 'Moonshot AI'},
    {'id': 'kimi-k2-5', 'name': 'Kimi K2.5', 'type': 'free', 'provider': 'Moonshot AI'},

    # Pro models - Claude
    {'id': 'claude-opus-4-byok-beta', 'name': 'Claude Opus 4 BYOK Beta', 'type': 'pro', 'provider': 'Anthropic'},
    {'id': 'claude-opus-4-thinking-byok-beta', 'name': 'Claude Opus 4 Thinking BYOK Beta', 'type': 'pro', 'provider': 'Anthropic'},
    {'id': 'claude-sonnet-4-byok', 'name': 'Claude Sonnet 4 BYOK', 'type': 'pro', 'provider': 'Anthropic'},
    {'id': 'claude-sonnet-4-thinking-byok', 'name': 'Claude Sonnet 4 Thinking BYOK', 'type': 'pro', 'provider': 'Anthropic'},

    # Pro models - OpenAI
    {'id': 'gpt-5-2-low-thinking', 'name': 'GPT-5.2 Low Thinking', 'type': 'pro', 'provider': 'OpenAI'},

    # Pro models - Google
    {'id': 'gemini-3-flash-low', 'name': 'Gemini 3 Flash Low', 'type': 'pro', 'provider': 'Google'},

    # Pro models - Zhipu AI
    {'id': 'glm-4-7-beta', 'name': 'GLM-4.7 Beta', 'type': 'pro', 'provider': 'Zhipu AI'},
    {'id': 'glm-5', 'name': 'GLM-5', 'type': 'pro', 'provider': 'Zhipu AI'},
    {'id': 'glm-5-1', 'name': 'GLM-5.1', 'type': 'pro', 'provider': 'Zhipu AI'},

    # Special models
    {'id': 'adaptive-ss', 'name': 'Adaptive SS', 'type': 'adaptive', 'provider': 'Windsurf'},
    {'id': 'swe-1-6-fast', 'name': 'SWE-1.6Fast', 'type': 'specialized', 'provider': 'Windsurf'},
]

# Test prompt
TEST_PROMPT = """Execute this simple task and respond with:
1. Your model name
2. Your provider
3. A simple calculation: 15 + 27 = ?
4. Current timestamp

Keep response under 100 words."""

print('='*70)
print('WINDSURF MODEL COMPARISON TEST')
print('='*70)
print(f'\nTimestamp: {datetime.now().isoformat()}')
print(f'Models to test: {len(MODELS_TO_TEST)}')
print(f'Test prompt: {len(TEST_PROMPT)} chars\n')

results = []

for idx, model_info in enumerate(MODELS_TO_TEST, 1):
    model_id = model_info['id']
    model_name = model_info['name']
    model_type = model_info['type']
    provider = model_info['provider']

    print(f'\n{"="*70}')
    print(f'[{idx}/{len(MODELS_TO_TEST)}] Testing: {model_name}')
    print(f'{"="*70}')
    print(f'  ID: {model_id}')
    print(f'  Type: {model_type}')
    print(f'  Provider: {provider}')

    result = {
        'model_id': model_id,
        'model_name': model_name,
        'model_type': model_type,
        'provider': provider,
        'status': 'unknown',
        'error': None,
        'response_time_ms': None,
        'response_size_bytes': None,
        'response_text': None,
        'cascade_id': None,
        'model_router_uid': None,
        'assign_model_status': None,
    }

    try:
        # Step 1: Start cascade
        print('\n  [1/5] Starting cascade...')
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
        print(f'  ✓ Cascade created: {cascade_id[:20]}...')

        # Step 2: Try to assign model
        print(f'\n  [2/5] Attempting to assign model: {model_id}...')

        # First get trajectory to extract model router UID
        traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
        _, traj_result = p.run_request(traj_req)
        body_hex = traj_result.get('bodyHex', '')

        if body_hex:
            body_bytes = bytes.fromhex(body_hex)
            model_router_uid = p.extract_model_router_uid_from_trajectory_body(body_bytes)
            result['model_router_uid'] = model_router_uid

            if model_router_uid:
                print(f'  ✓ Model router UID: {model_router_uid[:20]}...')

                # Configure AssignModel via environment variables
                os.environ['WINDSURF_ASSIGN_MODEL_CASCADE_ID'] = cascade_id
                os.environ['WINDSURF_ASSIGN_MODEL_ROUTER_UID'] = model_router_uid
                os.environ['WINDSURF_ASSIGN_MODEL_VARIANT'] = 'router-cascade-prompt'
                os.environ['WINDSURF_ASSIGN_MODEL_PROMPT_TEXT'] = f'Use model: {model_id}'

                # Store model ID in metadata for the assignment
                os.environ['WINDSURF_ASSIGN_MODEL_ID'] = model_id

                # Try AssignModel
                assign_req, _ = p.build_assign_model_probe_request(token)
                _, assign_result = p.run_request(assign_req)

                assign_status = assign_result.get('status')
                result['assign_model_status'] = assign_status

                if assign_status == 200:
                    print(f'  ✓ Model assigned successfully')
                else:
                    print(f'  ⚠ AssignModel returned: {assign_status}')
                    # Extract error if present
                    assign_body_hex = assign_result.get('bodyHex', '')
                    if assign_body_hex:
                        assign_body = bytes.fromhex(assign_body_hex)
                        error_match = re.search(rb'error["\s:]+([^"]+)', assign_body, re.IGNORECASE)
                        if error_match:
                            result['error'] = error_match.group(1).decode('utf-8', errors='ignore')
            else:
                print(f'  ⚠ No model router UID found')

        # Step 3: Send message
        print(f'\n  [3/5] Sending test message...')
        os.environ['WINDSURF_CHAT_TEXT'] = TEST_PROMPT
        send_req, _ = p.build_send_user_cascade_message_probe_request(token, cascade_id)
        _, send_result = p.run_request(send_req)

        if send_result.get('status') != 200:
            result['status'] = 'failed'
            result['error'] = f"SendMessage failed: {send_result.get('status')}"
            print(f'  ✗ Failed to send message')
            results.append(result)
            continue

        print(f'  ✓ Message sent')

        # Step 4: Wait for response
        print(f'\n  [4/5] Waiting for response (10s)...')
        time.sleep(10)

        # Step 5: Get trajectory response
        print(f'\n  [5/5] Fetching response...')
        traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
        _, traj_result = p.run_request(traj_req)

        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        result['response_time_ms'] = response_time_ms

        body_hex = traj_result.get('bodyHex', '')
        if not body_hex:
            result['status'] = 'failed'
            result['error'] = 'No response body'
            print(f'  ✗ No response received')
            results.append(result)
            continue

        body_bytes = bytes.fromhex(body_hex)
        result['response_size_bytes'] = len(body_bytes)

        # Extract response text
        text_pattern = rb'[\x20-\x7e\s]{30,500}'
        text_matches = re.findall(text_pattern, body_bytes)

        response_text = None
        for match in text_matches:
            text = match.decode('utf-8', errors='ignore').strip()
            if any(keyword in text.lower() for keyword in ['model', 'calculation', '42', 'timestamp']):
                if len(text) < 500 and 'You are Cascade' not in text:
                    response_text = text
                    break

        result['response_text'] = response_text
        result['status'] = 'success'

        print(f'\n  ✓ SUCCESS')
        print(f'    Response time: {response_time_ms}ms')
        print(f'    Response size: {len(body_bytes)} bytes')
        if response_text:
            preview = response_text[:150] + ('...' if len(response_text) > 150 else '')
            print(f'    Response preview: {preview}')

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)[:200]
        print(f'\n  ✗ ERROR: {str(e)[:100]}')

    results.append(result)

    # Pause between tests
    if idx < len(MODELS_TO_TEST):
        print(f'\n  Pausing 3s before next test...')
        time.sleep(3)

# Generate comparison report
print('\n\n' + '='*70)
print('COMPARISON REPORT')
print('='*70)

# Group by status
successful = [r for r in results if r['status'] == 'success']
failed = [r for r in results if r['status'] == 'failed']
errors = [r for r in results if r['status'] == 'error']

print(f'\n📊 SUMMARY')
print(f'  Total tested: {len(results)}')
print(f'  ✓ Successful: {len(successful)}')
print(f'  ✗ Failed: {len(failed)}')
print(f'  ⚠ Errors: {len(errors)}')

# Performance comparison (successful only)
if successful:
    print(f'\n⚡ PERFORMANCE (Successful models only)')
    print(f'{"Model":<35} {"Type":<12} {"Time (ms)":<12} {"Size (bytes)":<12}')
    print('-'*70)

    for r in sorted(successful, key=lambda x: x['response_time_ms'] or 999999):
        print(f'{r["model_name"]:<35} {r["model_type"]:<12} {r["response_time_ms"]:<12} {r["response_size_bytes"]:<12}')

    # Stats
    times = [r['response_time_ms'] for r in successful if r['response_time_ms']]
    if times:
        print(f'\n  Fastest: {min(times)}ms')
        print(f'  Slowest: {max(times)}ms')
        print(f'  Average: {int(sum(times)/len(times))}ms')

# Availability by type
print(f'\n📋 AVAILABILITY BY TYPE')
by_type = {}
for r in results:
    t = r['model_type']
    if t not in by_type:
        by_type[t] = {'total': 0, 'success': 0, 'failed': 0, 'error': 0}
    by_type[t]['total'] += 1
    by_type[t][r['status']] += 1

for model_type, stats in sorted(by_type.items()):
    success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f'  {model_type:<12}: {stats["success"]}/{stats["total"]} available ({success_rate:.0f}%)')

# Failed models details
if failed or errors:
    print(f'\n❌ UNAVAILABLE MODELS')
    for r in failed + errors:
        print(f'\n  {r["model_name"]} ({r["model_type"]})')
        print(f'    Provider: {r["provider"]}')
        print(f'    Status: {r["status"]}')
        if r['error']:
            print(f'    Error: {r["error"][:100]}')
        if r['assign_model_status']:
            print(f'    AssignModel status: {r["assign_model_status"]}')

# Save detailed results
output_file = 'windsurf_model_comparison_results.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'errors': len(errors),
        },
        'by_type': by_type,
        'results': results
    }, f, indent=2, ensure_ascii=False)

print(f'\n\n✓ Detailed results saved to: {output_file}')

# Generate markdown report
report_file = 'WINDSURF_MODEL_COMPARISON_REPORT.md'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write('# Windsurf Model Comparison Report\n\n')
    f.write(f'**Date**: {datetime.now().isoformat()}  \n')
    f.write(f'**Models Tested**: {len(results)}  \n')
    f.write(f'**Test Type**: Free + Pro models with AssignModel\n\n')
    f.write('---\n\n')

    f.write('## Summary\n\n')
    f.write(f'| Status | Count | Percentage |\n')
    f.write(f'|--------|-------|------------|\n')
    f.write(f'| ✓ Successful | {len(successful)} | {len(successful)/len(results)*100:.1f}% |\n')
    f.write(f'| ✗ Failed | {len(failed)} | {len(failed)/len(results)*100:.1f}% |\n')
    f.write(f'| ⚠ Errors | {len(errors)} | {len(errors)/len(results)*100:.1f}% |\n\n')

    if successful:
        f.write('## Performance Comparison\n\n')
        f.write('| Model | Type | Provider | Response Time | Size |\n')
        f.write('|-------|------|----------|---------------|------|\n')
        for r in sorted(successful, key=lambda x: x['response_time_ms'] or 999999):
            f.write(f'| {r["model_name"]} | {r["model_type"]} | {r["provider"]} | {r["response_time_ms"]}ms | {r["response_size_bytes"]} bytes |\n')
        f.write('\n')

    f.write('## Availability by Type\n\n')
    f.write('| Type | Available | Total | Success Rate |\n')
    f.write('|------|-----------|-------|-------------|\n')
    for model_type, stats in sorted(by_type.items()):
        success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        f.write(f'| {model_type} | {stats["success"]} | {stats["total"]} | {success_rate:.0f}% |\n')
    f.write('\n')

    if failed or errors:
        f.write('## Unavailable Models\n\n')
        for r in failed + errors:
            f.write(f'### {r["model_name"]}\n\n')
            f.write(f'- **Type**: {r["model_type"]}\n')
            f.write(f'- **Provider**: {r["provider"]}\n')
            f.write(f'- **Status**: {r["status"]}\n')
            if r['error']:
                f.write(f'- **Error**: {r["error"]}\n')
            if r['assign_model_status']:
                f.write(f'- **AssignModel Status**: {r["assign_model_status"]}\n')
            f.write('\n')

    f.write('---\n\n')
    f.write('**Conclusion**: ')
    if len(successful) == 1:
        f.write(f'Only {successful[0]["model_name"]} is available. ')
        f.write('Other models require BYOK API keys or are not yet deployed.\n')
    elif len(successful) > 1:
        f.write(f'{len(successful)} models are available. ')
        f.write('See performance comparison above.\n')
    else:
        f.write('No models are currently available.\n')

print(f'✓ Markdown report saved to: {report_file}')

print('\n' + '='*70)
print('TEST COMPLETE')
print('='*70)
