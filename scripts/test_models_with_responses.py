#!/usr/bin/env python3
"""
Test all 8 discovered models with a real prompt and capture their responses
"""

import json
import urllib.request
import urllib.error
import time
import re

# Configuration
PORT = 51834
SESSION_TOKEN = "devin-session-token$eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uX2lkIjoid2luZHN1cmYtc2Vzc2lvbi1iMzhmZjUxYmFjMzc0ZDJlOGMyMjY3ZDMzODQwYmQyMiJ9.Bh2TUtbSyCkAEKngLUdpWFmpJdMKNGV8xTfRsrXnnII"
CSRF_TOKEN = "965fdd75-25f9-45cc-ac13-ee8dea91fa46"

# Test prompt
TEST_PROMPT = "Quel modèle LLM êtes-vous? Répondez en une phrase courte."

# Load models
with open('windsurf_models_from_setusersettings.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    MODELS = [m['full_uid'] for m in data['models']]

def encode_protobuf_string(field_number, value):
    """Encode a protobuf string field"""
    tag = (field_number << 3) | 2
    value_bytes = value.encode('utf-8')
    length = len(value_bytes)

    result = bytearray()
    result.append(tag)
    result.append(length)
    result.extend(value_bytes)

    return bytes(result)

def encode_protobuf_message(field_number, message_bytes):
    """Encode a nested protobuf message"""
    tag = (field_number << 3) | 2
    length = len(message_bytes)

    result = bytearray()
    result.append(tag)
    result.append(length)
    result.extend(message_bytes)

    return bytes(result)

def start_cascade():
    """Start a new cascade"""
    url = f"http://127.0.0.1:{PORT}/exa.language_server_pb.LanguageServerService/StartCascade"

    payload = {
        "metadata": {
            "apiKey": SESSION_TOKEN,
            "ideName": "windsurf",
            "ideVersion": "1.108.2",
            "extensionName": "windsurf",
            "extensionVersion": "1.108.2",
            "locale": "en",
            "sessionId": f"test-{int(time.time())}"
        },
        "source": 1
    }

    headers = {
        "Accept": "*/*",
        "Authorization": SESSION_TOKEN,
        "Content-Type": "application/json",
        "Host": f"l.localhost:{PORT}",
        "Origin": "vscode-file://vscode-app",
        "x-codeium-csrf-token": CSRF_TOKEN
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read()
            if body[:2] == b'\x1f\x8b':
                import gzip
                body = gzip.decompress(body)

            body_text = body.decode('utf-8', errors='ignore')
            match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', body_text)

            if match:
                return match.group(0)
            return None

    except Exception as e:
        return None

def send_message_and_get_response(model_uid, cascade_id, prompt):
    """Send message and try to capture response"""

    # Build protobuf message
    message = bytearray()
    message.extend(encode_protobuf_string(1, cascade_id))
    message.extend(encode_protobuf_string(2, prompt))

    plan_model_msg = encode_protobuf_string(1, model_uid)
    message.extend(encode_protobuf_message(3, plan_model_msg))

    url = f"http://127.0.0.1:{PORT}/exa.language_server_pb.LanguageServerService/SendUserCascadeMessage"

    headers = {
        "Accept": "*/*",
        "Authorization": SESSION_TOKEN,
        "Content-Type": "application/grpc-web+proto",
        "Host": f"e.localhost:{PORT}",
        "Origin": "vscode-file://vscode-app",
        "x-codeium-csrf-token": CSRF_TOKEN
    }

    try:
        req = urllib.request.Request(
            url,
            data=bytes(message),
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            body = response.read()

            # Try to decode response
            if body[:2] == b'\x1f\x8b':
                import gzip
                body = gzip.decompress(body)

            # Response is protobuf - try to extract text
            body_text = body.decode('utf-8', errors='ignore')

            return {
                'status': 'success',
                'http_status': response.status,
                'response_preview': body_text[:500] if body_text else '(empty response)',
                'response_length': len(body)
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        return {
            'status': 'error',
            'http_status': e.code,
            'error': error_body[:200]
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)[:200]
        }

def main():
    print("="*70)
    print("TEST DES 8 MODELES WINDSURF AVEC PROMPT")
    print("="*70)
    print()
    print(f"Prompt de test: \"{TEST_PROMPT}\"")
    print(f"Port: {PORT}")
    print()

    results = []

    for i, model in enumerate(MODELS, 1):
        base_name = model.replace('-20260424', '')
        print(f"[{i}/{len(MODELS)}] {base_name}")
        print("-" * 70)

        # Start cascade
        print(f"  Demarrage cascade...", end=' ', flush=True)
        cascade_id = start_cascade()

        if not cascade_id:
            print("ECHEC")
            results.append({
                'model': model,
                'base_name': base_name,
                'status': 'error',
                'error': 'Failed to start cascade'
            })
            print()
            continue

        print(f"OK ({cascade_id[:8]}...)")

        # Send message
        print(f"  Envoi du prompt...", end=' ', flush=True)
        result = send_message_and_get_response(model, cascade_id, TEST_PROMPT)

        if result['status'] == 'success':
            print(f"OK (HTTP {result['http_status']})")
            print(f"  Reponse recue: {result['response_length']} bytes")
            if result['response_preview']:
                preview = result['response_preview'][:200].replace('\n', ' ')
                print(f"  Apercu: {preview}...")
        else:
            print(f"ECHEC")
            if 'http_status' in result:
                print(f"  HTTP {result['http_status']}")
            if 'error' in result:
                print(f"  Erreur: {result['error'][:100]}")

        results.append({
            'model': model,
            'base_name': base_name,
            **result
        })

        print()
        time.sleep(1)

    # Summary
    print("="*70)
    print("RESUME")
    print("="*70)
    print()

    success = [r for r in results if r.get('status') == 'success']
    failed = [r for r in results if r.get('status') == 'error']

    print(f"Total: {len(results)}")
    print(f"Succes: {len(success)}")
    print(f"Echecs: {len(failed)}")
    print()

    if success:
        print("MODELES FONCTIONNELS:")
        for r in success:
            print(f"  - {r['base_name']}")
            if r.get('response_preview'):
                preview = r['response_preview'][:150].replace('\n', ' ')
                print(f"    Reponse: {preview}...")
        print()

    if failed:
        print("MODELES EN ECHEC:")
        for r in failed:
            print(f"  - {r['base_name']}")
        print()

    # Save results
    output = {
        'timestamp': '2026-05-04T13:30:00Z',
        'test_prompt': TEST_PROMPT,
        'port': PORT,
        'total_tested': len(results),
        'success_count': len(success),
        'failed_count': len(failed),
        'results': results
    }

    output_file = 'windsurf_models_response_test.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Resultats sauvegardes: {output_file}")
    print("="*70)

if __name__ == '__main__':
    main()
