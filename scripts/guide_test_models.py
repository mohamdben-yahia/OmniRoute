#!/usr/bin/env python3
"""
Guide interactif pour tester les 8 modèles Windsurf
Affiche les instructions étape par étape
"""

import json
from datetime import datetime

# Le prompt de test
TEST_PROMPT = "Quel modèle LLM êtes-vous? Répondez en une phrase courte avec votre nom exact et vos capacités principales."

# Les 8 modèles à tester
MODELS = [
    {
        "num": 1,
        "name": "GPT-5.5 Low",
        "uid": "gpt-5-5-low-20260424",
        "search": "GPT-5.5 Low ou GPT 5.5 Low"
    },
    {
        "num": 2,
        "name": "Claude Opus 4.7 Medium",
        "uid": "claude-opus-4-7-medium-20260424",
        "search": "Claude Opus 4.7 Medium"
    },
    {
        "num": 3,
        "name": "Claude Opus 4.6 Thinking",
        "uid": "claude-opus-4-6-thinking-20260424",
        "search": "Claude Opus 4.6 Thinking"
    },
    {
        "num": 4,
        "name": "Claude Sonnet 4.6 Thinking",
        "uid": "claude-sonnet-4-6-thinking-20260424",
        "search": "Claude Sonnet 4.6 Thinking"
    },
    {
        "num": 5,
        "name": "DeepSeek V4",
        "uid": "deepseek-v4-20260424",
        "search": "DeepSeek V4 ou DeepSeek"
    },
    {
        "num": 6,
        "name": "Kimi K2.6",
        "uid": "kimi-k2-6-20260424",
        "search": "Kimi K2.6 ou Kimi"
    },
    {
        "num": 7,
        "name": "SWE-1.6",
        "uid": "swe-1-6-20260424",
        "search": "SWE-1.6 ou SWE 1.6"
    },
    {
        "num": 8,
        "name": "SWE-1.6 Fast",
        "uid": "swe-1-6-fast-20260424",
        "search": "SWE-1.6 Fast ou SWE Fast"
    }
]

def print_header():
    print("=" * 70)
    print("GUIDE DE TEST DES 8 MODÈLES WINDSURF")
    print("=" * 70)
    print()
    print(f"Prompt à utiliser: \"{TEST_PROMPT}\"")
    print()
    print("IMPORTANT:")
    print("- Ouvrez Windsurf avec le chat Cascade visible")
    print("- Copiez le prompt ci-dessus")
    print("- Suivez les instructions pour chaque modèle")
    print()

def print_model_instructions(model):
    print("\n" + "#" * 70)
    print(f"MODÈLE {model['num']}/8: {model['name']}")
    print("#" * 70)
    print()
    print(f"UID technique: {model['uid']}")
    print(f"Cherchez dans Windsurf: {model['search']}")
    print()
    print("ÉTAPES:")
    print("  1. Sélectionnez ce modèle dans le menu déroulant de Windsurf")
    print("  2. Collez le prompt dans le chat")
    print("  3. Appuyez sur Entrée")
    print("  4. Attendez la réponse complète (5-30 secondes)")
    print("  5. Lisez la réponse")
    print()

def collect_response(model):
    print(f"Réponse du modèle {model['name']}:")
    print("-" * 70)

    lines = []
    print("Collez la réponse ici (ligne vide pour terminer):")

    while True:
        try:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)
        except EOFError:
            break

    response = "\n".join(lines)

    if not response.strip():
        print("\n⚠️  Aucune réponse capturée!")
        retry = input("Voulez-vous réessayer? (o/n): ")
        if retry.lower() == 'o':
            return collect_response(model)
        else:
            response = "[Pas de réponse capturée]"

    print(f"\n✅ Réponse capturée: {len(response)} caractères")
    return response

def save_results(results):
    output = {
        'timestamp': datetime.now().isoformat(),
        'test_prompt': TEST_PROMPT,
        'total_models': len(results),
        'results': results
    }

    filename = 'windsurf_test_results.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Résultats sauvegardés dans: {filename}")

def create_markdown_report(results):
    filename = 'WINDSURF_TEST_RESULTS.md'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Résultats des Tests - 8 Modèles Windsurf\n\n")
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

        # Tableau de comparaison
        f.write("## Comparaison\n\n")
        f.write("| Modèle | Longueur (chars) |\n")
        f.write("|--------|------------------|\n")

        for result in results:
            f.write(f"| {result['model']} | {result['response_length']} |\n")

    print(f"✅ Rapport créé: {filename}")

def main():
    print_header()

    input("Appuyez sur Entrée pour commencer...")

    results = []

    for model in MODELS:
        print_model_instructions(model)

        input(f"\nAppuyez sur Entrée quand vous êtes prêt à tester {model['name']}...")

        response = collect_response(model)

        result = {
            'model': model['name'],
            'uid': model['uid'],
            'prompt': TEST_PROMPT,
            'response': response,
            'response_length': len(response),
            'timestamp': datetime.now().isoformat()
        }

        results.append(result)

        print(f"\n✅ Modèle {model['num']}/8 terminé")

        if model['num'] < 8:
            print(f"\nProchain: {MODELS[model['num']]['name']}")

    print("\n" + "=" * 70)
    print("TOUS LES TESTS TERMINÉS!")
    print("=" * 70)

    # Sauvegarder les résultats
    save_results(results)
    create_markdown_report(results)

    print("\n✅ Tests complétés avec succès!")
    print(f"✅ {len(results)} modèles testés")

if __name__ == '__main__':
    main()
