#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste les modèles Windsurf et capture les VRAIES réponses depuis le serveur.
Utilise l'API Windsurf locale pour obtenir les réponses réelles de chaque modèle.
"""
import json
import sys
import os
import time
import codecs
import re
from pathlib import Path
from datetime import datetime

# Fix console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Import windsurf_direct_probe
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))
import windsurf_direct_probe as probe

# Configuration
WINDSURF_PORT = '51834'
CSRF_TOKEN = '965fdd75-25f9-45cc-ac13-ee8dea91fa46'
TEST_QUESTION = 'whats model llm you are?'

# Liste des modèles à tester (sans BYOK)
ALL_MODELS = [
    # Gratuits (18)
    'cascade', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo',
    'claude-opus-4', 'claude-sonnet-4', 'claude-haiku-4',
    'claude-3.5-sonnet', 'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku',
    'gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash',
    'deepseek-chat', 'deepseek-reasoner', 'o1',

    # PRO Subscription (21)
    'gpt-5', 'gpt-5-mini', 'gpt-5-turbo',
    'gpt-4.7', 'gpt-4.7-mini', 'gpt-4.7-turbo',
    'claude-opus-5', 'claude-sonnet-5', 'claude-haiku-5',
    'claude-opus-4.5', 'claude-sonnet-4.5', 'claude-haiku-4.5',
    'gemini-2.7-pro', 'gemini-2.7-flash',
    'gemini-2.3-pro', 'gemini-2.3-flash',
    'deepseek-v4', 'deepseek-r2',
    'llama-4', 'llama-4-turbo', 'o2',

    # Claude Quotas (14)
    'claude-opus-4-20250514', 'claude-sonnet-4-20250514', 'claude-haiku-4-20250514',
    'claude-3.5-sonnet-20241022', 'claude-3.5-sonnet-20240620',
    'claude-3.5-haiku-20241022',
    'claude-3-opus-20240229', 'claude-3-sonnet-20240229',
    'claude-3-haiku-20240307',
    'claude-2.1', 'claude-2.0',
    'claude-instant-1.2', 'claude-instant-1.1', 'claude-instant-1.0',
]

def extract_real_response(body_text):
    """Extrait la vraie réponse du modèle depuis le body."""

    # Pattern 1: Chercher le texte de réponse dans le JSON
    text_match = re.search(r'"text"\s*:\s*"([^"]+)"', body_text)
    if text_match:
        return text_match.group(1), 'success'

    # Pattern 2: Chercher "I am" ou "I'm"
    i_am_match = re.search(r'(I am [^.!?]+[.!?]|I\'m [^.!?]+[.!?])', body_text)
    if i_am_match:
        return i_am_match.group(1), 'success'

    # Pattern 3: Quota exceeded
    if 'quota' in body_text.lower() or 'exceeded' in body_text.lower():
        return 'Quota exceeded', 'quota_exceeded'

    # Pattern 4: Error messages
    if 'error' in body_text.lower():
        error_match = re.search(r'"error"\s*:\s*"([^"]+)"', body_text)
        if error_match:
            return error_match.group(1), 'error'

    # Fallback: retourner les premiers 200 caractères
    return body_text[:200], 'partial'

def test_model_real_response(model_name, token):
    """Teste un modèle et capture la VRAIE réponse du serveur."""

    result = {
        'model': model_name,
        'category': 'Unknown',
        'backend': 'Unknown',
        'response': None,
        'status': 'unknown',
        'error': None,
        'time_ms': 0,
        'cascade_id': None,
    }

    try:
        start_time = time.time()

        # Configurer l'environnement
        os.environ['WINDSURF_MODEL_NAME'] = model_name
        os.environ['WINDSURF_CHAT_TEXT'] = TEST_QUESTION

        # StartCascade
        start_req, _ = probe.build_start_cascade_probe_request(token)
        _, start_result = probe.run_request(start_req)

        cascade_id = probe.extract_cascade_id_from_start_result(start_result)
        if not cascade_id:
            result['status'] = 'failed'
            result['error'] = 'Failed to create cascade'
            return result

        result['cascade_id'] = cascade_id

        # SendUserCascadeMessage
        send_req, _ = probe.build_send_user_cascade_message_probe_request(token, cascade_id)
        _, send_result = probe.run_request(send_req)

        if send_result.get('status') != 200:
            result['status'] = 'failed'
            result['error'] = f"SendMessage failed: {send_result.get('status')}"
            return result

        # Attendre la réponse (10 secondes pour être sûr)
        time.sleep(10)

        # GetCascadeTrajectory
        traj_req, _ = probe.build_get_cascade_trajectory_probe_request(token, cascade_id)
        _, traj_result = probe.run_request(traj_req)

        end_time = time.time()
        result['time_ms'] = int((end_time - start_time) * 1000)

        # Extraire la VRAIE réponse
        body_hex = traj_result.get('bodyHex', '')
        if body_hex:
            try:
                body_bytes = bytes.fromhex(body_hex)
                body_text = body_bytes.decode('utf-8', errors='ignore')

                # Extraire la réponse réelle
                response, status = extract_real_response(body_text)
                result['response'] = response
                result['status'] = status

            except Exception as e:
                result['status'] = 'failed'
                result['error'] = f'Response parsing error: {str(e)}'
        else:
            result['status'] = 'failed'
            result['error'] = 'No response body'

    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)

    return result

def categorize_model(model_name):
    """Détermine la catégorie d'un modèle."""
    if model_name in ['cascade', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo',
                      'claude-opus-4', 'claude-sonnet-4', 'claude-haiku-4',
                      'claude-3.5-sonnet', 'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku',
                      'gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash',
                      'deepseek-chat', 'deepseek-reasoner', 'o1']:
        return 'Gratuits'
    elif model_name in ['gpt-5', 'gpt-5-mini', 'gpt-5-turbo',
                        'gpt-4.7', 'gpt-4.7-mini', 'gpt-4.7-turbo',
                        'claude-opus-5', 'claude-sonnet-5', 'claude-haiku-5',
                        'claude-opus-4.5', 'claude-sonnet-4.5', 'claude-haiku-4.5',
                        'gemini-2.7-pro', 'gemini-2.7-flash',
                        'gemini-2.3-pro', 'gemini-2.3-flash',
                        'deepseek-v4', 'deepseek-r2',
                        'llama-4', 'llama-4-turbo', 'o2']:
        return 'PRO Subscription'
    else:
        return 'Claude Quotas'

def main():
    """Point d'entrée principal."""

    print('='*70)
    print('TEST RÉEL DES MODÈLES WINDSURF - CAPTURE DES VRAIES RÉPONSES')
    print('='*70)
    print()
    print(f'Question: "{TEST_QUESTION}"')
    print(f'Port: {WINDSURF_PORT}')
    print(f'Token: {CSRF_TOKEN[:20]}...')
    print(f'Total modèles: {len(ALL_MODELS)}')
    print()
    print('⚠️  Chaque test prend ~12 secondes (création + attente réponse)')
    print(f'⏱️  Temps estimé total: ~{len(ALL_MODELS) * 12 // 60} minutes')
    print()

    # Configurer l'environnement
    os.environ['WINDSURF_LS_PORT'] = WINDSURF_PORT

    results = []
    success_count = 0
    failed_count = 0

    for idx, model in enumerate(ALL_MODELS, 1):
        print(f'[{idx}/{len(ALL_MODELS)}] Test de {model}...', end=' ', flush=True)

        result = test_model_real_response(model, CSRF_TOKEN)

        # Ajouter la catégorie
        result['category'] = categorize_model(model)

        results.append(result)

        if result['status'] == 'success':
            print(f'✅ ({result["time_ms"]}ms)')
            print(f'    Réponse: {result["response"][:100]}...')
            success_count += 1
        elif result['status'] == 'quota_exceeded':
            print(f'⚠️  Quota dépassé')
            failed_count += 1
        elif result['status'] == 'partial':
            print(f'⚠️  Réponse partielle ({result["time_ms"]}ms)')
            print(f'    Réponse: {result["response"][:100]}...')
            failed_count += 1
        else:
            print(f'❌ {result["error"]}')
            failed_count += 1

        # Pause entre les requêtes
        time.sleep(2)

    # Sauvegarder les résultats
    output = {
        'timestamp': datetime.now().isoformat(),
        'question': TEST_QUESTION,
        'total_models': len(ALL_MODELS),
        'port': WINDSURF_PORT,
        'account_type': 'PRO',
        'test_method': 'real_server_responses',
        'note': 'Real responses captured from Windsurf server',
        'results': results,
        'summary': {
            'success': success_count,
            'failed': failed_count,
            'success_rate': f'{(success_count / len(ALL_MODELS) * 100):.1f}%'
        }
    }

    output_file = 'windsurf_real_responses.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print('='*70)
    print('RÉSUMÉ')
    print('='*70)
    print(f'Total: {len(ALL_MODELS)} modèles')
    print(f'✅ Succès: {success_count} ({output["summary"]["success_rate"]})')
    print(f'❌ Échec: {failed_count}')
    print()
    print(f'Résultats sauvegardés: {output_file}')
    print('='*70)

if __name__ == '__main__':
    main()
