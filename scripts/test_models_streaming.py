#!/usr/bin/env python3
"""
Test models by monitoring the cascade events stream
The response comes through streaming events, not the SendUserCascadeMessage response
"""

import json
import urllib.request
import urllib.error
import time
import re
import threading

# Configuration
PORT = 51834
SESSION_TOKEN = "devin-session-token$eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uX2lkIjoid2luZHN1cmYtc2Vzc2lvbi1iMzhmZjUxYmFjMzc0ZDJlOGMyMjY3ZDMzODQwYmQyMiJ9.Bh2TUtbSyCkAEKngLUdpWFmpJdMKNGV8xTfRsrXnnII"
CSRF_TOKEN = "965fdd75-25f9-45cc-ac13-ee8dea91fa46"

TEST_PROMPT = "Quel modèle LLM êtes-vous? Répondez en une phrase courte."

# Load models - test just 3 for now
MODELS_TO_TEST = [
    "gpt-5-5-low-20260424",
    "claude-opus-4-7-medium-20260424",
    "deepseek-v4-20260424"
]

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
        print(f"    StartCascade error: {e}")
        return None

def listen_to_cascade_events(cascade_id, duration=15):
    """Listen to cascade events stream"""
    url = f"http://127.0.0.1:{PORT}/exa.language_server_pb.LanguageServerService/GetCascadeEvents"

    # This might be a streaming endpoint
    payload = {
        "metadata": {
            "apiKey": SESSION_TOKEN,
            "ideName": "windsurf",
            "ideVersion": "1.108.2",
            "extensionName": "windsurf",
            "extensionVersion": "1.108.2",
            "locale": "en",
            "sessionId": f"test-listen"
        },
        "cascadeId": cascade_id
    }

    headers = {
        "Accept": "*/*",
        "Authorization": SESSION_TOKEN,
        "Content-Type": "application/json",
        "Host": f"g.localhost:{PORT}",
        "Origin": "vscode-file://vscode-app",
        "x-codeium-csrf-token": CSRF_TOKEN
    }

    collected_data = []

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=duration) as response:
            # Read streaming response
            while True:
                chunk = response.read(1024)
                if not chunk:
                    break

                # Try to decode
                try:
                    text = chunk.decode('utf-8', errors='ignore')
                    if text.strip():
                        collected_data.append(text)
                except:
                    pass

    except Exception as e:
        pass

    return ''.join(collected_data)

def send_message(model_uid, cascade_id, prompt):
    """Send message"""
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

        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status == 200

    except Exception as e:
        print(f"    Send error: {e}")
        return False

def test_model_with_streaming(model_uid):
    """Test model and try to capture streaming response"""
    base_name = model_uid.replace('-20260424', '')

    print(f"\nTest: {base_name}")
    print("-" * 70)

    # Start cascade
    print("  1. Demarrage cascade...", end=' ', flush=True)
    cascade_id = start_cascade()
    if not cascade_id:
        print("ECHEC")
        return None
    print(f"OK ({cascade_id[:8]}...)")

    # Start listening in background
    print("  2. Ecoute des evenements...", end=' ', flush=True)
    events_data = []

    def listen_thread():
        data = listen_to_cascade_events(cascade_id, duration=10)
        events_data.append(data)

    listener = threading.Thread(target=listen_thread)
    listener.start()

    time.sleep(1)  # Let listener start
    print("OK")

    # Send message
    print("  3. Envoi du prompt...", end=' ', flush=True)
    success = send_message(model_uid, cascade_id, TEST_PROMPT)
    if not success:
        print("ECHEC")
        return None
    print("OK")

    # Wait for response
    print("  4. Attente de la reponse (10s)...", end=' ', flush=True)
    listener.join(timeout=12)
    print("OK")

    response_text = events_data[0] if events_data else ""

    if response_text:
        print(f"  Reponse recue: {len(response_text)} caracteres")
        preview = response_text[:200].replace('\n', ' ')
        print(f"  Apercu: {preview}...")
    else:
        print("  Aucune reponse capturee")

    return {
        'model': model_uid,
        'base_name': base_name,
        'cascade_id': cascade_id,
        'response': response_text,
        'response_length': len(response_text)
    }

def main():
    print("="*70)
    print("TEST DES MODELES AVEC STREAMING")
    print("="*70)
    print(f"\nPrompt: \"{TEST_PROMPT}\"")
    print(f"Modeles a tester: {len(MODELS_TO_TEST)}")
    print()

    results = []

    for model in MODELS_TO_TEST:
        result = test_model_with_streaming(model)
        if result:
            results.append(result)
        time.sleep(2)

    # Summary
    print("\n" + "="*70)
    print("RESUME")
    print("="*70)

    for r in results:
        print(f"\n{r['base_name']}:")
        if r['response']:
            print(f"  Reponse ({r['response_length']} chars):")
            print(f"  {r['response'][:300]}...")
        else:
            print("  Aucune reponse capturee")

    # Save
    output = {
        'timestamp': '2026-05-04T13:32:00Z',
        'test_prompt': TEST_PROMPT,
        'results': results
    }

    with open('windsurf_streaming_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResultats sauvegardes: windsurf_streaming_test_results.json")

if __name__ == '__main__':
    main()
