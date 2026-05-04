#!/usr/bin/env python3
"""
Test simple de tous les modèles Windsurf avec message personnalisé
"""

import os
import sys
import json
import subprocess

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

def test_model(model):
    """Test un modèle avec le message personnalisé"""
    env = os.environ.copy()
    env['WINDSURF_CHAT_MODEL_NAME'] = model
    env['WINDSURF_CHAT_TEXT'] = MESSAGE

    print(f"\n{'='*70}")
    print(f"Testing: {model}")
    print(f"Message: {MESSAGE}")
    print(f"{'='*70}")

    try:
        # Appeler le probe sans --run-abc-experiment pour utiliser le flux normal
        result = subprocess.run(
            [sys.executable, 'windsurf_direct_probe.py'],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(__file__)
        )

        if result.returncode != 0:
            print(f"[ERROR] Exit code {result.returncode}")
            return {'model': model, 'status': 'error', 'error': 'Non-zero exit code'}

        # Parser la sortie JSON
        data = json.loads(result.stdout)

        # Vérifier le statut
        send_status = data.get('sendUserCascadeMessage', {}).get('status')

        if send_status == 200:
            print(f"[SUCCESS] Status 200")

            # Extraire la réponse si disponible
            response = data.get('response', '')
            if response:
                print(f"Response: {response[:200]}")
                return {
                    'model': model,
                    'status': 'success',
                    'response': response
                }
            else:
                print(f"[WARNING] No response content")
                return {
                    'model': model,
                    'status': 'success',
                    'response': ''
                }
        else:
            print(f"[REJECTED] Status {send_status}")
            error = data.get('sendUserCascadeMessage', {}).get('structuredLog', {}).get('error_message', 'Unknown')
            return {
                'model': model,
                'status': 'rejected',
                'http_status': send_status,
                'error': error
            }

    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT]")
        return {'model': model, 'status': 'timeout'}
    except json.JSONDecodeError as e:
        print(f"[JSON ERROR] {e}")
        return {'model': model, 'status': 'parse_error', 'error': str(e)}
    except Exception as e:
        print(f"[EXCEPTION] {e}")
        return {'model': model, 'status': 'exception', 'error': str(e)}

def main():
    print("="*70)
    print("Test de tous les modèles Windsurf")
    print(f"Message: '{MESSAGE}'")
    print(f"Total: {len(MODELS)} modèles")
    print("="*70)

    results = []
    success = 0
    rejected = 0
    errors = 0

    for model in MODELS:
        result = test_model(model)
        results.append(result)

        if result['status'] == 'success':
            success += 1
        elif result['status'] == 'rejected':
            rejected += 1
        else:
            errors += 1

    # Résumé
    print("\n" + "="*70)
    print("RESUME FINAL")
    print("="*70)
    print(f"\n[SUCCESS] {success}/{len(MODELS)}")
    print(f"[REJECTED] {rejected}/{len(MODELS)}")
    print(f"[ERRORS] {errors}/{len(MODELS)}")

    print("\n[SUCCESS] Modeles fonctionnels:")
    for r in results:
        if r['status'] == 'success':
            resp = r.get('response', '')
            print(f"  - {r['model']}")
            if resp:
                print(f"    Reponse: {resp[:150]}")

    print("\n[REJECTED] Modeles rejetes:")
    for r in results:
        if r['status'] == 'rejected':
            print(f"  - {r['model']} (Status {r.get('http_status', 'unknown')})")

    # Sauvegarder
    output = {
        'timestamp': '2026-05-04 02:06:00',
        'message': MESSAGE,
        'total': len(MODELS),
        'success': success,
        'rejected': rejected,
        'errors': errors,
        'results': results
    }

    with open('test_models_simple_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResultats sauvegardes: test_models_simple_results.json")
    print("="*70)

if __name__ == '__main__':
    sys.exit(main())
