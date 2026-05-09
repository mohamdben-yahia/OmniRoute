#!/usr/bin/env python3
"""
Test les 8 modèles Windsurf découverts en utilisant windsurf_direct_probe.py
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Chemin vers le script windsurf_direct_probe.py
WINDSURF_PROBE_SCRIPT = Path(r"C:\Users\amine\AppData\Local\Programs\Windsurf\winsurftiwtest\scripts\windsurf_direct_probe.py")

# Le prompt de test
TEST_PROMPT = "Quel modèle LLM êtes-vous? Répondez en une phrase courte avec votre nom exact et vos capacités principales."

# Les 8 modèles à tester
MODELS = [
    {
        "num": 1,
        "name": "GPT-5.5 Low",
        "uid": "gpt-5-5-low-20260424",
    },
    {
        "num": 2,
        "name": "Claude Opus 4.7 Medium",
        "uid": "claude-opus-4-7-medium-20260424",
    },
    {
        "num": 3,
        "name": "Claude Opus 4.6 Thinking",
        "uid": "claude-opus-4-6-thinking-20260424",
    },
    {
        "num": 4,
        "name": "Claude Sonnet 4.6 Thinking",
        "uid": "claude-sonnet-4-6-thinking-20260424",
    },
    {
        "num": 5,
        "name": "DeepSeek V4",
        "uid": "deepseek-v4-20260424",
    },
    {
        "num": 6,
        "name": "Kimi K2.6",
        "uid": "kimi-k2-6-20260424",
    },
    {
        "num": 7,
        "name": "SWE-1.6",
        "uid": "swe-1-6-20260424",
    },
    {
        "num": 8,
        "name": "SWE-1.6 Fast",
        "uid": "swe-1-6-fast-20260424",
    },
]


def test_model_with_probe(model: dict) -> dict:
    """
    Teste un modèle en utilisant windsurf_direct_probe.py
    """
    print(f"\n{'='*70}")
    print(f"TEST {model['num']}/8: {model['name']}")
    print(f"UID: {model['uid']}")
    print('='*70)

    if not WINDSURF_PROBE_SCRIPT.exists():
        print(f"[ERREUR] Script windsurf_direct_probe.py introuvable: {WINDSURF_PROBE_SCRIPT}")
        return {
            'model': model['name'],
            'uid': model['uid'],
            'status': 'error',
            'error': 'Script windsurf_direct_probe.py introuvable',
            'response': None,
        }

    # Construire la commande
    cmd = [
        sys.executable,
        str(WINDSURF_PROBE_SCRIPT),
        "--mode", "cascade",
        "--model", model['uid'],
        "--prompt", TEST_PROMPT,
    ]

    print(f"Commande: {' '.join(cmd)}")
    print(f"Envoi du prompt...")

    try:
        # Exécuter le script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8',
            errors='replace'
        )

        print(f"\nCode de sortie: {result.returncode}")

        if result.returncode == 0:
            print(f"[OK] Succes")

            # Essayer d'extraire la réponse du stdout
            response_text = result.stdout.strip()

            # Chercher la réponse dans le stdout
            if "Response:" in response_text or "response" in response_text.lower():
                print(f"\nReponse capturee ({len(response_text)} caracteres)")
                print(f"Apercu: {response_text[:200]}...")
            else:
                print(f"\n[WARN] Reponse non trouvee dans stdout")
                print(f"Stdout: {response_text[:500]}...")

            return {
                'model': model['name'],
                'uid': model['uid'],
                'status': 'success',
                'response': response_text,
                'response_length': len(response_text),
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timestamp': datetime.now().isoformat(),
            }
        else:
            print(f"[ERREUR] Echec (code {result.returncode})")
            print(f"Stderr: {result.stderr[:500]}")

            return {
                'model': model['name'],
                'uid': model['uid'],
                'status': 'failed',
                'error': f"Exit code {result.returncode}",
                'response': None,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timestamp': datetime.now().isoformat(),
            }

    except subprocess.TimeoutExpired:
        print(f"[ERREUR] Timeout (>60s)")
        return {
            'model': model['name'],
            'uid': model['uid'],
            'status': 'timeout',
            'error': 'Timeout après 60 secondes',
            'response': None,
            'timestamp': datetime.now().isoformat(),
        }

    except Exception as e:
        print(f"[ERREUR] Erreur: {e}")
        return {
            'model': model['name'],
            'uid': model['uid'],
            'status': 'error',
            'error': str(e),
            'response': None,
            'timestamp': datetime.now().isoformat(),
        }


def save_results(results: list) -> None:
    """Sauvegarde les résultats en JSON"""
    output = {
        'timestamp': datetime.now().isoformat(),
        'test_prompt': TEST_PROMPT,
        'total_models': len(results),
        'results': results,
    }

    output_file = 'windsurf_probe_test_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Resultats sauvegardes: {output_file}")


def create_markdown_report(results: list) -> None:
    """Crée un rapport markdown"""
    filename = 'WINDSURF_PROBE_TEST_RESULTS.md'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Résultats Tests - 8 Modèles Windsurf (via windsurf_direct_probe.py)\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Prompt**: \"{TEST_PROMPT}\"\n\n")
        f.write("---\n\n")

        # Résumé
        success_count = sum(1 for r in results if r['status'] == 'success')
        f.write(f"## Résumé\n\n")
        f.write(f"- **Total**: {len(results)} modèles\n")
        f.write(f"- **Succès**: {success_count}/{len(results)}\n")
        f.write(f"- **Échecs**: {len(results) - success_count}/{len(results)}\n\n")
        f.write("---\n\n")

        # Détails par modèle
        for i, result in enumerate(results, 1):
            f.write(f"## {i}. {result['model']}\n\n")
            f.write(f"**UID**: `{result['uid']}`\n\n")
            f.write(f"**Statut**: {result['status']}\n\n")

            if result['status'] == 'success':
                f.write(f"**Longueur réponse**: {result.get('response_length', 0)} caractères\n\n")
                f.write("**Réponse**:\n\n")
                f.write(f"```\n{result.get('response', 'N/A')}\n```\n\n")
            else:
                f.write(f"**Erreur**: {result.get('error', 'N/A')}\n\n")
                if result.get('stderr'):
                    f.write(f"**Stderr**:\n\n")
                    f.write(f"```\n{result['stderr'][:500]}\n```\n\n")

            f.write("---\n\n")

    print(f"[OK] Rapport cree: {filename}")


def main():
    print("="*70)
    print("TEST DES 8 MODÈLES WINDSURF VIA windsurf_direct_probe.py")
    print("="*70)
    print()
    print(f"Script probe: {WINDSURF_PROBE_SCRIPT}")
    print(f"Prompt: \"{TEST_PROMPT}\"")
    print(f"Modèles à tester: {len(MODELS)}")
    print()

    if not WINDSURF_PROBE_SCRIPT.exists():
        print(f"[ERREUR] Script windsurf_direct_probe.py introuvable")
        print(f"Chemin: {WINDSURF_PROBE_SCRIPT}")
        return 1

    print("[OK] Script windsurf_direct_probe.py trouve")
    print()
    print("Demarrage des tests...")
    print()

    results = []

    for model in MODELS:
        result = test_model_with_probe(model)
        results.append(result)

        if model['num'] < len(MODELS):
            print(f"\n[OK] Modele {model['num']}/{len(MODELS)} termine")
            print(f"Prochain: {MODELS[model['num']]['name']}")
            print()

    print("\n" + "="*70)
    print("TOUS LES TESTS TERMINÉS")
    print("="*70)

    # Statistiques
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"\nRésultats:")
    print(f"  Succès: {success_count}/{len(results)}")
    print(f"  Échecs: {len(results) - success_count}/{len(results)}")

    # Sauvegarder
    save_results(results)
    create_markdown_report(results)

    print("\n[OK] Tests completes!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
