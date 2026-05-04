#!/usr/bin/env python3
"""
Windsurf Model Backend Discovery
Capture modelRouterUid pour identifier les vrais backends
"""
import json
import os
import sys
from pathlib import Path

# Import windsurf_direct_probe utilities
sys.path.insert(0, str(Path(__file__).parent))
from windsurf_direct_probe import (
    resolve_auth_context_for_mode,
    run_ls_emulator_cycle,
    emit_output
)

MODELS_TO_TEST = [
    # Famille Kimi
    "kimi-k2-6",
    "kimi-k2-5",
    "kimi-k2-7",

    # Famille Claude
    "claude-opus-4",
    "claude-sonnet-4",
    "claude-haiku-4",

    # Famille GPT
    "gpt-5",
    "gpt-4-turbo",
    "gpt-4",

    # Famille Gemini
    "gemini-3-flash",
    "gemini-2-pro",
    "gemini-pro",

    # Famille GLM
    "glm-5",
    "glm-5-1",
    "glm-4",

    # Spécialisés
    "adaptive-ss",
    "swe-1-6-fast",
]

def extract_model_router_uid(cycle_payload):
    """Extract modelRouterUid from AssignModel request"""
    assign_model = cycle_payload.get("assignModel")
    if not assign_model:
        return None

    request_preview = assign_model.get("requestPreview", {})
    return request_preview.get("modelRouterUid")

def test_model_backend(model_uid):
    """Test a model and extract its backend modelRouterUid"""
    print(f"Testing {model_uid}...", file=sys.stderr)

    # Set environment for this model
    os.environ["WINDSURF_CHAT_TEXT"] = "hello"
    os.environ["WINDSURF_CHAT_MODEL_NAME"] = model_uid

    # Get auth
    local_auth = resolve_auth_context_for_mode("ls_emulator")
    local_token = local_auth["token"]

    if not local_token:
        return {
            "model": model_uid,
            "error": "No token available",
            "modelRouterUid": None,
            "backend": None
        }

    # Run cycle
    try:
        exit_code, cycle_payload = run_ls_emulator_cycle(
            local_token,
            prompt_text="hello",
            run_id="backend-discovery"
        )

        # Extract modelRouterUid
        model_router_uid = extract_model_router_uid(cycle_payload)

        # Get status
        send_msg = cycle_payload.get("sendUserCascadeMessage", {})
        status = send_msg.get("status")

        return {
            "model": model_uid,
            "status": status,
            "modelRouterUid": model_router_uid,
            "backend": "unknown" if not model_router_uid else model_router_uid,
            "cascadeId": cycle_payload.get("startCascade", {}).get("cascadeId"),
            "error": None if status == 200 else send_msg.get("body", {}).get("message")
        }
    except Exception as e:
        return {
            "model": model_uid,
            "error": str(e),
            "modelRouterUid": None,
            "backend": None
        }

def main():
    results = []

    print("=== Windsurf Backend Discovery ===", file=sys.stderr)
    print(f"Testing {len(MODELS_TO_TEST)} models...\n", file=sys.stderr)

    for model_uid in MODELS_TO_TEST:
        result = test_model_backend(model_uid)
        results.append(result)

        # Print progress
        status_icon = "✅" if result["status"] == 200 else "❌"
        backend = result.get("modelRouterUid", "N/A")
        print(f"{status_icon} {model_uid}: {backend[:8]}..." if backend and backend != "N/A" else f"{status_icon} {model_uid}: {result.get('error', 'N/A')}", file=sys.stderr)

    # Group by backend
    backends = {}
    for result in results:
        if result["status"] == 200:
            backend_uid = result.get("modelRouterUid", "unknown")
            if backend_uid not in backends:
                backends[backend_uid] = []
            backends[backend_uid].append(result["model"])

    # Output results
    output = {
        "timestamp": "2026-05-04T00:26:00Z",
        "totalModels": len(MODELS_TO_TEST),
        "successfulTests": len([r for r in results if r["status"] == 200]),
        "uniqueBackends": len(backends),
        "backends": backends,
        "detailedResults": results
    }

    emit_output(output)

    # Print summary
    print("\n=== Summary ===", file=sys.stderr)
    print(f"Total models tested: {len(MODELS_TO_TEST)}", file=sys.stderr)
    print(f"Successful: {output['successfulTests']}", file=sys.stderr)
    print(f"Unique backends: {output['uniqueBackends']}", file=sys.stderr)
    print("\nBackends found:", file=sys.stderr)
    for backend_uid, models in backends.items():
        print(f"  {backend_uid[:16]}... → {len(models)} models: {', '.join(models[:3])}{'...' if len(models) > 3 else ''}", file=sys.stderr)

    return 0

if __name__ == "__main__":
    sys.exit(main())
