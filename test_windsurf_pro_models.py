#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Windsurf PRO models with BYOK configuration.
Tests the most powerful models on the market: GPT-5.5, Claude Opus 4.7, etc.
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
print('WINDSURF PRO MODELS TEST')
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
print('[3/3] Starting PRO model tests...')
print()

# PRO models - most powerful on the market
PRO_MODELS = [
    # OpenAI GPT-5 series (most powerful)
    ('gpt-5.5', 'GPT-5.5', 'OpenAI'),
    ('gpt-5.2-low-thinking', 'GPT-5.2 Low Thinking', 'OpenAI'),
    ('gpt-5', 'GPT-5', 'OpenAI'),

    # Anthropic Claude 4 series (most powerful)
    ('claude-opus-4.7', 'Claude Opus 4.7', 'Anthropic'),
    ('claude-opus-4-thinking', 'Claude Opus 4 Thinking', 'Anthropic'),
    ('claude-opus-4', 'Claude Opus 4', 'Anthropic'),
    ('claude-sonnet-4-thinking', 'Claude Sonnet 4 Thinking', 'Anthropic'),
    ('claude-sonnet-4', 'Claude Sonnet 4', 'Anthropic'),

    # Google Gemini 3 series
    ('gemini-3-flash-low', 'Gemini 3 Flash Low', 'Google'),
    ('gemini-3-flash', 'Gemini 3 Flash', 'Google'),

    # Zhipu AI GLM series
    ('glm-5.1', 'GLM-5.1', 'Zhipu AI'),
    ('glm-5', 'GLM-5', 'Zhipu AI'),
    ('glm-4.7', 'GLM-4.7', 'Zhipu AI'),
]

TEST_PROMPT = "What is the most advanced AI model you are? Explain your capabilities in 2-3 sentences."

print('='*70)
print('TEST DES MODÈLES PRO WINDSURF')
print('='*70)
print(f'\nTimestamp: {datetime.now().isoformat()}')
print(f'Modèles PRO à tester: {len(PRO_MODELS)}')
print(f'Méthode: Test avec AssignModel (BYOK requis)\n')
print('⚠️  NOTE: Ces modèles nécessitent des clés API configurées')
print('    dans Windsurf Settings → API Keys\n')

results = []

for idx, (model_id, model_name, provider) in enumerate(PRO_MODELS, 1):
    print(f'\n{"="*70}')
    print(f'[{idx}/{len(PRO_MODELS)}] Test: {model_name} ({provider})')
    print(f'{"="*70}')

    result = {
        'model_id': model_id,
        'model_name': model_name,
        'provider': provider,
        'status': 'unknown',
        'error': None,
        'cascade_id': None,
        'model_router_uid': None,
        'assign_model_status': None,
        'response_time_ms': None,
        'response_size_bytes': None,
        'response_text': None,
    }

    try:
        # Start cascade
        print('  [1/5] Starting cascade...')
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

        # Try to assign model (requires BYOK)
        print(f'  [2/5] Attempting to assign model {model_id}...')

        # Use a placeholder model_router_uid (will fail if BYOK not configured)
        model_router_uid = 'model-router-uid-placeholder'
        result['model_router_uid'] = model_router_uid

        os.environ['WINDSURF_ASSIGN_MODEL_CASCADE_ID'] = cascade_id
        os.environ['WINDSURF_ASSIGN_MODEL_ROUTER_UID'] = model_router_uid
        os.environ['WINDSURF_ASSIGN_MODEL_VARIANT'] = 'router-cascade-prompt'
        os.environ['WINDSURF_ASSIGN_MODEL_PROMPT_TEXT'] = f'Use model: {model_id}'

        assign_req, _ = p.build_assign_model_probe_request(token)
        _, assign_result = p.run_request(assign_req)

        assign_status = assign_result.get('status')
        result['assign_model_status'] = assign_status

        if assign_status == 500:
            result['status'] = 'byok_required'
            result['error'] = f'BYOK configuration required for {provider}'
            print(f'  ⚠ AssignModel returned 500 - BYOK required')
            print(f'    → Configure {provider} API key in Windsurf Settings')
            results.append(result)
            continue
        elif assign_status != 200:
            result['status'] = 'failed'
            result['error'] = f'AssignModel failed: {assign_status}'
            print(f'  ✗ AssignModel failed: {assign_status}')
            results.append(result)
            continue

        print(f'  ✓ Model assigned')

        # Send message
        print(f'  [3/5] Sending test message...')
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
        print(f'  [4/5] Waiting for response (10s)...')
        time.sleep(10)

        # Get trajectory response
        print(f'  [5/5] Fetching response...')
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
        if response_text:
            preview = response_text[:150].replace('\n', ' ')
            print(f'    Response: {preview}...')

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)[:200]
        print(f'\n  ✗ ERROR: {str(e)[:80]}')

    results.append(result)

    # Pause between tests
    if idx < len(PRO_MODELS):
        print(f'\n  Pausing 2s...')
        time.sleep(2)

# Generate report
print('\n\n' + '='*70)
print('RAPPORT FINAL - MODÈLES PRO')
print('='*70)

successful = [r for r in results if r['status'] == 'success']
byok_required = [r for r in results if r['status'] == 'byok_required']
failed = [r for r in results if r['status'] == 'failed']
errors = [r for r in results if r['status'] == 'error']

print(f'\n📊 RÉSUMÉ')
print(f'  Total testé: {len(results)}')
print(f'  ✓ Disponibles: {len(successful)}')
print(f'  ⚠ BYOK requis: {len(byok_required)}')
print(f'  ✗ Échecs: {len(failed)}')
print(f'  ⚠ Erreurs: {len(errors)}')

if successful:
    print(f'\n✓ MODÈLES PRO DISPONIBLES')
    by_provider = {}
    for r in successful:
        provider = r['provider']
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(r)

    for provider, models in sorted(by_provider.items()):
        print(f'\n  {provider}:')
        for r in models:
            print(f'    • {r["model_name"]} ({r["response_time_ms"]}ms)')

if byok_required:
    print(f'\n⚠ MODÈLES NÉCESSITANT BYOK')
    by_provider = {}
    for r in byok_required:
        provider = r['provider']
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(r['model_name'])

    for provider, models in sorted(by_provider.items()):
        print(f'\n  {provider}:')
        for model in models:
            print(f'    • {model}')
        print(f'    → Configure {provider} API key in Windsurf Settings → API Keys')

if failed or errors:
    print(f'\n✗ MODÈLES NON DISPONIBLES')
    for r in failed + errors:
        print(f'  • {r["model_name"]}: {r["error"] or r["status"]}')

# Save results
output_file = 'windsurf_pro_models_test.json'
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
            'byok_required': len(byok_required),
            'failed': len(failed) + len(errors),
        },
        'results': results
    }, f, indent=2, ensure_ascii=False)

print(f'\n\n✓ Résultats sauvegardés: {output_file}')

print('\n' + '='*70)
print('INSTRUCTIONS POUR ACTIVER LES MODÈLES PRO')
print('='*70)
print('\n1. Ouvrir Windsurf Settings (Ctrl+,)')
print('2. Aller dans API Keys')
print('3. Configurer les clés API:')
print('   • OpenAI: https://platform.openai.com/api-keys')
print('   • Anthropic: https://console.anthropic.com/settings/keys')
print('   • Google: https://makersuite.google.com/app/apikey')
print('   • Zhipu AI: https://open.bigmodel.cn/usercenter/apikeys')
print('4. Relancer ce script après configuration')

print('\n' + '='*70)
print('TEST TERMINÉ')
print('='*70)
