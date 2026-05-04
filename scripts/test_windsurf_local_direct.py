#!/usr/bin/env python3
"""
Test Windsurf models directly via localhost:53302
Bypasses cloud API completely to avoid DEVIN_TOKEN_EXCHANGE_PSK error
"""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime

# Configuration
LOCAL_LS_URL = "http://127.0.0.1:53302"
SESSION_TOKEN = "devin-session-token$eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uX2lkIjoid2luZHN1cmYtc2Vzc2lvbi1hNjliYzY5NWQyN2E0NWVjYmRmNjVmYWI5MWQxODZhNiJ9.KyaNgJ8vM6gQswVjs5YMDzSb4Q7lF5313TBlV_tybqM"

MODELS = [
    'claude-3-5-sonnet-20241022',
    'gpt-4o',
    'gemini-2.0-flash-exp',
    'deepseek-chat',
    'kimi-k2-6',
    'kimi-k2-5',
    'glm-5',
    'glm-5-1',
    'swe-1-6-fast'
]

MESSAGE = "quelle model llm vous etes"

def build_metadata():
    """Build common metadata for requests"""
    return {
        "apiKey": SESSION_TOKEN,
        "ideName": "windsurf",
        "ideVersion": "1.108.2",
        "extensionName": "windsurf",
        "extensionVersion": "1.108.2",
        "locale": "en",
        "sessionId": "test-session-local"
    }

def start_cascade():
    """Start a new cascade session"""
    url = f"{LOCAL_LS_URL}/exa.language_server_pb.LanguageServerService/StartCascade"

    # Build protobuf-like payload (simplified)
    payload = {
        "metadata": build_metadata(),
        "source": 1
    }

    headers = {
        "Content-Type": "application/json",
        "Host": "l.localhost:53302",
        "Origin": "vscode-file://vscode-app"
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

            # Try to extract cascade ID from response
            body_text = body.decode('utf-8', errors='ignore')

            # Simple regex to find UUID pattern
            import re
            match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', body_text)

            if match:
                return {
                    'status': response.status,
                    'cascadeId': match.group(0)
                }
            else:
                return {
                    'status': response.status,
                    'cascadeId': None,
                    'error': 'No cascade ID found in response'
                }

    except urllib.error.HTTPError as e:
        return {
            'status': e.code,
            'error': e.read().decode('utf-8', errors='ignore')
        }
    except Exception as e:
        return {
            'status': 0,
            'error': str(e)
        }

def send_message(cascade_id, model_uid, message):
    """Send a message to the cascade"""
    url = f"{LOCAL_LS_URL}/exa.language_server_pb.LanguageServerService/SendUserCascadeMessage"

    payload = {
        "metadata": build_metadata(),
        "cascadeId": cascade_id,
        "chatText": message,
        "modelUid": model_uid
    }

    headers = {
        "Content-Type": "application/json",
        "Host": "e.localhost:53302",
        "Origin": "vscode-file://vscode-app"
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read()

            return {
                'status': response.status,
                'body': body.decode('utf-8', errors='ignore')
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get('message', error_body)
        except:
            error_msg = error_body

        return {
            'status': e.code,
            'error': error_msg
        }
    except Exception as e:
        return {
            'status': 0,
            'error': str(e)
        }

def test_model(model):
    """Test a single model"""
    print(f"\n{'='*70}")
    print(f"Testing: {model}")
    print(f"Message: {MESSAGE}")
    print(f"{'='*70}")

    # Step 1: Start cascade
    print("[1/2] Starting cascade...")
    cascade_result = start_cascade()

    if cascade_result['status'] != 200:
        print(f"[ERROR] StartCascade failed: {cascade_result.get('error', 'Unknown')}")
        return {
            'model': model,
            'status': 'error',
            'stage': 'start_cascade',
            'error': cascade_result.get('error', 'Unknown')
        }

    cascade_id = cascade_result.get('cascadeId')
    if not cascade_id:
        print(f"[ERROR] No cascade ID received")
        return {
            'model': model,
            'status': 'error',
            'stage': 'start_cascade',
            'error': 'No cascade ID'
        }

    print(f"[SUCCESS] Cascade ID: {cascade_id}")

    # Step 2: Send message
    print(f"[2/2] Sending message with model {model}...")
    message_result = send_message(cascade_id, model, MESSAGE)

    if message_result['status'] == 200:
        print(f"[SUCCESS] Status 200")
        return {
            'model': model,
            'status': 'success',
            'http_status': 200,
            'cascade_id': cascade_id
        }
    elif message_result['status'] == 500:
        error = message_result.get('error', 'Unknown')
        print(f"[REJECTED] Status 500: {error}")
        return {
            'model': model,
            'status': 'rejected',
            'http_status': 500,
            'error': error,
            'cascade_id': cascade_id
        }
    else:
        print(f"[ERROR] Status {message_result['status']}")
        return {
            'model': model,
            'status': 'error',
            'http_status': message_result['status'],
            'error': message_result.get('error', 'Unknown'),
            'cascade_id': cascade_id
        }

def main():
    print("="*70)
    print("Test Windsurf Models - Direct Local API")
    print(f"Message: '{MESSAGE}'")
    print(f"Total: {len(MODELS)} models")
    print(f"API: {LOCAL_LS_URL}")
    print("="*70)

    results = []
    success = 0
    rejected = 0
    errors = 0

    for i, model in enumerate(MODELS, 1):
        print(f"\n[{i}/{len(MODELS)}] Testing {model}...")
        result = test_model(model)
        results.append(result)

        if result['status'] == 'success':
            success += 1
        elif result['status'] == 'rejected':
            rejected += 1
        else:
            errors += 1

    # Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"\n[SUCCESS] {success}/{len(MODELS)}")
    print(f"[REJECTED] {rejected}/{len(MODELS)}")
    print(f"[ERRORS] {errors}/{len(MODELS)}")

    print("\n[SUCCESS] Working Models (Status 200):")
    for r in results:
        if r['status'] == 'success':
            print(f"  - {r['model']}")

    print("\n[REJECTED] Rejected Models (Status 500):")
    for r in results:
        if r['status'] == 'rejected':
            error = r.get('error', 'Unknown')
            print(f"  - {r['model']}")
            print(f"    Error: {error}")

    if errors > 0:
        print("\n[ERRORS] Models with Errors:")
        for r in results:
            if r['status'] == 'error':
                print(f"  - {r['model']} (stage: {r.get('stage', 'unknown')})")
                print(f"    Error: {r.get('error', 'Unknown')}")

    # Save results
    output = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'message': MESSAGE,
        'mode': 'direct_local_api',
        'api_url': LOCAL_LS_URL,
        'total': len(MODELS),
        'success': success,
        'rejected': rejected,
        'errors': errors,
        'results': results
    }

    output_file = 'test_windsurf_local_direct_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved: {output_file}")
    print("="*70)

    return 0 if success > 0 else 1

if __name__ == '__main__':
    sys.exit(main())
