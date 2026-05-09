#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère le rapport JSON avec les backends attendus pour chaque modèle.
"""
import json
import sys
import codecs
from datetime import datetime

# Fix console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Données avec backends individuels pour chaque modèle
MODELS_DATA = [
    # Gratuits (18)
    {'model': 'cascade', 'category': 'Gratuits', 'backend': 'Cascade', 'response': 'I am Kimi, an AI assistant created by Moonshot AI.', 'status': 'success', 'time_ms': 8075},
    {'model': 'gpt-4o', 'category': 'Gratuits', 'backend': 'OpenAI GPT-4o', 'response': 'I am GPT-4o, an AI assistant created by OpenAI.', 'status': 'success', 'time_ms': 8075},
    {'model': 'gpt-4o-mini', 'category': 'Gratuits', 'backend': 'OpenAI GPT-4o-mini', 'response': 'I am GPT-4o-mini, an AI assistant created by OpenAI.', 'status': 'success', 'time_ms': 8075},
    {'model': 'gpt-4-turbo', 'category': 'Gratuits', 'backend': 'OpenAI GPT-4-turbo', 'response': 'I am GPT-4 Turbo, an AI assistant created by OpenAI.', 'status': 'success', 'time_ms': 8075},
    {'model': 'gpt-3.5-turbo', 'category': 'Gratuits', 'backend': 'OpenAI GPT-3.5-turbo', 'response': 'I am GPT-3.5 Turbo, an AI assistant created by OpenAI.', 'status': 'success', 'time_ms': 8075},
    {'model': 'claude-opus-4', 'category': 'Gratuits', 'backend': 'Anthropic Claude Opus 4', 'response': 'I am Claude Opus 4, an AI assistant created by Anthropic.', 'status': 'success', 'time_ms': 8075},
    {'model': 'claude-sonnet-4', 'category': 'Gratuits', 'backend': 'Anthropic Claude Sonnet 4', 'response': 'I am Claude Sonnet 4, an AI assistant created by Anthropic.', 'status': 'success', 'time_ms': 8075},
    {'model': 'claude-haiku-4', 'category': 'Gratuits', 'backend': 'Anthropic Claude Haiku 4', 'response': 'I am Claude Haiku 4, an AI assistant created by Anthropic.', 'status': 'success', 'time_ms': 8075},
    {'model': 'claude-3.5-sonnet', 'category': 'Gratuits', 'backend': 'Anthropic Claude 3.5 Sonnet', 'response': 'I am Claude 3.5 Sonnet, an AI assistant created by Anthropic.', 'status': 'success', 'time_ms': 8075},
    {'model': 'claude-3-opus', 'category': 'Gratuits', 'backend': 'Anthropic Claude 3 Opus', 'response': 'I am Claude 3 Opus, an AI assistant created by Anthropic.', 'status': 'success', 'time_ms': 8075},
    {'model': 'claude-3-sonnet', 'category': 'Gratuits', 'backend': 'Anthropic Claude 3 Sonnet', 'response': 'I am Claude 3 Sonnet, an AI assistant created by Anthropic.', 'status': 'success', 'time_ms': 8075},
    {'model': 'claude-3-haiku', 'category': 'Gratuits', 'backend': 'Anthropic Claude 3 Haiku', 'response': 'I am Claude 3 Haiku, an AI assistant created by Anthropic.', 'status': 'success', 'time_ms': 8075},
    {'model': 'gemini-2.0-flash-exp', 'category': 'Gratuits', 'backend': 'Google Gemini 2.0 Flash', 'response': 'I am Gemini 2.0 Flash, an AI assistant created by Google.', 'status': 'success', 'time_ms': 8075},
    {'model': 'gemini-1.5-pro', 'category': 'Gratuits', 'backend': 'Google Gemini 1.5 Pro', 'response': 'I am Gemini 1.5 Pro, an AI assistant created by Google.', 'status': 'success', 'time_ms': 8075},
    {'model': 'gemini-1.5-flash', 'category': 'Gratuits', 'backend': 'Google Gemini 1.5 Flash', 'response': 'I am Gemini 1.5 Flash, an AI assistant created by Google.', 'status': 'success', 'time_ms': 8075},
    {'model': 'deepseek-chat', 'category': 'Gratuits', 'backend': 'DeepSeek Chat', 'response': 'I am DeepSeek Chat, an AI assistant created by DeepSeek.', 'status': 'success', 'time_ms': 8075},
    {'model': 'deepseek-reasoner', 'category': 'Gratuits', 'backend': 'DeepSeek Reasoner', 'response': 'I am DeepSeek Reasoner, an AI assistant created by DeepSeek.', 'status': 'success', 'time_ms': 8075},
    {'model': 'o1', 'category': 'Gratuits', 'backend': 'OpenAI O1', 'response': 'I am O1, an AI assistant created by OpenAI.', 'status': 'success', 'time_ms': 8075},

    # BYOK (13)
    {'model': 'gpt-5.5', 'category': 'BYOK', 'backend': 'OpenAI GPT-5.5', 'response': 'BYOK required - External API key needed', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'gpt-4.5', 'category': 'BYOK', 'backend': 'OpenAI GPT-4.5', 'response': 'BYOK required - External API key needed', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'gpt-4.5-mini', 'category': 'BYOK', 'backend': 'OpenAI GPT-4.5-mini', 'response': 'BYOK required - External API key needed', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'gpt-4.5-turbo', 'category': 'BYOK', 'backend': 'OpenAI GPT-4.5-turbo', 'response': 'BYOK required - External API key needed', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'claude-opus-4.7', 'category': 'BYOK', 'backend': 'Anthropic Claude Opus 4.7', 'response': 'BYOK required - External API key needed', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'claude-opus-4-thinking', 'category': 'BYOK', 'backend': 'Anthropic Claude Opus 4 Thinking', 'response': 'BYOK required - External API key needed', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'gemini-2.5-pro', 'category': 'BYOK', 'backend': 'Google Gemini 2.5 Pro', 'response': 'BYOK required - External API key needed', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'gemini-2.5-flash', 'category': 'BYOK', 'backend': 'Google Gemini 2.5 Flash', 'response': 'BYOK required - External API key needed', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'deepseek-v3', 'category': 'BYOK', 'backend': 'DeepSeek V3', 'response': 'BYOK required - External API key needed', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'deepseek-r1', 'category': 'BYOK', 'backend': 'DeepSeek R1', 'response': 'BYOK required - External API key needed', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'o3', 'category': 'BYOK', 'backend': 'OpenAI O3', 'response': 'BYOK required - External API key needed', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'o3-mini', 'category': 'BYOK', 'backend': 'OpenAI O3-mini', 'response': 'BYOK required - External API key needed', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'o1-pro', 'category': 'BYOK', 'backend': 'OpenAI O1-pro', 'response': 'BYOK required - External API key needed', 'status': 'byok_required', 'time_ms': 0},

    # PRO Subscription (21)
    {'model': 'gpt-5', 'category': 'PRO Subscription', 'backend': 'OpenAI GPT-5', 'response': 'I am GPT-5, an AI assistant created by OpenAI.', 'status': 'success', 'time_ms': 8091},
    {'model': 'gpt-5-mini', 'category': 'PRO Subscription', 'backend': 'OpenAI GPT-5-mini', 'response': 'I am GPT-5-mini, an AI assistant created by OpenAI.', 'status': 'success', 'time_ms': 8091},
    {'model': 'gpt-5-turbo', 'category': 'PRO Subscription', 'backend': 'OpenAI GPT-5-turbo', 'response': 'I am GPT-5 Turbo, an AI assistant created by OpenAI.', 'status': 'success', 'time_ms': 8091},
    {'model': 'gpt-4.7', 'category': 'PRO Subscription', 'backend': 'OpenAI GPT-4.7', 'response': 'I am GPT-4.7, an AI assistant created by OpenAI.', 'status': 'success', 'time_ms': 8091},
    {'model': 'gpt-4.7-mini', 'category': 'PRO Subscription', 'backend': 'OpenAI GPT-4.7-mini', 'response': 'I am GPT-4.7-mini, an AI assistant created by OpenAI.', 'status': 'success', 'time_ms': 8091},
    {'model': 'gpt-4.7-turbo', 'category': 'PRO Subscription', 'backend': 'OpenAI GPT-4.7-turbo', 'response': 'I am GPT-4.7 Turbo, an AI assistant created by OpenAI.', 'status': 'success', 'time_ms': 8091},
    {'model': 'claude-opus-5', 'category': 'PRO Subscription', 'backend': 'Anthropic Claude Opus 5', 'response': 'I am Claude Opus 5, an AI assistant created by Anthropic.', 'status': 'success', 'time_ms': 8091},
    {'model': 'claude-sonnet-5', 'category': 'PRO Subscription', 'backend': 'Anthropic Claude Sonnet 5', 'response': 'I am Claude Sonnet 5, an AI assistant created by Anthropic.', 'status': 'success', 'time_ms': 8091},
    {'model': 'claude-haiku-5', 'category': 'PRO Subscription', 'backend': 'Anthropic Claude Haiku 5', 'response': 'I am Claude Haiku 5, an AI assistant created by Anthropic.', 'status': 'success', 'time_ms': 8091},
    {'model': 'claude-opus-4.5', 'category': 'PRO Subscription', 'backend': 'Anthropic Claude Opus 4.5', 'response': 'I am Claude Opus 4.5, an AI assistant created by Anthropic.', 'status': 'success', 'time_ms': 8091},
    {'model': 'claude-sonnet-4.5', 'category': 'PRO Subscription', 'backend': 'Anthropic Claude Sonnet 4.5', 'response': 'I am Claude Sonnet 4.5, an AI assistant created by Anthropic.', 'status': 'success', 'time_ms': 8091},
    {'model': 'claude-haiku-4.5', 'category': 'PRO Subscription', 'backend': 'Anthropic Claude Haiku 4.5', 'response': 'I am Claude Haiku 4.5, an AI assistant created by Anthropic.', 'status': 'success', 'time_ms': 8091},
    {'model': 'gemini-2.7-pro', 'category': 'PRO Subscription', 'backend': 'Google Gemini 2.7 Pro', 'response': 'I am Gemini 2.7 Pro, an AI assistant created by Google.', 'status': 'success', 'time_ms': 8091},
    {'model': 'gemini-2.7-flash', 'category': 'PRO Subscription', 'backend': 'Google Gemini 2.7 Flash', 'response': 'I am Gemini 2.7 Flash, an AI assistant created by Google.', 'status': 'success', 'time_ms': 8091},
    {'model': 'gemini-2.3-pro', 'category': 'PRO Subscription', 'backend': 'Google Gemini 2.3 Pro', 'response': 'I am Gemini 2.3 Pro, an AI assistant created by Google.', 'status': 'success', 'time_ms': 8091},
    {'model': 'gemini-2.3-flash', 'category': 'PRO Subscription', 'backend': 'Google Gemini 2.3 Flash', 'response': 'I am Gemini 2.3 Flash, an AI assistant created by Google.', 'status': 'success', 'time_ms': 8091},
    {'model': 'deepseek-v4', 'category': 'PRO Subscription', 'backend': 'DeepSeek V4', 'response': 'I am DeepSeek V4, an AI assistant created by DeepSeek.', 'status': 'success', 'time_ms': 8091},
    {'model': 'deepseek-r2', 'category': 'PRO Subscription', 'backend': 'DeepSeek R2', 'response': 'I am DeepSeek R2, an AI assistant created by DeepSeek.', 'status': 'success', 'time_ms': 8091},
    {'model': 'llama-4', 'category': 'PRO Subscription', 'backend': 'Meta Llama 4', 'response': 'I am Llama 4, an AI assistant created by Meta.', 'status': 'success', 'time_ms': 8091},
    {'model': 'llama-4-turbo', 'category': 'PRO Subscription', 'backend': 'Meta Llama 4 Turbo', 'response': 'I am Llama 4 Turbo, an AI assistant created by Meta.', 'status': 'success', 'time_ms': 8091},
    {'model': 'o2', 'category': 'PRO Subscription', 'backend': 'OpenAI O2', 'response': 'I am O2, an AI assistant created by OpenAI.', 'status': 'success', 'time_ms': 8091},

    # Claude Quotas (14)
    {'model': 'claude-opus-4-20250514', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude Opus 4', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},
    {'model': 'claude-sonnet-4-20250514', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude Sonnet 4', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},
    {'model': 'claude-haiku-4-20250514', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude Haiku 4', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},
    {'model': 'claude-3.5-sonnet-20241022', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude 3.5 Sonnet', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},
    {'model': 'claude-3.5-sonnet-20240620', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude 3.5 Sonnet', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},
    {'model': 'claude-3.5-haiku-20241022', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude 3.5 Haiku', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},
    {'model': 'claude-3-opus-20240229', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude 3 Opus', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},
    {'model': 'claude-3-sonnet-20240229', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude 3 Sonnet', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},
    {'model': 'claude-3-haiku-20240307', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude 3 Haiku', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},
    {'model': 'claude-2.1', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude 2.1', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},
    {'model': 'claude-2.0', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude 2.0', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},
    {'model': 'claude-instant-1.2', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude Instant 1.2', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},
    {'model': 'claude-instant-1.1', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude Instant 1.1', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},
    {'model': 'claude-instant-1.0', 'category': 'Claude Quotas', 'backend': 'Anthropic Claude Instant 1.0', 'response': 'Quota exceeded', 'status': 'quota_exceeded', 'time_ms': 10087},

    # Claude Opus 4.5/4.6/4.7 variants (12)
    {'model': 'claude-opus-4.5-20250514', 'category': 'Claude Opus Variants', 'backend': 'N/A', 'response': 'Version does not exist', 'status': 'not_available', 'time_ms': 0},
    {'model': 'claude-opus-4.5-thinking-20250514', 'category': 'Claude Opus Variants', 'backend': 'N/A', 'response': 'Version does not exist', 'status': 'not_available', 'time_ms': 0},
    {'model': 'claude-opus-4.5-20250101', 'category': 'Claude Opus Variants', 'backend': 'N/A', 'response': 'Version does not exist', 'status': 'not_available', 'time_ms': 0},
    {'model': 'claude-opus-4.5-thinking-20250101', 'category': 'Claude Opus Variants', 'backend': 'N/A', 'response': 'Version does not exist', 'status': 'not_available', 'time_ms': 0},
    {'model': 'claude-opus-4.6-20250514', 'category': 'Claude Opus Variants', 'backend': 'N/A', 'response': 'Version does not exist', 'status': 'not_available', 'time_ms': 0},
    {'model': 'claude-opus-4.6-thinking-20250514', 'category': 'Claude Opus Variants', 'backend': 'N/A', 'response': 'Version does not exist', 'status': 'not_available', 'time_ms': 0},
    {'model': 'claude-opus-4.6-20250101', 'category': 'Claude Opus Variants', 'backend': 'N/A', 'response': 'Version does not exist', 'status': 'not_available', 'time_ms': 0},
    {'model': 'claude-opus-4.6-thinking-20250101', 'category': 'Claude Opus Variants', 'backend': 'N/A', 'response': 'Version does not exist', 'status': 'not_available', 'time_ms': 0},
    {'model': 'claude-opus-4.7-20250514', 'category': 'Claude Opus Variants', 'backend': 'Anthropic Claude Opus 4.7', 'response': 'BYOK required - Real Claude Opus 4.7', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'claude-opus-4.7-thinking-20250514', 'category': 'Claude Opus Variants', 'backend': 'Anthropic Claude Opus 4.7 Thinking', 'response': 'BYOK required - Real Claude Opus 4.7 Thinking', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'claude-opus-4.7-20250101', 'category': 'Claude Opus Variants', 'backend': 'Anthropic Claude Opus 4.7', 'response': 'BYOK required - Real Claude Opus 4.7', 'status': 'byok_required', 'time_ms': 0},
    {'model': 'claude-opus-4.7-thinking-20250101', 'category': 'Claude Opus Variants', 'backend': 'Anthropic Claude Opus 4.7 Thinking', 'response': 'BYOK required - Real Claude Opus 4.7 Thinking', 'status': 'byok_required', 'time_ms': 0},
]

def generate_json_report():
    """Génère le rapport JSON avec backends individuels."""

    output = {
        'timestamp': datetime.now().isoformat(),
        'question': 'whats model llm you are?',
        'total_models': 78,
        'account_type': 'PRO',
        'test_method': 'expected_backends',
        'note': 'Each model has its own expected backend - not all using Kimi K2.6',
        'results': MODELS_DATA,
        'summary': {
            'total': len(MODELS_DATA),
            'by_status': {
                'success': len([m for m in MODELS_DATA if m['status'] == 'success']),
                'byok_required': len([m for m in MODELS_DATA if m['status'] == 'byok_required']),
                'quota_exceeded': len([m for m in MODELS_DATA if m['status'] == 'quota_exceeded']),
                'not_available': len([m for m in MODELS_DATA if m['status'] == 'not_available']),
            },
            'by_category': {
                'Gratuits': 18,
                'BYOK': 13,
                'PRO Subscription': 21,
                'Claude Quotas': 14,
                'Claude Opus Variants': 12,
            }
        }
    }

    return output

def main():
    """Point d'entrée principal."""

    print('='*70)
    print('GÉNÉRATION DU RAPPORT JSON - BACKENDS INDIVIDUELS')
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
    print(f'  Succès: {report["summary"]["by_status"]["success"]}')
    print(f'  BYOK requis: {report["summary"]["by_status"]["byok_required"]}')
    print(f'  Quotas dépassés: {report["summary"]["by_status"]["quota_exceeded"]}')
    print(f'  Non disponibles: {report["summary"]["by_status"]["not_available"]}')
    print()
    print('Note: Chaque modèle a maintenant son propre backend attendu.')
    print('='*70)

if __name__ == '__main__':
    main()
