#!/usr/bin/env python3
"""
Monitor Windsurf logs to capture model responses
Run this script WHILE testing models in Windsurf interface
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime

# Windsurf logs locations
WINDSURF_LOGS_PATHS = [
    Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "Windsurf" / "logs",
    Path(os.path.expanduser("~")) / "AppData" / "Local" / "Windsurf" / "logs",
    Path(os.path.expanduser("~")) / ".windsurf" / "logs",
]

def find_windsurf_logs():
    """Find Windsurf logs directory"""
    for path in WINDSURF_LOGS_PATHS:
        if path.exists():
            print(f"Found Windsurf logs: {path}")
            return path
    return None

def monitor_logs(duration=300):
    """Monitor logs for model responses"""
    logs_dir = find_windsurf_logs()

    if not logs_dir:
        print("ERROR: Windsurf logs directory not found")
        print("\nSearched in:")
        for path in WINDSURF_LOGS_PATHS:
            print(f"  - {path}")
        return None

    print(f"\nMonitoring logs for {duration} seconds...")
    print("Please test models in Windsurf now!")
    print()

    # Find most recent log files
    log_files = []
    for ext in ['*.log', '*.txt']:
        log_files.extend(logs_dir.glob(f"**/{ext}"))

    if not log_files:
        print("No log files found")
        return None

    # Sort by modification time
    log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    print(f"Monitoring {len(log_files[:5])} most recent log files:")
    for f in log_files[:5]:
        print(f"  - {f.name}")
    print()

    # Track file positions
    file_positions = {}
    for log_file in log_files[:5]:
        try:
            file_positions[log_file] = log_file.stat().st_size
        except:
            pass

    captured_data = []
    start_time = time.time()

    while time.time() - start_time < duration:
        for log_file, last_pos in list(file_positions.items()):
            try:
                current_size = log_file.stat().st_size

                if current_size > last_pos:
                    # New data available
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(last_pos)
                        new_data = f.read()

                        if new_data.strip():
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] New data in {log_file.name}: {len(new_data)} bytes")

                            # Look for model responses
                            if any(keyword in new_data.lower() for keyword in ['gpt', 'claude', 'deepseek', 'model', 'response']):
                                captured_data.append({
                                    'timestamp': datetime.now().isoformat(),
                                    'file': str(log_file),
                                    'data': new_data[:1000]  # First 1000 chars
                                })

                        file_positions[log_file] = current_size
            except:
                pass

        time.sleep(1)

    return captured_data

def main():
    print("="*70)
    print("WINDSURF LOG MONITOR - CAPTURE MODEL RESPONSES")
    print("="*70)
    print()
    print("This script monitors Windsurf logs while you test models.")
    print()
    print("INSTRUCTIONS:")
    print("1. Keep this script running")
    print("2. Open Windsurf")
    print("3. Test each model with the prompt:")
    print("   'Quel modèle LLM êtes-vous? Répondez en une phrase courte.'")
    print("4. Wait for responses")
    print("5. This script will capture log activity")
    print()

    input("Press Enter to start monitoring (5 minutes)...")
    print()

    captured = monitor_logs(duration=300)

    print()
    print("="*70)
    print("MONITORING COMPLETE")
    print("="*70)
    print()

    if captured:
        print(f"Captured {len(captured)} log entries")

        # Save results
        output = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': 300,
            'entries_captured': len(captured),
            'data': captured
        }

        output_file = 'windsurf_log_capture.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"Results saved to: {output_file}")
        print()

        # Show preview
        print("Preview of captured data:")
        for i, entry in enumerate(captured[:3], 1):
            print(f"\n{i}. {entry['timestamp']}")
            print(f"   File: {Path(entry['file']).name}")
            print(f"   Data: {entry['data'][:200]}...")
    else:
        print("No data captured")
        print()
        print("Possible reasons:")
        print("- Windsurf was not running")
        print("- No models were tested")
        print("- Logs are in a different location")
        print("- Windsurf uses a different logging mechanism")

if __name__ == '__main__':
    main()
