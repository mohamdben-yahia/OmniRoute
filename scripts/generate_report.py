#!/usr/bin/env python3
"""
Windsurf Authentication Toolkit — Report Generator

Generate a comprehensive report of all toolkit files with statistics.

Usage:
    python generate_report.py
    python generate_report.py --output report.txt
    python generate_report.py --format markdown

Author: OmniRoute Research Team
Date: 2026-05-02
Version: 1.0.0
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# ANSI color codes
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def get_file_stats(file_path: Path) -> Dict:
    """Get statistics for a file."""
    stats = file_path.stat()
    return {
        "size": stats.st_size,
        "modified": datetime.fromtimestamp(stats.st_mtime),
        "created": datetime.fromtimestamp(stats.st_ctime),
    }


def count_lines(file_path: Path) -> int:
    """Count lines in a text file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return len(f.readlines())
    except:
        return 0


def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def generate_report(output_file: str = None, format_type: str = "text") -> None:
    """Generate comprehensive toolkit report."""
    script_dir = Path(__file__).parent.absolute()
    
    # File categories
    categories = {
        "Python Scripts": [
            "windsurf_quick_start.py",
            "windsurf_token_extractor.py",
            "windsurf_authenticated_probe.py",
            "windsurf_auth_test_suite.py",
            "windsurf_cdp_inject.py",
            "windsurf_direct_probe.py",
            "runtime_ls_state.py",
            "verify_setup.py",
            "cleanup.py",
            "validate_toolkit.py",
            "generate_report.py",
        ],
        "Documentation": [
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
            "PROJECT_COMPLETE.md",
            "FILE_NAVIGATOR.md",
            "README_GITHUB.md",
            "PROJECT_CLOSURE.md",
        ],
        "Configuration": [
            "requirements.txt",
            ".gitignore",
            "QUICK_REFERENCE.txt",
            "launch_windsurf_with_cdp.ps1",
            "quick_start.ps1",
        ],
    }
    
    # Collect statistics
    report_lines = []
    total_files = 0
    total_size = 0
    total_lines = 0
    category_stats = {}
    
    # Header
    if format_type == "markdown":
        report_lines.append("# Windsurf Authentication Toolkit — File Report")
        report_lines.append("")
        report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d at %H:%M:%S UTC')}")
        report_lines.append(f"**Location:** `{script_dir}`")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
    else:
        report_lines.append("=" * 80)
        report_lines.append("WINDSURF AUTHENTICATION TOOLKIT — FILE REPORT".center(80))
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S UTC')}")
        report_lines.append(f"Location: {script_dir}")
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("")
    
    # Process each category
    for category, files in categories.items():
        category_size = 0
        category_lines = 0
        category_count = 0
        
        if format_type == "markdown":
            report_lines.append(f"## {category}")
            report_lines.append("")
            report_lines.append("| # | File | Size | Lines | Modified |")
            report_lines.append("|---|------|------|-------|----------|")
        else:
            report_lines.append(f"\n{category}")
            report_lines.append("-" * 80)
        
        for idx, file_name in enumerate(files, 1):
            file_path = script_dir / file_name
            
            if file_path.exists():
                stats = get_file_stats(file_path)
                lines = count_lines(file_path)
                
                category_size += stats["size"]
                category_lines += lines
                category_count += 1
                total_files += 1
                total_size += stats["size"]
                total_lines += lines
                
                if format_type == "markdown":
                    report_lines.append(
                        f"| {idx} | `{file_name}` | {format_size(stats['size'])} | "
                        f"{lines:,} | {stats['modified'].strftime('%Y-%m-%d %H:%M')} |"
                    )
                else:
                    report_lines.append(
                        f"{idx:2}. {file_name:45} {format_size(stats['size']):>10} "
                        f"{lines:>7,} lines  {stats['modified'].strftime('%Y-%m-%d')}"
                    )
            else:
                if format_type == "markdown":
                    report_lines.append(f"| {idx} | `{file_name}` | ❌ Not found | - | - |")
                else:
                    report_lines.append(f"{idx:2}. {file_name:45} ❌ NOT FOUND")
        
        category_stats[category] = {
            "count": category_count,
            "size": category_size,
            "lines": category_lines,
        }
        
        if format_type == "markdown":
            report_lines.append("")
            report_lines.append(f"**Subtotal:** {category_count} files | "
                              f"{format_size(category_size)} | {category_lines:,} lines")
            report_lines.append("")
        else:
            report_lines.append("")
            report_lines.append(
                f"Subtotal: {category_count} files | {format_size(category_size)} | "
                f"{category_lines:,} lines"
            )
            report_lines.append("")
    
    # Summary
    if format_type == "markdown":
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("## Summary")
        report_lines.append("")
        report_lines.append("| Category | Files | Total Size | Total Lines |")
        report_lines.append("|----------|-------|------------|-------------|")
        for category, stats in category_stats.items():
            report_lines.append(
                f"| {category} | {stats['count']} | {format_size(stats['size'])} | "
                f"{stats['lines']:,} |"
            )
        report_lines.append(f"| **TOTAL** | **{total_files}** | "
                          f"**{format_size(total_size)}** | **{total_lines:,}** |")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("## Statistics")
        report_lines.append("")
        report_lines.append(f"- **Total Files:** {total_files}")
        report_lines.append(f"- **Total Size:** {format_size(total_size)}")
        report_lines.append(f"- **Total Lines:** {total_lines:,}")
        report_lines.append(f"- **Average File Size:** {format_size(total_size // total_files)}")
        report_lines.append(f"- **Average Lines per File:** {total_lines // total_files:,}")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("© 2026 OmniRoute Research Team — Licensed under MIT")
    else:
        report_lines.append("=" * 80)
        report_lines.append("SUMMARY".center(80))
        report_lines.append("=" * 80)
        report_lines.append("")
        for category, stats in category_stats.items():
            report_lines.append(
                f"{category:30} {stats['count']:>3} files  {format_size(stats['size']):>10}  "
                f"{stats['lines']:>7,} lines"
            )
        report_lines.append("-" * 80)
        report_lines.append(
            f"{'TOTAL':30} {total_files:>3} files  {format_size(total_size):>10}  "
            f"{total_lines:>7,} lines"
        )
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append(f"Average file size: {format_size(total_size // total_files)}")
        report_lines.append(f"Average lines per file: {total_lines // total_files:,}")
        report_lines.append("")
        report_lines.append("=" * 80)
    
    # Output
    report_text = "\n".join(report_lines)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"{GREEN}✅ Report saved to: {output_file}{RESET}")
    else:
        print(report_text)


def main() -> int:
    """Main function."""
    output_file = None
    format_type = "text"
    
    # Parse arguments
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]
    
    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            format_type = sys.argv[idx + 1]
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python generate_report.py [options]")
        print("")
        print("Options:")
        print("  --output FILE    Save report to file")
        print("  --format TYPE    Output format (text or markdown)")
        print("  --help, -h       Show this help message")
        print("")
        print("Examples:")
        print("  python generate_report.py")
        print("  python generate_report.py --output report.txt")
        print("  python generate_report.py --format markdown --output REPORT.md")
        return 0
    
    generate_report(output_file, format_type)
    return 0


if __name__ == "__main__":
    sys.exit(main())
