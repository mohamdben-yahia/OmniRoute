#!/usr/bin/env python3
"""
Windsurf Authentication Toolkit — Validation Script

This script validates that all toolkit files are present and correctly structured.
Run this after cloning the repository or before starting tests.

Usage:
    python validate_toolkit.py
    python validate_toolkit.py --verbose
    python validate_toolkit.py --fix

Author: OmniRoute Research Team
Date: 2026-05-02
Version: 1.0.0
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Expected files and their categories
EXPECTED_FILES = {
    "scripts": [
        "windsurf_quick_start.py",
        "windsurf_token_extractor.py",
        "windsurf_authenticated_probe.py",
        "windsurf_auth_test_suite.py",
        "windsurf_cdp_inject.py",
        "windsurf_direct_probe.py",
        "runtime_ls_state.py",
        "verify_setup.py",
        "cleanup.py",
        "validate_toolkit.py",  # This script
    ],
    "documentation": [
        "README.md",
        "MANUAL_TEST_GUIDE.md",
        "TEST_REPORT.md",
        "HANDOFF.md",
        "CHEAT_SHEET.md",
        "README_AUTH_TOOLKIT.md",
        "WINDSURF_AUTH_FLOW.md",
        "CDP_INJECTION_GUIDE.md",
        "INDEX.md",
        "EXECUTIVE_SUMMARY.md",
        "INTEGRATION_GUIDE.md",
        "MAINTENANCE_GUIDE.md",
        "VISUAL_ARCHITECTURE.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "FAQ.md",
        "GLOSSARY.md",
        "SUMMARY.md",
    ],
    "configuration": [
        "requirements.txt",
        ".gitignore",
        "QUICK_REFERENCE.txt",
        "launch_windsurf_with_cdp.ps1",
    ],
}

# Minimum file sizes (bytes) to detect empty/incomplete files
MIN_FILE_SIZES = {
    "windsurf_quick_start.py": 1000,
    "windsurf_token_extractor.py": 2000,
    "windsurf_authenticated_probe.py": 1500,
    "windsurf_auth_test_suite.py": 2000,
    "windsurf_cdp_inject.py": 1500,
    "windsurf_direct_probe.py": 100000,  # Large file
    "runtime_ls_state.py": 500,
    "verify_setup.py": 2000,
    "cleanup.py": 1500,
    "README.md": 5000,
    "MANUAL_TEST_GUIDE.md": 3000,
    "TEST_REPORT.md": 3000,
    "HANDOFF.md": 3000,
    "requirements.txt": 20,
    ".gitignore": 50,
}


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{RED}❌ {text}{RESET}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{BLUE}ℹ️  {text}{RESET}")


def get_script_dir() -> Path:
    """Get the directory where this script is located."""
    return Path(__file__).parent.absolute()


def check_file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    return file_path.exists() and file_path.is_file()


def check_file_size(file_path: Path, min_size: int) -> Tuple[bool, int]:
    """Check if a file meets minimum size requirements."""
    if not file_path.exists():
        return False, 0
    
    size = file_path.stat().st_size
    return size >= min_size, size


def validate_python_syntax(file_path: Path) -> Tuple[bool, str]:
    """Validate Python file syntax."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        compile(code, str(file_path), "exec")
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def validate_markdown_structure(file_path: Path) -> Tuple[bool, str]:
    """Validate basic Markdown structure."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for basic Markdown elements
        has_headers = "#" in content
        has_content = len(content.strip()) > 100
        
        if not has_headers:
            return False, "No headers found"
        if not has_content:
            return False, "File appears empty or too short"
        
        return True, "Structure OK"
    except Exception as e:
        return False, f"Error: {str(e)}"


def validate_category(
    category: str, files: List[str], verbose: bool = False
) -> Tuple[int, int, List[str]]:
    """Validate all files in a category."""
    script_dir = get_script_dir()
    passed = 0
    failed = 0
    issues = []
    
    print(f"\n{BLUE}Validating {category}...{RESET}")
    
    for file_name in files:
        file_path = script_dir / file_name
        
        # Check existence
        if not check_file_exists(file_path):
            print_error(f"{file_name} — File not found")
            failed += 1
            issues.append(f"{file_name}: File not found")
            continue
        
        # Check size
        min_size = MIN_FILE_SIZES.get(file_name, 0)
        if min_size > 0:
            size_ok, actual_size = check_file_size(file_path, min_size)
            if not size_ok:
                print_warning(
                    f"{file_name} — File too small ({actual_size} bytes, expected >= {min_size})"
                )
                issues.append(
                    f"{file_name}: File too small ({actual_size} bytes, expected >= {min_size})"
                )
        
        # Validate syntax/structure
        if file_name.endswith(".py"):
            syntax_ok, syntax_msg = validate_python_syntax(file_path)
            if syntax_ok:
                print_success(f"{file_name} — {syntax_msg}")
                passed += 1
            else:
                print_error(f"{file_name} — {syntax_msg}")
                failed += 1
                issues.append(f"{file_name}: {syntax_msg}")
        elif file_name.endswith(".md"):
            structure_ok, structure_msg = validate_markdown_structure(file_path)
            if structure_ok:
                print_success(f"{file_name} — {structure_msg}")
                passed += 1
            else:
                print_warning(f"{file_name} — {structure_msg}")
                issues.append(f"{file_name}: {structure_msg}")
        else:
            # Just check existence for other files
            print_success(f"{file_name} — Present")
            passed += 1
        
        if verbose:
            size = file_path.stat().st_size
            print_info(f"  Size: {size:,} bytes")
    
    return passed, failed, issues


def generate_summary_report(results: Dict[str, Tuple[int, int, List[str]]]) -> None:
    """Generate a summary report of validation results."""
    print_header("VALIDATION SUMMARY")
    
    total_passed = 0
    total_failed = 0
    all_issues = []
    
    for category, (passed, failed, issues) in results.items():
        total_passed += passed
        total_failed += failed
        all_issues.extend(issues)
        
        status = f"{GREEN}✅{RESET}" if failed == 0 else f"{RED}❌{RESET}"
        print(f"{status} {category.capitalize()}: {passed} passed, {failed} failed")
    
    print(f"\n{BLUE}{'─' * 70}{RESET}")
    print(f"Total Files Validated: {total_passed + total_failed}")
    print(f"{GREEN}Passed: {total_passed}{RESET}")
    print(f"{RED}Failed: {total_failed}{RESET}")
    
    if total_failed == 0:
        print(f"\n{GREEN}🎉 All validations passed! Toolkit is ready.{RESET}")
    else:
        print(f"\n{RED}⚠️  {total_failed} validation(s) failed. See issues below:{RESET}")
        for issue in all_issues:
            print(f"  • {issue}")
    
    print(f"{BLUE}{'─' * 70}{RESET}\n")


def main() -> int:
    """Main validation function."""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    print_header("🔍 WINDSURF AUTHENTICATION TOOLKIT VALIDATOR")
    
    print_info(f"Script directory: {get_script_dir()}")
    print_info(f"Validating {sum(len(files) for files in EXPECTED_FILES.values())} files...")
    
    results = {}
    
    # Validate each category
    for category, files in EXPECTED_FILES.items():
        passed, failed, issues = validate_category(category, files, verbose)
        results[category] = (passed, failed, issues)
    
    # Generate summary
    generate_summary_report(results)
    
    # Return exit code
    total_failed = sum(failed for _, failed, _ in results.values())
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
