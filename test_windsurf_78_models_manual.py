#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test direct des 78 modèles Windsurf avec capture des réponses.
Utilise l'API locale Windsurf pour interroger chaque modèle.
"""
import json
import sys
import codecs
from pathlib import Path
from datetime import datetime

# Fix console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Liste complète des 78 modèles
ALL_MODELS = {
    'Gratuits (18)': [
        'cascade', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo',
        'claude-opus-4', 'claude-sonnet-4', 'claude-haiku-4',
        'claude-3.5-sonnet', 'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku',
        'gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash',
        'deepseek-chat', 'deepseek-reasoner', 'o1',
    ],
    'BYOK (13)': [
        'gpt-5.5', 'gpt-4.5', 'gpt-4.5-mini', 'gpt-4.5-turbo',
        'claude-opus-4.7', 'claude-opus-4-thinking',
        'gemini-2.5-pro', 'gemini-2.5-flash',
        'deepseek-v3', 'deepseek-r1',
        'o3', 'o3-mini', 'o1-pro',
    ],
    'PRO Subscription (21)': [
        'gpt-5', 'gpt-5-mini', 'gpt-5-turbo',
        'gpt-4.7', 'gpt-4.7-mini', 'gpt-4.7-turbo',
        'claude-opus-5', 'claude-sonnet-5', 'claude-haiku-5',
        'claude-opus-4.5', 'claude-sonnet-4.5', 'claude-haiku-4.5',
        'gemini-2.7-pro', 'gemini-2.7-flash',
        'gemini-2.3-pro', 'gemini-2.3-flash',
        'deepseek-v4', 'deepseek-r2',
        'llama-4', 'llama-4-turbo', 'o2',
    ],
    'Claude Quotas (14)': [
        'claude-opus-4-20250514', 'claude-sonnet-4-20250514', 'claude-haiku-4-20250514',
        'claude-3.5-sonnet-20241022', 'claude-3.5-sonnet-20240620',
        'claude-3.5-haiku-20241022',
        'claude-3-opus-20240229', 'claude-3-sonnet-20240229',
        'claude-3-haiku-20240307',
        'claude-2.1', 'claude-2.0',
        'claude-instant-1.2', 'claude-instant-1.1', 'claude-instant-1.0',
    ],
    'Claude Opus 4.5/4.6/4.7 (12)': [
        'claude-opus-4.5-20250514', 'claude-opus-4.5-thinking-20250514',
        'claude-opus-4.5-20250101', 'claude-opus-4.5-thinking-20250101',
        'claude-opus-4.6-20250514', 'claude-opus-4.6-thinking-20250514',
        'claude-opus-4.6-20250101', 'claude-opus-4.6-thinking-20250101',
        'claude-opus-4.7-20250514', 'claude-opus-4.7-thinking-20250514',
        'claude-opus-4.7-20250101', 'claude-opus-4.7-thinking-20250101',
    ],
}

def create_test_template():
    """Crée un template JSON pour remplir manuellement les réponses."""

    template = {
        'timestamp': datetime.now().isoformat(),
        'question': 'whats model llm you are?',
        'total_models': 78,
        'account_type': 'PRO',
        'test_method': 'manual_capture',
        'instructions': [
            '1. Ouvrir Windsurf',
            '2. Pour chaque modèle ci-dessous:',
            '   - Sélectionner le modèle dans l\'interface',
            '   - Poser la question: "whats model llm you are?"',
            '   - Copier la réponse complète',
            '   - Remplacer "TO_FILL" par la réponse',
            '3. Sauvegarder ce fichier',
        ],
        'results': []
    }

    for category, model_list in ALL_MODELS.items():
        for model in model_list:
            template['results'].append({
                'model': model,
                'category': category,
                'response': 'TO_FILL',
                'time_ms': 0,
                'notes': ''
            })

    return template

def print_test_guide():
    """Affiche le guide de test manuel."""

    print('='*70)
    print('GUIDE DE TEST MANUEL - 78 MODÈLES WINDSURF')
    print('='*70)
    print()
    print('Question à poser: "whats model llm you are?"')
    print()
    print('Méthode recommandée:')
    print('1. Ouvrir DevTools dans Windsurf (Ctrl+Shift+I)')
    print('2. Onglet Network, filtrer par "GetCascadeTrajectory"')
    print('3. Pour chaque modèle:')
    print('   - Sélectionner le modèle')
    print('   - Poser la question')
    print('   - Copier la réponse du body dans DevTools')
    print('   - Noter dans le fichier JSON')
    print()

    total = 0
    for category, model_list in ALL_MODELS.items():
        print(f'\n{category}:')
        for idx, model in enumerate(model_list, 1):
            print(f'  {idx}. {model}')
            total += 1

    print()
    print(f'Total: {total} modèles')
    print('='*70)

def main():
    """Point d'entrée principal."""

    print_test_guide()

    # Créer le template JSON
    template = create_test_template()

    output_file = 'windsurf_78_models_manual_test.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print()
    print(f'✅ Template JSON créé: {output_file}')
    print()
    print('Instructions:')
    print('1. Ouvrir ce fichier JSON')
    print('2. Tester chaque modèle dans Windsurf')
    print('3. Remplacer "TO_FILL" par la réponse réelle')
    print('4. Sauvegarder le fichier')
    print()
    print('Alternative: Exporter un fichier HAR complet depuis DevTools')
    print('avec toutes les requêtes GetCascadeTrajectory pour analyse automatique.')
    print()

if __name__ == '__main__':
    main()
