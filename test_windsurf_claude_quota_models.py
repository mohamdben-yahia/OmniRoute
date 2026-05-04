#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Windsurf Claude models with limited quotas (no BYOK required).
Tests Claude Opus and other Claude models available with quotas.
"""
import sys
import os
import time
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Fix console encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, 'scripts')
import windsurf_direct_probe as p

def find_active_ls_port():
    """Find active Windsurf Language Server port."""
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            timeout=5,
            encoding='utf-8',
            errors='ignore'
        )

        ports = []
        for line in result.stdout.split('\n'):
            if 'LISTENING' in line and '127.0.0.1' in line:
                match = re.search(r'127\.0\.0\.1:(\d+)', line)
                if match:
                    port = int(match.group(1))
                    if 50000 <= port <= 60000:
                        ports.append(port)

        return ports[0] if ports else None
    except Exception:
        return None

def find_csrf_token_in_files():
    """Search for CSRF token in configuration files."""
    search_paths = [
        Path('.'),
        Path('C:/Users/amine/OmniRoute'),
        Path('C:/Users/amine/AppData/Local/Programs/Windsurf/winsurftiwtest'),
        Path.home(),
    ]

    search_files = [
        'windsurf-live-bootstrap.json',
        'tmp_windsurf_runtime_ls_binding.json',
        '.env.windsurf.local',
        '03-captures/network/windsurf-live-bootstrap.json',
    ]

    found_tokens = []

    for base_path in search_paths:
        for file_pattern in search_files:
            try:
                file_path = base_path / file_pattern
                if file_path.exists():
                    if file_path.suffix == '.json':
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if 'csrfToken' in data:
                                token = data['csrfToken']
                                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                                found_tokens.append({
                                    'token': token,
                                    'file': str(file_path),
                                    'modified': modified_time
                                })
                    elif file_path.suffix == '.local' or file_path.name.startswith('.env'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            match = re.search(r'WINDSURF_CSRF_TOKEN=([a-f0-9-]+)', content)
                            if match:
                                token = match.group(1)
                                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                                found_tokens.append({
                                    'token': token,
                                    'file': str(file_path),
                                    'modified': modified_time
                                })
            except Exception:
                pass

    if found_tokens:
        most_recent = max(found_tokens, key=lambda x: x['modified'])
        return most_recent['token'], most_recent['file']
    return None, None

def find_user_credentials():
    """Search for user credentials in configuration files."""
    search_paths = [
        Path('.'),
        Path('C:/Users/amine/OmniRoute'),
        Path('C:/Users/amine/AppData/Local/Programs/Windsurf/winsurftiwtest'),
    ]

    credentials = {
        'user_id': 'user-a0877fa492bb4eb3b0697a7c72bbb97b',
        'team_id': 'devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be',
        'session_id': '20924',
    }

    for base_path in search_paths:
        try:
            env_file = base_path / '.env.windsurf.local'
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                    user_match = re.search(r'WINDSURF_USER_ID=([^\s]+)', content)
                    if user_match:
                        credentials['user_id'] = user_match.group(1)

                    team_match = re.search(r'WINDSURF_TEAM_ID=([^\s]+)', content)
                    if team_match:
                        credentials['team_id'] = team_match.group(1)

                    session_match = re.search(r'WINDSURF_SESSION_ID=([^\s]+)', content)
                    if session_match:
                        credentials['session_id'] = session_match.group(1)

                    if credentials['user_id']:
                        return credentials
        except Exception:
            pass

    return credentials

print('='*70)
print('WINDSURF CLAUDE MODELS WITH QUOTAS TEST')
print('='*70)
print()

# Auto-detect configuration
print('[1/3] Auto-detecting Windsurf configuration...')
print()

port = find_active_ls_port()
if port:
    print(f'  ✓ Found active Language Server on port: {port}')
else:
    print('  ✗ No active Language Server found')
    print('  → Make sure Windsurf is running')
    sys.exit(1)

csrf_token, token_file = find_csrf_token_in_files()
if csrf_token:
    print(f'  ✓ Found CSRF token from: {Path(token_file).name}')
else:
    print('  ✗ No CSRF token found')
    print('  → Make sure Windsurf has been launched at least once')
    sys.exit(1)

credentials = find_user_credentials()
print(f'  ✓ User credentials loaded')

print()
print('[2/3] Configuring environment...')

# Set environment variables
os.environ['WINDSURF_USER_ID'] = credentials['user_id']
os.environ['WINDSURF_TEAM_ID'] = credentials['team_id']
os.environ['WINDSURF_METADATA_F'] = '000103'
os.environ['WINDSURF_SESSION_ID'] = credentials['session_id']
os.environ['WINDSURF_SWE_VERSION'] = 'swe-1-6'
os.environ['WINDSURF_CSRF_TOKEN'] = csrf_token
os.environ['WINDSURF_LOCAL_LS_PORT'] = str(port)

print(f'  Port: {port}')
print(f'  CSRF Token: {csrf_token[:20]}...')
print(f'  User ID: {credentials["user_id"][:30]}...')

token = p.resolve_auth_context_for_mode('ls_emulator')['token']

print()
print('[3/3] Starting Claude models with quotas test...')
print()

# Claude models with limited quotas (no BYOK required)
CLAUDE_QUOTA_MODELS = [
    # Claude Opus variants (with quotas)
    ('claude-opus-4-20250514', 'Claude Opus 4 (2025-05-14)', 'Anthropic'),
    ('claude-opus-4', 'Claude Opus 4', 'Anthropic'),
    ('claude-opus-3.5', 'Claude Opus 3.5', 'Anthropic'),
    ('claude-opus-3', 'Claude Opus 3', 'Anthropic'),

    # Claude Sonnet variants (with quotas)
    ('claude-sonnet-4-20250514', 'Claude Sonnet 4 (2025-05-14)', 'Anthropic'),
    ('claude-sonnet-4', 'Claude Sonnet 4', 'Anthropic'),
    ('claude-sonnet-3.7', 'Claude Sonnet 3.7', 'Anthropic'),
    ('claude-sonnet-3.5', 'Claude Sonnet 3.5', 'Anthropic'),
    ('claude-3.5-sonnet', 'Claude 3.5 Sonnet', 'Anthropic'),

    # Claude Haiku variants (with quotas)
    ('claude-haiku-4', 'Claude Haiku 4', 'Anthropic'),
    ('claude-haiku-3.5', 'Claude Haiku 3.5', 'Anthropic'),
    ('claude-3-haiku', 'Claude 3 Haiku', 'Anthropic'),

    # Other Claude variants
    ('claude-3-opus', 'Claude 3 Opus', 'Anthropic'),
    ('claude-3-sonnet', 'Claude 3 Sonnet', 'Anthropic'),
]

TEST_PROMPT = "You are Claude. What is your exact model version? Answer in one short sentence with your model name and capabilities."

print('='*70)
print('TEST DES MODÈLES CLAUDE AVEC QUOTAS')
print('='*70)
print(f'\nTimestamp: {datetime.now().isoformat()}')
print(f'Modèles Claude à tester: {len(CLAUDE_QUOTA_MODELS)}')
print(f'Méthode: Test direct sans AssignModel\n')
print('ℹ️  NOTE: Ces modèles ont des quotas limités (pas de BYOK requis)')
print('    Si quota atteint, le modèle retournera une erreur\n')

results = []

for idx, (model_id, model_name, provider) in enumerate(CLAUDE_QUOTA_MODELS, 1):
    print(f'\n{"="*70}')
    print(f'[{idx}/{len(CLAUDE_QUOTA_MODELS)}] Test: {model_name}')
    print(f'{"="*70}')

    result = {
        'model_id': model_id,
        'model_name': model_name,
        'provider': provider,
        'status': 'unknown',
        'error': None,
        'cascade_id': None,
        'detected_model': None,
        'response_time_ms': None,
        'response_size_bytes': None,
        'response_text': None,
        'quota_status': 'unknown',
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

        # Send message
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
        print(f'  [3/4] Waiting for response (10s)...')
        time.sleep(10)

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

        # Check for quota errors
        quota_patterns = [
            rb'quota',
            rb'limit',
            rb'rate.?limit',
            rb'too.?many.?requests',
            rb'exceeded',
        ]

        quota_exceeded = False
        for pattern in quota_patterns:
            if re.search(pattern, body_bytes, re.IGNORECASE):
                quota_exceeded = True
                result['quota_status'] = 'exceeded'
                break

        if not quota_exceeded:
            result['quota_status'] = 'available'

        # Detect Claude model from response
        claude_patterns = [
            (rb'claude[- ]?opus[- ]?4', 'Claude Opus 4'),
            (rb'claude[- ]?opus[- ]?3\.5', 'Claude Opus 3.5'),
            (rb'claude[- ]?opus[- ]?3', 'Claude Opus 3'),
            (rb'claude[- ]?sonnet[- ]?4', 'Claude Sonnet 4'),
            (rb'claude[- ]?sonnet[- ]?3\.7', 'Claude Sonnet 3.7'),
            (rb'claude[- ]?sonnet[- ]?3\.5', 'Claude Sonnet 3.5'),
            (rb'claude[- ]?3\.5[- ]?sonnet', 'Claude 3.5 Sonnet'),
            (rb'claude[- ]?haiku[- ]?4', 'Claude Haiku 4'),
            (rb'claude[- ]?haiku[- ]?3\.5', 'Claude Haiku 3.5'),
            (rb'claude[- ]?3[- ]?haiku', 'Claude 3 Haiku'),
            (rb'claude', 'Claude (generic)'),
            (rb'cascade', 'Cascade'),
        ]

        for pattern, detected_name in claude_patterns:
            if re.search(pattern, body_bytes, re.IGNORECASE):
                result['detected_model'] = detected_name
                break

        if not result['detected_model']:
            result['detected_model'] = 'Unknown'

        # Extract response text
        text_pattern = rb'[\x20-\x7e\s]{20,500}'
        text_matches = re.findall(text_pattern, body_bytes)

        response_text = None
        for match in text_matches:
            text = match.decode('utf-8', errors='ignore').strip()
            if 'You are Cascade' in text or 'system' in text.lower():
                continue
            if len(text) > 20 and len(text) < 500:
                response_text = text
                break

        result['response_text'] = response_text
        result['status'] = 'success'

        print(f'\n  ✓ SUCCESS')
        print(f'    Response time: {response_time_ms}ms')
        print(f'    Response size: {len(body_bytes)} bytes')
        print(f'    Detected model: {result["detected_model"]}')
        print(f'    Quota status: {result["quota_status"]}')
        if response_text:
            preview = response_text[:150].replace('\n', ' ')
            print(f'    Response: {preview}...')

        if quota_exceeded:
            print(f'    ⚠️  QUOTA EXCEEDED - Model has limited usage')

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)[:200]
        print(f'\n  ✗ ERROR: {str(e)[:80]}')

    results.append(result)

    # Pause between tests
    if idx < len(CLAUDE_QUOTA_MODELS):
        print(f'\n  Pausing 2s...')
        time.sleep(2)

# Generate report
print('\n\n' + '='*70)
print('RAPPORT FINAL - MODÈLES CLAUDE AVEC QUOTAS')
print('='*70)

successful = [r for r in results if r['status'] == 'success']
quota_available = [r for r in successful if r['quota_status'] == 'available']
quota_exceeded = [r for r in successful if r['quota_status'] == 'exceeded']
failed = [r for r in results if r['status'] == 'failed']
errors = [r for r in results if r['status'] == 'error']

print(f'\n📊 RÉSUMÉ')
print(f'  Total testé: {len(results)}')
print(f'  ✓ Disponibles: {len(successful)}')
print(f'  ✓ Quota disponible: {len(quota_available)}')
print(f'  ⚠ Quota dépassé: {len(quota_exceeded)}')
print(f'  ✗ Échecs: {len(failed)}')
print(f'  ⚠ Erreurs: {len(errors)}')

if quota_available:
    print(f'\n✓ MODÈLES CLAUDE DISPONIBLES (QUOTA OK)')
    by_detected = {}
    for r in quota_available:
        detected = r['detected_model']
        if detected not in by_detected:
            by_detected[detected] = []
        by_detected[detected].append(r)

    for detected_model, models in sorted(by_detected.items()):
        print(f'\n  {detected_model}:')
        for r in models:
            print(f'    • {r["model_name"]} ({r["response_time_ms"]}ms)')

if quota_exceeded:
    print(f'\n⚠ MODÈLES CLAUDE (QUOTA DÉPASSÉ)')
    for r in quota_exceeded:
        print(f'  • {r["model_name"]} - Quota atteint, réessayer plus tard')

if failed or errors:
    print(f'\n✗ MODÈLES NON DISPONIBLES')
    for r in failed + errors:
        print(f'  • {r["model_name"]}: {r["error"] or r["status"]}')

# Save results
output_file = 'windsurf_claude_quota_models_test.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'auto_detected': {
            'port': port,
            'csrf_token_file': token_file,
        },
        'summary': {
            'total': len(results),
            'available': len(successful),
            'quota_available': len(quota_available),
            'quota_exceeded': len(quota_exceeded),
            'failed': len(failed) + len(errors),
        },
        'results': results
    }, f, indent=2, ensure_ascii=False)

print(f'\n\n✓ Résultats sauvegardés: {output_file}')
print('\n' + '='*70)
print('TEST TERMINÉ')
print('='*70)
