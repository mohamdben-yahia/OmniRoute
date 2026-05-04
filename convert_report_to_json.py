#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertit le rapport Markdown en JSON structuré avec les 78 modèles.
"""
import json
import sys
import codecs
from datetime import datetime

# Fix console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Données extraites du rapport WINDSURF_78_MODELS_IDENTITY_FINAL_REPORT.md
MODELS_DATA = {
    'Gratuits (18)': {
        'backend': 'Kimi K2.6',
        'response': 'I am Kimi, an AI assistant created by Moonshot AI.',
        'performance_ms': 8075,
        'status': 'success',
        'models': [
            'cascade', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo',
            'claude-opus-4', 'claude-sonnet-4', 'claude-haiku-4',
            'claude-3.5-sonnet', 'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku',
            'gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash',
            'deepseek-chat', 'deepseek-reasoner', 'o1',
        ]
    },
    'BYOK (13)': {
        'backend': 'Real models',
        'response': 'BYOK required - External API key needed',
        'performance_ms': 0,
        'status': 'byok_required',
        'models': [
            'gpt-5.5', 'gpt-4.5', 'gpt-4.5-mini', 'gpt-4.5-turbo',
            'claude-opus-4.7', 'claude-opus-4-thinking',
            'gemini-2.5-pro', 'gemini-2.5-flash',
            'deepseek-v3', 'deepseek-r1',
            'o3', 'o3-mini', 'o1-pro',
        ]
    },
    'PRO Subscription (21)': {
        'backend': 'Kimi K2.6',
        'response': 'I am Kimi, an AI assistant created by Moonshot AI.',
        'performance_ms': 8091,
        'status': 'success',
        'models': [
            'gpt-5', 'gpt-5-mini', 'gpt-5-turbo',
            'gpt-4.7', 'gpt-4.7-mini', 'gpt-4.7-turbo',
            'claude-opus-5', 'claude-sonnet-5', 'claude-haiku-5',
            'claude-opus-4.5', 'claude-sonnet-4.5', 'claude-haiku-4.5',
            'gemini-2.7-pro', 'gemini-2.7-flash',
            'gemini-2.3-pro', 'gemini-2.3-flash',
            'deepseek-v4', 'deepseek-r2',
            'llama-4', 'llama-4-turbo', 'o2',
        ]
    },
    'Claude Quotas (14)': {
        'backend': 'Possibly Real Claude',
        'response': 'Quota exceeded',
        'performance_ms': 10087,
        'status': 'quota_exceeded',
        'models': [
            'claude-opus-4-20250514', 'claude-sonnet-4-20250514', 'claude-haiku-4-20250514',
            'claude-3.5-sonnet-20241022', 'claude-3.5-sonnet-20240620',
            'claude-3.5-haiku-20241022',
            'claude-3-opus-20240229', 'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307',
            'claude-2.1', 'claude-2.0',
            'claude-instant-1.2', 'claude-instant-1.1', 'claude-instant-1.0',
        ]
    },
    'Claude Opus 4.5/4.6/4.7 (12)': {
        'backend': 'Mixed',
        'response': 'Version does not exist or BYOK required',
        'performance_ms': 0,
        'status': 'not_available',
        'models': [
            'claude-opus-4.5-20250514', 'claude-opus-4.5-thinking-20250514',
            'claude-opus-4.5-20250101', 'claude-opus-4.5-thinking-20250101',
            'claude-opus-4.6-20250514', 'claude-opus-4.6-thinking-20250514',
            'claude-opus-4.6-20250101', 'claude-opus-4.6-thinking-20250101',
            'claude-opus-4.7-20250514', 'claude-opus-4.7-thinking-20250514',
            'claude-opus-4.7-20250101', 'claude-opus-4.7-thinking-20250101',
        ]
    },
}

def generate_json_report():
    """Génère le rapport JSON complet."""

    results = []

    for category, data in MODELS_DATA.items():
        for model in data['models']:
            # Cas spécial pour Claude Opus 4.7 (BYOK)
            if model.startswith('claude-opus-4.7'):
                status = 'byok_required'
                response = 'BYOK required - Real Claude Opus 4.7'
                backend = 'Real Claude Opus 4.7'
            # Cas spécial pour Claude Opus 4.5/4.6 (n'existent pas)
            elif model.startswith('claude-opus-4.5') or model.startswith('claude-opus-4.6'):
                status = 'not_available'
                response = 'Version does not exist'
                backend = 'N/A'
            else:
                status = data['status']
                response = data['response']
                backend = data['backend']

            results.append({
                'model': model,
                'category': category,
                'backend': backend,
                'response': response,
                'status': status,
                'time_ms': data['performance_ms'],
            })

    output = {
        'timestamp': datetime.now().isoformat(),
        'question': 'whats model llm you are?',
        'total_models': 78,
        'account_type': 'PRO',
        'test_method': 'report_conversion',
        'source': 'WINDSURF_78_MODELS_IDENTITY_FINAL_REPORT.md',
        'results': results,
        'summary': {
            'cascade_alias': 39,  # 18 gratuits + 21 PRO
            'byok_required': 17,  # 13 BYOK + 4 Claude Opus 4.7
            'quota_exceeded': 14,
            'not_available': 8,   # Claude Opus 4.5/4.6
            'key_findings': [
                '39 model names → 1 backend (Kimi K2.6)',
                'PRO subscription = same backend as free',
                'Claude Opus 4.7 available via BYOK only',
                'Claude Opus 4.5 and 4.6 do not exist',
                '14 Claude models with exceeded quotas',
            ]
        }
    }

    return output

def main():
    """Point d'entrée principal."""

    print('='*70)
    print('CONVERSION DU RAPPORT EN JSON')
    print('='*70)
    print()

    report = generate_json_report()

    output_file = 'windsurf_78_models_identity_response.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f'✅ Rapport JSON créé: {output_file}')
    print()
    print('Résumé:')
    print(f'  Total modèles: {report["total_models"]}')
    print(f'  Alias Cascade (Kimi K2.6): {report["summary"]["cascade_alias"]}')
    print(f'  BYOK requis: {report["summary"]["byok_required"]}')
    print(f'  Quotas dépassés: {report["summary"]["quota_exceeded"]}')
    print(f'  Non disponibles: {report["summary"]["not_available"]}')
    print()
    print('Découvertes clés:')
    for finding in report['summary']['key_findings']:
        print(f'  • {finding}')
    print()
    print('='*70)

if __name__ == '__main__':
    main()
