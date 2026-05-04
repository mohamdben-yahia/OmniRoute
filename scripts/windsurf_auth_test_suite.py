#!/usr/bin/env python3
"""
Windsurf Auth Test Suite — Quick Validation
============================================

Runs all authentication tests in sequence to validate the complete flow.

Usage:
    python windsurf_auth_test_suite.py
    python windsurf_auth_test_suite.py --skip-extraction  # Use existing tokens.json
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List


class TestResult:
    def __init__(self, name: str, success: bool, message: str, details: Any = None):
        self.name = name
        self.success = success
        self.message = message
        self.details = details
        self.timestamp = time.time()


class WindsurfAuthTestSuite:
    def __init__(self, skip_extraction: bool = False):
        self.skip_extraction = skip_extraction
        self.results: List[TestResult] = []
        self.scripts_dir = Path(__file__).parent
        self.tokens_file = self.scripts_dir / "tokens.json"
    
    def run_command(self, cmd: List[str], timeout: int = 30) -> Dict[str, Any]:
        """Run a command and return result."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.scripts_dir
            )
            
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Timeout after {timeout}s"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_cdp_availability(self) -> TestResult:
        """Test 1: Check if CDP is available."""
        print("\n🧪 Test 1: CDP Availability")
        print("-" * 60)
        
        try:
            import urllib.request
            response = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
            data = json.loads(response.read())
            
            if data:
                return TestResult(
                    "CDP Availability",
                    True,
                    f"✅ CDP available with {len(data)} targets",
                    {"target_count": len(data)}
                )
            else:
                return TestResult(
                    "CDP Availability",
                    False,
                    "❌ CDP available but no targets found"
                )
        
        except Exception as e:
            return TestResult(
                "CDP Availability",
                False,
                f"❌ CDP not available: {e}",
                {"error": str(e)}
            )
    
    def test_token_extraction(self) -> TestResult:
        """Test 2: Extract tokens via CDP."""
        print("\n🧪 Test 2: Token Extraction")
        print("-" * 60)
        
        if self.skip_extraction and self.tokens_file.exists():
            print("⏭️  Skipping extraction (using existing tokens.json)")
            return TestResult(
                "Token Extraction",
                True,
                "⏭️  Skipped (using existing tokens)",
                {"skipped": True}
            )
        
        cmd = [
            sys.executable,
            str(self.scripts_dir / "windsurf_token_extractor.py"),
            "--extract-all",
            "--output", str(self.tokens_file)
        ]
        
        result = self.run_command(cmd, timeout=15)
        
        if result["success"] and self.tokens_file.exists():
            # Load and validate tokens
            with open(self.tokens_file, "r") as f:
                tokens = json.load(f)
            
            has_session = bool(tokens.get("sessionId"))
            has_csrf = bool(tokens.get("csrfToken"))
            
            if has_session and has_csrf:
                return TestResult(
                    "Token Extraction",
                    True,
                    "✅ Tokens extracted successfully",
                    {
                        "sessionId": tokens["sessionId"][:20] + "...",
                        "csrfToken": tokens["csrfToken"][:20] + "...",
                        "localStorage_keys": len(tokens.get("localStorage", {})),
                        "cookies": len(tokens.get("cookies", []))
                    }
                )
            else:
                return TestResult(
                    "Token Extraction",
                    False,
                    f"❌ Tokens incomplete (session: {has_session}, csrf: {has_csrf})",
                    {"tokens": tokens}
                )
        else:
            return TestResult(
                "Token Extraction",
                False,
                "❌ Token extraction failed",
                result
            )
    
    def test_token_validation(self) -> TestResult:
        """Test 3: Validate extracted tokens."""
        print("\n🧪 Test 3: Token Validation")
        print("-" * 60)
        
        if not self.tokens_file.exists():
            return TestResult(
                "Token Validation",
                False,
                "❌ tokens.json not found"
            )
        
        try:
            with open(self.tokens_file, "r") as f:
                tokens = json.load(f)
            
            session_id = tokens.get("sessionId")
            csrf_token = tokens.get("csrfToken")
            
            if not session_id or not csrf_token:
                return TestResult(
                    "Token Validation",
                    False,
                    "❌ Missing sessionId or csrfToken"
                )
            
            # Check token format
            issues = []
            
            if len(session_id) < 10:
                issues.append("sessionId too short")
            
            if len(csrf_token) < 10:
                issues.append("csrfToken too short")
            
            if issues:
                return TestResult(
                    "Token Validation",
                    False,
                    f"❌ Token format issues: {', '.join(issues)}",
                    {"issues": issues}
                )
            
            return TestResult(
                "Token Validation",
                True,
                "✅ Tokens format valid",
                {
                    "sessionId_length": len(session_id),
                    "csrfToken_length": len(csrf_token)
                }
            )
        
        except Exception as e:
            return TestResult(
                "Token Validation",
                False,
                f"❌ Token validation error: {e}"
            )
    
    def test_start_cascade_auth(self) -> TestResult:
        """Test 4: Test StartCascade with captured tokens."""
        print("\n🧪 Test 4: StartCascade Authentication")
        print("-" * 60)
        
        cmd = [
            sys.executable,
            str(self.scripts_dir / "windsurf_authenticated_probe.py"),
            "--tokens", str(self.tokens_file),
            "--test-start-cascade"
        ]
        
        result = self.run_command(cmd, timeout=15)
        
        if result["success"]:
            # Parse output for status
            stdout = result["stdout"]
            
            if "✅ AUTHENTICATION SUCCESSFUL" in stdout:
                return TestResult(
                    "StartCascade Auth",
                    True,
                    "✅ StartCascade authentication successful",
                    {"stdout": stdout[:500]}
                )
            elif "Status: 200" in stdout:
                return TestResult(
                    "StartCascade Auth",
                    True,
                    "✅ StartCascade returned 200",
                    {"stdout": stdout[:500]}
                )
            else:
                return TestResult(
                    "StartCascade Auth",
                    False,
                    "❌ StartCascade auth unclear",
                    {"stdout": stdout[:500]}
                )
        else:
            return TestResult(
                "StartCascade Auth",
                False,
                "❌ StartCascade test failed",
                result
            )
    
    def test_direct_probe_integration(self) -> TestResult:
        """Test 5: Test integration with windsurf_direct_probe.py."""
        print("\n🧪 Test 5: Direct Probe Integration")
        print("-" * 60)
        
        cmd = [
            sys.executable,
            str(self.scripts_dir / "windsurf_authenticated_probe.py"),
            "--tokens", str(self.tokens_file),
            "--use-direct-probe"
        ]
        
        result = self.run_command(cmd, timeout=30)
        
        if result["success"]:
            stdout = result["stdout"]
            
            if "✅ PROBE SUCCESSFUL" in stdout:
                return TestResult(
                    "Direct Probe Integration",
                    True,
                    "✅ Direct probe integration successful",
                    {"stdout": stdout[:500]}
                )
            else:
                return TestResult(
                    "Direct Probe Integration",
                    False,
                    "❌ Direct probe integration unclear",
                    {"stdout": stdout[:500]}
                )
        else:
            return TestResult(
                "Direct Probe Integration",
                False,
                "❌ Direct probe integration failed",
                result
            )
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        print("=" * 70)
        print("🚀 WINDSURF AUTHENTICATION TEST SUITE")
        print("=" * 70)
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Scripts dir: {self.scripts_dir}")
        print(f"Tokens file: {self.tokens_file}")
        
        # Test 1: CDP Availability
        result = self.test_cdp_availability()
        self.results.append(result)
        print(f"\n{result.message}")
        
        if not result.success:
            print("\n⚠️  CDP not available. Please start Windsurf with:")
            print('   & "C:\\Users\\amine\\AppData\\Local\\Programs\\Windsurf\\Windsurf.exe" --remote-debugging-port=9222')
            return
        
        # Test 2: Token Extraction
        result = self.test_token_extraction()
        self.results.append(result)
        print(f"\n{result.message}")
        
        if not result.success and not result.details.get("skipped"):
            print("\n⚠️  Token extraction failed. Check if Windsurf is running and Cascade is active.")
            return
        
        # Test 3: Token Validation
        result = self.test_token_validation()
        self.results.append(result)
        print(f"\n{result.message}")
        
        if not result.success:
            print("\n⚠️  Token validation failed. Tokens may be incomplete or invalid.")
            return
        
        # Test 4: StartCascade Auth
        result = self.test_start_cascade_auth()
        self.results.append(result)
        print(f"\n{result.message}")
        
        # Test 5: Direct Probe Integration
        result = self.test_direct_probe_integration()
        self.results.append(result)
        print(f"\n{result.message}")
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for r in self.results if r.success)
        total = len(self.results)
        
        print(f"\nTotal: {total} tests")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {total - passed} ❌")
        print(f"Success rate: {passed / total * 100:.1f}%")
        
        print("\n" + "-" * 70)
        print("DETAILED RESULTS")
        print("-" * 70)
        
        for i, result in enumerate(self.results, 1):
            status = "✅" if result.success else "❌"
            print(f"\n{i}. {result.name}: {status}")
            print(f"   {result.message}")
            
            if result.details and not result.success:
                print(f"   Details: {json.dumps(result.details, indent=6)[:200]}...")
        
        print("\n" + "=" * 70)
        
        if passed == total:
            print("🎉 ALL TESTS PASSED!")
            print("\n✅ Authentication flow is working correctly.")
            print("✅ You can now use captured tokens to call the LS.")
        else:
            print("⚠️  SOME TESTS FAILED")
            print("\n💡 Next steps:")
            print("   1. Check that Windsurf is running with --remote-debugging-port=9222")
            print("   2. Open Cascade panel and send a message")
            print("   3. Re-run the test suite")


def main():
    parser = argparse.ArgumentParser(description="Windsurf Auth Test Suite")
    parser.add_argument("--skip-extraction", action="store_true", help="Skip token extraction (use existing tokens.json)")
    
    args = parser.parse_args()
    
    suite = WindsurfAuthTestSuite(skip_extraction=args.skip_extraction)
    suite.run_all_tests()
    
    # Exit code based on results
    passed = sum(1 for r in suite.results if r.success)
    total = len(suite.results)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
