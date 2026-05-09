#!/usr/bin/env python3
"""
Test all 8 models with a prompt and compare their responses
Uses pyautogui to automate Windsurf interface
"""

import time
import json
import pyperclip
from datetime import datetime

# Test prompt
TEST_PROMPT = "Quel modèle LLM êtes-vous? Répondez en une phrase courte avec votre nom exact et vos capacités principales."

# Models to test
MODELS = [
    {"name": "GPT-5.5 Low", "uid": "gpt-5-5-low-20260424"},
    {"name": "Claude Opus 4.7 Medium", "uid": "claude-opus-4-7-medium-20260424"},
    {"name": "Claude Opus 4.6 Thinking", "uid": "claude-opus-4-6-thinking-20260424"},
    {"name": "Claude Sonnet 4.6 Thinking", "uid": "claude-sonnet-4-6-thinking-20260424"},
    {"name": "DeepSeek V4", "uid": "deepseek-v4-20260424"},
    {"name": "Kimi K2.6", "uid": "kimi-k2-6-20260424"},
    {"name": "SWE-1.6", "uid": "swe-1-6-20260424"},
    {"name": "SWE-1.6 Fast", "uid": "swe-1-6-fast-20260424"},
]

def test_model_manual(model):
    """Test a model with manual copy-paste"""
    print(f"\n{'='*70}")
    print(f"TEST: {model['name']}")
    print(f"UID: {model['uid']}")
    print('='*70)

    # Copy prompt to clipboard
    pyperclip.copy(TEST_PROMPT)

    print("\nINSTRUCTIONS:")
    print("1. Sélectionnez le modèle dans Windsurf")
    print(f"   Cherchez: {model['name']}")
    print("2. Collez le prompt (Ctrl+V) dans le chat")
    print("3. Appuyez sur Entrée")
    print("4. Attendez la réponse complète")
    print("5. Sélectionnez TOUTE la réponse (Ctrl+A dans la bulle)")
    print("6. Copiez la réponse (Ctrl+C)")
    print("7. Appuyez sur Entrée ici pour continuer")

    input("\nAppuyez sur Entrée quand vous avez copié la réponse...")

    # Get response from clipboard
    response = pyperclip.paste()

    if response == TEST_PROMPT:
        print("\n⚠️  ATTENTION: La réponse est identique au prompt!")
        print("Vous avez peut-être copié le prompt au lieu de la réponse.")
        retry = input("Voulez-vous réessayer? (o/n): ")
        if retry.lower() == 'o':
            return test_model_manual(model)
        else:
            response = "[Pas de réponse capturée]"

    print(f"\n✅ Réponse capturée: {len(response)} caractères")
    print(f"Aperçu: {response[:100]}...")

    return {
        'model': model['name'],
        'uid': model['uid'],
        'prompt': TEST_PROMPT,
        'response': response,
        'response_length': len(response),
        'timestamp': datetime.now().isoformat()
    }

def compare_responses(results):
    """Compare all model responses"""
    print("\n" + "="*70)
    print("COMPARAISON DES RÉPONSES")
    print("="*70)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['model']}")
        print("-" * 70)
        print(f"Longueur: {result['response_length']} caractères")
        print(f"Réponse: {result['response'][:200]}...")
        if len(result['response']) > 200:
            print(f"         [...{len(result['response']) - 200} caractères supplémentaires]")

    # Analysis
    print("\n" + "="*70)
    print("ANALYSE")
    print("="*70)

    # Shortest and longest
    shortest = min(results, key=lambda x: x['response_length'])
    longest = max(results, key=lambda x: x['response_length'])

    print(f"\nRéponse la plus courte: {shortest['model']} ({shortest['response_length']} chars)")
    print(f"Réponse la plus longue: {longest['model']} ({longest['response_length']} chars)")

    # Average length
    avg_length = sum(r['response_length'] for r in results) / len(results)
    print(f"Longueur moyenne: {avg_length:.0f} caractères")

    # Models that identified themselves
    print("\nModèles qui se sont identifiés correctement:")
    for result in results:
        response_lower = result['response'].lower()
        model_name_parts = result['model'].lower().split()

        # Check if model name appears in response
        identified = any(part in response_lower for part in model_name_parts if len(part) > 3)

        if identified:
            print(f"  ✅ {result['model']}")
        else:
            print(f"  ❌ {result['model']} (ne s'est pas identifié clairement)")

def main():
    print("="*70)
    print("TEST ET COMPARAISON DES 8 MODÈLES WINDSURF")
    print("="*70)
    print()
    print(f"Prompt de test: \"{TEST_PROMPT}\"")
    print(f"Modèles à tester: {len(MODELS)}")
    print()
    print("IMPORTANT:")
    print("- Gardez Windsurf ouvert avec le chat Cascade visible")
    print("- Le prompt sera automatiquement copié dans le presse-papier")
    print("- Vous devrez sélectionner le modèle et coller le prompt")
    print("- Puis copier la réponse complète du modèle")
    print()

    input("Appuyez sur Entrée pour commencer...")

    results = []

    for i, model in enumerate(MODELS, 1):
        print(f"\n\n{'#'*70}")
        print(f"MODÈLE {i}/{len(MODELS)}")
        print('#'*70)

        result = test_model_manual(model)
        results.append(result)

        if i < len(MODELS):
            print(f"\n✅ Modèle {i}/{len(MODELS)} terminé")
            print(f"Prochain: {MODELS[i]['name']}")
            input("\nAppuyez sur Entrée pour continuer avec le prochain modèle...")

    # Compare all responses
    compare_responses(results)

    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'test_prompt': TEST_PROMPT,
        'total_models': len(results),
        'results': results
    }

    output_file = 'windsurf_models_comparison.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n\n{'='*70}")
    print("RÉSULTATS SAUVEGARDÉS")
    print('='*70)
    print(f"Fichier: {output_file}")
    print(f"Modèles testés: {len(results)}")

    # Create markdown report
    report_file = 'WINDSURF_MODELS_COMPARISON_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Comparaison des 8 Modèles Windsurf\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Prompt**: \"{TEST_PROMPT}\"\n\n")
        f.write("---\n\n")

        for i, result in enumerate(results, 1):
            f.write(f"## {i}. {result['model']}\n\n")
            f.write(f"**UID**: `{result['uid']}`\n\n")
            f.write(f"**Longueur**: {result['response_length']} caractères\n\n")
            f.write("**Réponse**:\n\n")
            f.write(f"> {result['response']}\n\n")
            f.write("---\n\n")

        # Add comparison section
        f.write("## Comparaison\n\n")
        f.write("| Modèle | Longueur | Identifié |\n")
        f.write("|--------|----------|----------|\n")

        for result in results:
            response_lower = result['response'].lower()
            model_name_parts = result['model'].lower().split()
            identified = any(part in response_lower for part in model_name_parts if len(part) > 3)
            identified_str = "✅" if identified else "❌"

            f.write(f"| {result['model']} | {result['response_length']} | {identified_str} |\n")

    print(f"Rapport: {report_file}")
    print()
    print("✅ Tests terminés!")

if __name__ == '__main__':
    try:
        import pyperclip
    except ImportError:
        print("ERROR: pyperclip n'est pas installé")
        print("Installez-le avec: pip install pyperclip")
        exit(1)

    main()
