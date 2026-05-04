#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the DEFAULT Windsurf model performance without AssignModel.
This tests what model actually responds when we don't try to assign a specific one.
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

# Different test prompts to measure performance
TEST_PROMPTS = [
    {
        'name': 'Simple Math',
        'prompt': 'Calculate: 15 + 27 = ?',
        'expected_keywords': ['42', 'equals', 'sum']
    },
    {
        'name': 'Code Generation',
        'prompt': 'Write a Python function to reverse a string',
        'expected_keywords': ['def', 'return', 'reverse', '[::-1]']
    },
    {
        'name': 'Explanation',
        'prompt': 'Explain what is a REST API in one sentence',
        'expected_keywords': ['http', 'api', 'rest', 'web', 'service']
    },
    {
        'name': 'Model Identity',
        'prompt': 'What model are you? Answer in one sentence.',
        'expected_keywords': ['kimi', 'model', 'ai', 'assistant']
    },
    {
        'name': 'Translation',
        'prompt': 'Translate to French: Hello, how are you?',
        'expected_keywords': ['bonjour', 'comment', 'allez', 'vas']
    },
]

print('='*70)
print('WINDSURF DEFAULT MODEL PERFORMANCE TEST')
print('='*70)
print(f'\nTimestamp: {datetime.now().isoformat()}')
print(f'Test prompts: {len(TEST_PROMPTS)}')
print(f'Tests per prompt: 3 (for consistency check)')
print(f'Total cascades: {len(TEST_PROMPTS) * 3}\n')

all_results = []

for prompt_idx, test_prompt in enumerate(TEST_PROMPTS, 1):
    prompt_name = test_prompt['name']
    prompt_text = test_prompt['prompt']
    expected_keywords = test_prompt['expected_keywords']

    print(f'\n{"="*70}')
    print(f'TEST {prompt_idx}/{len(TEST_PROMPTS)}: {prompt_name}')
    print(f'{"="*70}')
    print(f'Prompt: "{prompt_text}"')
    print(f'Expected keywords: {", ".join(expected_keywords)}')

    prompt_results = []

    # Run 3 times for consistency
    for run in range(1, 4):
        print(f'\n  --- Run {run}/3 ---')

        result = {
            'prompt_name': prompt_name,
            'prompt_text': prompt_text,
            'run': run,
            'status': 'unknown',
            'error': None,
            'cascade_id': None,
            'model_detected': None,
            'response_time_ms': None,
            'response_size_bytes': None,
            'response_text': None,
            'keywords_found': [],
        }

        try:
            # Start cascade
            start_time = time.time()
            start_req, _ = p.build_start_cascade_probe_request(token)
            _, start_result = p.run_request(start_req)
            cascade_id = p.extract_cascade_id_from_start_result(start_result)

            if not cascade_id:
                result['status'] = 'failed'
                result['error'] = 'Failed to create cascade'
                print(f'    ✗ Failed to create cascade')
                prompt_results.append(result)
                continue

            result['cascade_id'] = cascade_id
            print(f'    ✓ Cascade: {cascade_id[:16]}...')

            # Send message (NO AssignModel - use default model)
            os.environ['WINDSURF_CHAT_TEXT'] = prompt_text
            send_req, _ = p.build_send_user_cascade_message_probe_request(token, cascade_id)
            _, send_result = p.run_request(send_req)

            if send_result.get('status') != 200:
                result['status'] = 'failed'
                result['error'] = f"SendMessage failed: {send_result.get('status')}"
                print(f'    ✗ SendMessage failed')
                prompt_results.append(result)
                continue

            print(f'    ✓ Message sent')

            # Wait for response
            print(f'    ⏳ Waiting 8s...')
            time.sleep(8)

            # Get trajectory response
            traj_req, _ = p.build_get_cascade_trajectory_probe_request(token, cascade_id)
            _, traj_result = p.run_request(traj_req)

            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            result['response_time_ms'] = response_time_ms

            body_hex = traj_result.get('bodyHex', '')
            if not body_hex:
                result['status'] = 'failed'
                result['error'] = 'No response body'
                print(f'    ✗ No response')
                prompt_results.append(result)
                continue

            body_bytes = bytes.fromhex(body_hex)
            result['response_size_bytes'] = len(body_bytes)

            # Detect model
            model_patterns = [
                (rb'kimi[- ]?k2\.6', 'Kimi K2.6'),
                (rb'kimi-k2-6', 'Kimi K2.6'),
                (rb'kimi[- ]?k2\.5', 'Kimi K2.5'),
                (rb'claude', 'Claude'),
                (rb'gpt', 'GPT'),
                (rb'gemini', 'Gemini'),
                (rb'glm', 'GLM'),
            ]

            for pattern, model_name in model_patterns:
                if re.search(pattern, body_bytes, re.IGNORECASE):
                    result['model_detected'] = model_name
                    break

            if not result['model_detected']:
                result['model_detected'] = 'Unknown'

            # Extract response text
            text_pattern = rb'[\x20-\x7e\s]{20,800}'
            text_matches = re.findall(text_pattern, body_bytes)

            response_text = None
            for match in text_matches:
                text = match.decode('utf-8', errors='ignore').strip()
                # Skip system prompts
                if 'You are Cascade' in text or 'system' in text.lower():
                    continue
                # Look for actual response content
                if len(text) > 10 and len(text) < 600:
                    response_text = text
                    break

            result['response_text'] = response_text

            # Check for expected keywords
            if response_text:
                response_lower = response_text.lower()
                for keyword in expected_keywords:
                    if keyword.lower() in response_lower:
                        result['keywords_found'].append(keyword)

            result['status'] = 'success'

            print(f'    ✓ Response received')
            print(f'      Time: {response_time_ms}ms')
            print(f'      Size: {len(body_bytes)} bytes')
            print(f'      Model: {result["model_detected"]}')
            print(f'      Keywords found: {len(result["keywords_found"])}/{len(expected_keywords)}')
            if response_text:
                preview = response_text[:100].replace('\n', ' ')
                print(f'      Preview: {preview}...')

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)[:200]
            print(f'    ✗ ERROR: {str(e)[:80]}')

        prompt_results.append(result)
        all_results.append(result)

        # Pause between runs
        if run < 3:
            time.sleep(2)

    # Summary for this prompt
    successful = [r for r in prompt_results if r['status'] == 'success']
    if successful:
        avg_time = int(sum(r['response_time_ms'] for r in successful) / len(successful))
        models = set(r['model_detected'] for r in successful)
        print(f'\n  📊 Prompt Summary:')
        print(f'    Success rate: {len(successful)}/3')
        print(f'    Avg response time: {avg_time}ms')
        print(f'    Models detected: {", ".join(models)}')

    # Pause before next prompt
    if prompt_idx < len(TEST_PROMPTS):
        print(f'\n  Pausing 3s before next prompt...')
        time.sleep(3)

# Generate final report
print('\n\n' + '='*70)
print('FINAL PERFORMANCE REPORT')
print('='*70)

successful = [r for r in all_results if r['status'] == 'success']
failed = [r for r in all_results if r['status'] == 'failed']
errors = [r for r in all_results if r['status'] == 'error']

print(f'\n📊 OVERALL SUMMARY')
print(f'  Total tests: {len(all_results)}')
print(f'  ✓ Successful: {len(successful)} ({len(successful)/len(all_results)*100:.1f}%)')
print(f'  ✗ Failed: {len(failed)}')
print(f'  ⚠ Errors: {len(errors)}')

if successful:
    print(f'\n⚡ PERFORMANCE METRICS')
    times = [r['response_time_ms'] for r in successful]
    sizes = [r['response_size_bytes'] for r in successful]
    print(f'  Response time:')
    print(f'    Min: {min(times)}ms')
    print(f'    Max: {max(times)}ms')
    print(f'    Avg: {int(sum(times)/len(times))}ms')
    print(f'  Response size:')
    print(f'    Min: {min(sizes)} bytes')
    print(f'    Max: {max(sizes)} bytes')
    print(f'    Avg: {int(sum(sizes)/len(sizes))} bytes')

    # Model consistency
    models = [r['model_detected'] for r in successful]
    model_counts = {}
    for m in models:
        model_counts[m] = model_counts.get(m, 0) + 1

    print(f'\n🤖 MODEL CONSISTENCY')
    for model, count in sorted(model_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(successful) * 100
        print(f'  {model}: {count}/{len(successful)} ({percentage:.1f}%)')

    # Task performance
    print(f'\n📋 PERFORMANCE BY TASK')
    for test_prompt in TEST_PROMPTS:
        prompt_name = test_prompt['name']
        prompt_results = [r for r in successful if r['prompt_name'] == prompt_name]
        if prompt_results:
            avg_time = int(sum(r['response_time_ms'] for r in prompt_results) / len(prompt_results))
            avg_keywords = sum(len(r['keywords_found']) for r in prompt_results) / len(prompt_results)
            total_keywords = len(test_prompt['expected_keywords'])
            print(f'  {prompt_name}:')
            print(f'    Success: {len(prompt_results)}/3')
            print(f'    Avg time: {avg_time}ms')
            print(f'    Avg keywords: {avg_keywords:.1f}/{total_keywords}')

# Save detailed results
output_file = 'windsurf_default_model_performance.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': len(all_results),
            'successful': len(successful),
            'failed': len(failed),
            'errors': len(errors),
        },
        'results': all_results
    }, f, indent=2, ensure_ascii=False)

print(f'\n\n✓ Detailed results saved to: {output_file}')

# Generate markdown report
report_file = 'WINDSURF_DEFAULT_MODEL_PERFORMANCE_REPORT.md'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write('# Windsurf Default Model Performance Report\n\n')
    f.write(f'**Date**: {datetime.now().isoformat()}  \n')
    f.write(f'**Test Type**: Default model (no AssignModel)  \n')
    f.write(f'**Total Tests**: {len(all_results)}  \n')
    f.write(f'**Success Rate**: {len(successful)/len(all_results)*100:.1f}%\n\n')
    f.write('---\n\n')

    f.write('## Summary\n\n')
    f.write(f'| Metric | Value |\n')
    f.write(f'|--------|-------|\n')
    f.write(f'| Total tests | {len(all_results)} |\n')
    f.write(f'| Successful | {len(successful)} ({len(successful)/len(all_results)*100:.1f}%) |\n')
    f.write(f'| Failed | {len(failed)} |\n')
    f.write(f'| Errors | {len(errors)} |\n\n')

    if successful:
        times = [r['response_time_ms'] for r in successful]
        f.write('## Performance Metrics\n\n')
        f.write(f'| Metric | Min | Max | Avg |\n')
        f.write(f'|--------|-----|-----|-----|\n')
        f.write(f'| Response time (ms) | {min(times)} | {max(times)} | {int(sum(times)/len(times))} |\n\n')

        f.write('## Model Consistency\n\n')
        models = [r['model_detected'] for r in successful]
        model_counts = {}
        for m in models:
            model_counts[m] = model_counts.get(m, 0) + 1

        f.write(f'| Model | Count | Percentage |\n')
        f.write(f'|-------|-------|------------|\n')
        for model, count in sorted(model_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = count / len(successful) * 100
            f.write(f'| {model} | {count}/{len(successful)} | {percentage:.1f}% |\n')
        f.write('\n')

        f.write('## Performance by Task\n\n')
        for test_prompt in TEST_PROMPTS:
            prompt_name = test_prompt['name']
            prompt_results = [r for r in successful if r['prompt_name'] == prompt_name]
            if prompt_results:
                f.write(f'### {prompt_name}\n\n')
                f.write(f'- **Prompt**: "{test_prompt["prompt"]}"\n')
                f.write(f'- **Success rate**: {len(prompt_results)}/3\n')
                avg_time = int(sum(r['response_time_ms'] for r in prompt_results) / len(prompt_results))
                f.write(f'- **Avg response time**: {avg_time}ms\n')
                avg_keywords = sum(len(r['keywords_found']) for r in prompt_results) / len(prompt_results)
                f.write(f'- **Avg keywords found**: {avg_keywords:.1f}/{len(test_prompt["expected_keywords"])}\n\n')

    f.write('---\n\n')
    f.write('## Conclusion\n\n')
    if successful and model_counts:
        primary_model = max(model_counts.items(), key=lambda x: x[1])[0]
        f.write(f'The default Windsurf model is **{primary_model}** ')
        f.write(f'(detected in {model_counts[primary_model]}/{len(successful)} successful tests).\n\n')
        f.write('**Key findings**:\n')
        f.write(f'- Success rate: {len(successful)/len(all_results)*100:.1f}%\n')
        times = [r['response_time_ms'] for r in successful]
        f.write(f'- Average response time: {int(sum(times)/len(times))}ms\n')
        f.write(f'- Model consistency: {model_counts[primary_model]/len(successful)*100:.1f}%\n')

print(f'✓ Markdown report saved to: {report_file}')

print('\n' + '='*70)
print('TEST COMPLETE')
print('='*70)
