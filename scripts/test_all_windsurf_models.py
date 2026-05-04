#!/usr/bin/env python3
"""
Test tous les modèles Windsurf avec le message "quelle model llm vous etes"
"""

import os
import sys
import json
import subprocess
import time

# Liste complète des modèles à tester (de l'archive)
MODELS_TO_TEST = [
    # Anthropic
    'claude-3-5-sonnet-20241022',
    'claude-3-5-haiku-20241022',
    'claude-3-opus-20240229',

    # OpenAI
    'gpt-4o',
    'gpt-4o-mini',
    'o1-preview',
    'o1-mini',

    # Google
    'gemini-2.0-flash-exp',
    'gemini-1.5-pro',
    'gemini-1.5-flash',

    # DeepSeek
    'deepseek-chat',
    'deepseek-reasoner',

    # Autres
    'grok-2-1212',
    'llama-3.3-70b-versatile',
    'mixtral-8x7b-32768',

    # Modèles confirmés
    'kimi-k2-6',
    'kimi-k2-5',
    'glm-5',
    'glm-5-1',
    'swe-1-6-fast'
]

def test_model(model_uid):
    """Teste un modèle avec le message 'quelle model llm vous etes'"""

    env = os.environ.copy()
    env['WINDSURF_CHAT_MODEL_NAME'] = model_uid
    env['WINDSURF_CHAT_TEXT'] = 'quelle model llm vous etes'

    print(f"\n{'='*70}")
    print(f"Testing: {model_uid}")
    print(f"{'='*70}")

    try:
        result = subprocess.run(
            [sys.executable, 'windsurf_direct_probe.py', '--run-abc-experiment'],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(__file__)
        )

        if result.returncode != 0:
            print(f"[ERROR] Exit code {result.returncode}")
            if result.stderr:
                print(f"Stderr: {result.stderr[:200]}")
            return {
                'model': model_uid,
                'status': 'error',
                'exit_code': result.returncode,
                'error': result.stderr[:200] if result.stderr else 'Unknown error'
            }

        # Parser le JSON
        data = json.loads(result.stdout)

        # Extraire le statut du premier run
        for run_id, run_data in data.get('runs', {}).items():
            send_msg = run_data.get('sendUserCascadeMessage', {})
            status = send_msg.get('status')

            if status == 200:
                print(f"[SUCCESS] Status 200")

                # Essayer d'extraire la réponse
                trajectory = run_data.get('getCascadeTrajectory', {})
                response_preview = trajectory.get('bodyText', '')[:200]

                return {
                    'model': model_uid,
                    'status': 'success',
                    'http_status': 200,
                    'response_preview': response_preview
                }
            else:
                print(f"[REJECTED] Status {status}")
                struct_log = send_msg.get('structuredLog', {})
                error = struct_log.get('error_message', struct_log.get('rawBodyPreview', 'Unknown error'))

                return {
                    'model': model_uid,
                    'status': 'rejected',
                    'http_status': status,
                    'error': error[:200]
                }

        return {
            'model': model_uid,
            'status': 'unknown',
            'error': 'No run data found'
        }

    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] 30s")
        return {
            'model': model_uid,
            'status': 'timeout',
            'error': 'Test timeout after 30 seconds'
        }
    except json.JSONDecodeError as e:
        print(f"[JSON ERROR] {e}")
        return {
            'model': model_uid,
            'status': 'parse_error',
            'error': f'JSON decode error: {str(e)}'
        }
    except Exception as e:
        print(f"[EXCEPTION] {e}")
        return {
            'model': model_uid,
            'status': 'exception',
            'error': str(e)
        }

def main():
    print("="*70)
    print("Test de tous les modèles Windsurf")
    print("Message: 'quelle model llm vous etes'")
    print(f"Total: {len(MODELS_TO_TEST)} modèles")
    print("="*70)

    results = []
    success_count = 0
    rejected_count = 0
    error_count = 0

    for i, model in enumerate(MODELS_TO_TEST, 1):
        print(f"\n[{i}/{len(MODELS_TO_TEST)}] Testing {model}...")

        result = test_model(model)
        results.append(result)

        if result['status'] == 'success':
            success_count += 1
        elif result['status'] == 'rejected':
            rejected_count += 1
        else:
            error_count += 1

        # Pause entre les tests
        time.sleep(1)

    # Résumé final
    print("\n" + "="*70)
    print("RÉSUMÉ FINAL")
    print("="*70)

    print(f"\n[SUCCESS] {success_count}/{len(MODELS_TO_TEST)}")
    print(f"[REJECTED] {rejected_count}/{len(MODELS_TO_TEST)}")
    print(f"[ERRORS] {error_count}/{len(MODELS_TO_TEST)}")

    # Modèles qui fonctionnent
    print("\n[SUCCESS] Modeles Fonctionnels:")
    for result in results:
        if result['status'] == 'success':
            print(f"  - {result['model']}")
            if 'response_preview' in result and result['response_preview']:
                print(f"    Reponse: {result['response_preview'][:100]}...")

    # Modèles rejetés
    print("\n[REJECTED] Modeles Rejetes:")
    for result in results:
        if result['status'] == 'rejected':
            print(f"  - {result['model']} (Status {result.get('http_status', 'unknown')})")

    # Sauvegarder les résultats
    output_file = f'test_all_models_results_{int(time.time())}.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total': len(MODELS_TO_TEST),
            'success': success_count,
            'rejected': rejected_count,
            'errors': error_count,
            'results': results
        }, f, indent=2)

    print(f"\n📄 Résultats sauvegardés: {output_file}")
    print("="*70)

    return 0 if success_count > 0 else 1

if __name__ == '__main__':
    sys.exit(main())
