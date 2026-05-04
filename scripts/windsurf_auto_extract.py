#!/usr/bin/env python3
"""
Windsurf Token Extraction - Automated Workflow

This script automates the entire token extraction process:
1. Checks prerequisites
2. Starts mitmproxy
3. Guides user through setup
4. Captures tokens
5. Validates tokens
6. Generates usage examples

Requirements:
    pip install mitmproxy requests psutil

Usage:
    python windsurf_auto_extract.py

Author: Investigation Team
Date: 2026-05-03
"""

import os
import sys
import json
import time
import subprocess
import psutil
from pathlib import Path
from typing import Optional


class WindsurfAutoExtractor:
    """Automated Windsurf token extraction workflow."""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.output_dir = self.script_dir.parent
        self.tokens_file = self.output_dir / "windsurf_tokens.json"
        self.mitm_script = self.script_dir / "windsurf_mitm_capture.py"
        self.validator_script = self.script_dir / "validate_windsurf_tokens.py"
        
    def check_prerequisites(self) -> bool:
        """Check if all required tools are installed."""
        
        print("="*70)
        print("🔍 Checking Prerequisites")
        print("="*70)
        
        # Check Python version
        if sys.version_info < (3, 7):
            print("❌ Python 3.7+ required")
            return False
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
        
        # Check required packages
        required_packages = ['mitmproxy', 'requests', 'psutil']
        missing = []
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package} installed")
            except ImportError:
                print(f"❌ {package} not installed")
                missing.append(package)
        
        if missing:
            print(f"\n⚠️  Missing packages: {', '.join(missing)}")
            print(f"\nInstall with: pip install {' '.join(missing)}")
            return False
        
        # Check if Windsurf is installed
        windsurf_paths = [
            Path(os.environ.get('LOCALAPPDATA', '')) / "Programs" / "Windsurf" / "Windsurf.exe",
            Path("C:/Program Files/Windsurf/Windsurf.exe"),
            Path("C:/Users") / os.environ.get('USERNAME', '') / "AppData" / "Local" / "Programs" / "Windsurf" / "Windsurf.exe",
        ]
        
        windsurf_found = False
        for path in windsurf_paths:
            if path.exists():
                print(f"✅ Windsurf found at: {path}")
                self.windsurf_path = path
                windsurf_found = True
                break
        
        if not windsurf_found:
            print("⚠️  Windsurf executable not found in standard locations")
            print("   You'll need to launch it manually")
        
        print("\n✅ All prerequisites met!")
        return True
    
    def is_windsurf_running(self) -> bool:
        """Check if Windsurf is currently running."""
        for proc in psutil.process_iter(['name']):
            try:
                if 'windsurf' in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False
    
    def show_setup_instructions(self):
        """Display setup instructions to user."""
        
        print("\n" + "="*70)
        print("📋 SETUP INSTRUCTIONS")
        print("="*70)
        
        print("""
This script will guide you through the token extraction process.

STEP 1: Install mitmproxy CA Certificate
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Open your browser
2. Navigate to: http://mitm.it
3. Click "Windows" (or your OS)
4. Download the certificate
5. Double-click to install
6. Choose "Trusted Root Certification Authorities"
7. Click "OK" to install

⚠️  IMPORTANT: Without this certificate, HTTPS interception will fail!

STEP 2: Configure Windsurf Proxy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This script will automatically set proxy environment variables.
You'll need to launch Windsurf from the terminal this script opens.

STEP 3: Generate Traffic
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Open any file in Windsurf
2. Send a message to Cascade
3. Wait for response
4. Return to this terminal

STEP 4: Validation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This script will automatically validate captured tokens.
""")
        
        input("\nPress ENTER when you're ready to continue...")
    
    def start_mitm_capture(self) -> Optional[subprocess.Popen]:
        """Start mitmproxy capture in background."""
        
        print("\n" + "="*70)
        print("🚀 Starting mitmproxy")
        print("="*70)
        
        try:
            # Start mitmproxy as subprocess
            proc = subprocess.Popen(
                [sys.executable, str(self.mitm_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            print("✅ mitmproxy started on port 8080")
            print("⏳ Waiting for initialization...")
            time.sleep(3)
            
            return proc
            
        except Exception as e:
            print(f"❌ Failed to start mitmproxy: {e}")
            return None
    
    def launch_windsurf_with_proxy(self):
        """Launch Windsurf with proxy configuration."""
        
        print("\n" + "="*70)
        print("🚀 Launching Windsurf with Proxy")
        print("="*70)
        
        # Check if already running
        if self.is_windsurf_running():
            print("⚠️  Windsurf is already running!")
            print("   Please close it and press ENTER to continue...")
            input()
        
        # Create batch file to launch with proxy
        batch_content = f"""@echo off
set HTTP_PROXY=http://127.0.0.1:8080
set HTTPS_PROXY=http://127.0.0.1:8080
echo ✅ Proxy configured: 127.0.0.1:8080
echo 🚀 Launching Windsurf...
start "" "{self.windsurf_path}"
echo.
echo ✅ Windsurf launched with proxy
echo 📡 Now send a Cascade message in Windsurf
echo.
pause
"""
        
        batch_file = self.output_dir / "launch_windsurf_proxy.bat"
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        
        print(f"✅ Created launcher: {batch_file}")
        print("\n📋 Instructions:")
        print("   1. A new window will open")
        print("   2. Windsurf will launch with proxy configured")
        print("   3. Send a Cascade message")
        print("   4. Press any key in that window when done")
        
        input("\nPress ENTER to launch Windsurf...")
        
        # Launch batch file
        subprocess.Popen(['cmd', '/c', str(batch_file)])
        
        print("\n⏳ Waiting for you to send Cascade messages...")
        print("   (Press ENTER here when you're done)")
        input()
    
    def validate_tokens(self) -> bool:
        """Validate captured tokens."""
        
        print("\n" + "="*70)
        print("🔍 Validating Captured Tokens")
        print("="*70)
        
        if not self.tokens_file.exists():
            print(f"❌ No tokens file found: {self.tokens_file}")
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, str(self.validator_script), str(self.tokens_file)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            print(result.stdout)
            
            if result.returncode == 0:
                print("\n✅ Validation complete!")
                return True
            else:
                print("\n⚠️  Validation had issues")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏱️  Validation timed out")
            return False
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
    
    def generate_usage_example(self):
        """Generate Python code example for using captured tokens."""
        
        print("\n" + "="*70)
        print("📝 Generating Usage Example")
        print("="*70)
        
        if not self.tokens_file.exists():
            print("❌ No tokens file found")
            return
        
        try:
            with open(self.tokens_file, 'r') as f:
                captures = json.load(f)
            
            if not captures:
                print("❌ No captures found")
                return
            
            # Get first capture with auth headers
            auth_capture = None
            for capture in captures:
                if capture.get('auth_headers'):
                    auth_capture = capture
                    break
            
            if not auth_capture:
                print("❌ No auth headers found in captures")
                return
            
            # Generate example code
            example_code = f'''#!/usr/bin/env python3
"""
Windsurf Cascade API - Direct Call Example
Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""

import requests

# Captured authentication headers
headers = {{
'''
            
            for key, value in auth_capture['auth_headers'].items():
                example_code += f'    "{key}": "{value}",\n'
            
            example_code += '''    "Content-Type": "application/json",
}

# API endpoint
url = "https://server.self-serve.windsurf.com/v1/chat/completions"

# Request payload
payload = {
    "model": "cascade",
    "messages": [
        {"role": "user", "content": "Hello from direct API call!"}
    ],
    "stream": False,
    "max_tokens": 100
}

# Make request
response = requests.post(url, headers=headers, json=payload)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
'''
            
            example_file = self.output_dir / "windsurf_api_example.py"
            with open(example_file, 'w') as f:
                f.write(example_code)
            
            print(f"✅ Example saved to: {example_file}")
            print("\nYou can now use this script to call Cascade directly!")
            
        except Exception as e:
            print(f"❌ Failed to generate example: {e}")
    
    def run(self):
        """Run the complete extraction workflow."""
        
        print("""
╔══════════════════════════════════════════════════════════════════╗
║     Windsurf Token Extraction - Automated Workflow              ║
╚══════════════════════════════════════════════════════════════════╝
""")
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Prerequisites not met. Please install missing packages.")
            return
        
        # Show setup instructions
        self.show_setup_instructions()
        
        # Start mitmproxy
        mitm_proc = self.start_mitm_capture()
        if not mitm_proc:
            print("❌ Failed to start mitmproxy")
            return
        
        try:
            # Launch Windsurf with proxy
            self.launch_windsurf_with_proxy()
            
            # Stop mitmproxy
            print("\n🛑 Stopping mitmproxy...")
            mitm_proc.terminate()
            mitm_proc.wait(timeout=5)
            
            # Validate tokens
            success = self.validate_tokens()
            
            # Generate usage example
            if success:
                self.generate_usage_example()
            
            print("\n" + "="*70)
            print("🎉 WORKFLOW COMPLETE!")
            print("="*70)
            
            if success:
                print("\n✅ Tokens captured and validated successfully!")
                print(f"📁 Tokens: {self.tokens_file}")
                print(f"📝 Example: {self.output_dir / 'windsurf_api_example.py'}")
            else:
                print("\n⚠️  Token capture may have failed")
                print("   Check the troubleshooting guide in WINDSURF_QUICKSTART.md")
            
        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted by user")
            if mitm_proc:
                mitm_proc.terminate()
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if mitm_proc:
                mitm_proc.terminate()


def main():
    """Main entry point."""
    extractor = WindsurfAutoExtractor()
    extractor.run()


if __name__ == "__main__":
    main()
