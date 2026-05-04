#!/usr/bin/env python3
"""
Windsurf Authentication Toolkit — Cleanup Script

This script cleans up temporary files, tokens, and cached data
from the Windsurf Authentication Toolkit.

Usage:
    python cleanup.py                    # Interactive mode
    python cleanup.py --all              # Clean everything
    python cleanup.py --tokens           # Clean tokens only
    python cleanup.py --cache            # Clean cache only
    python cleanup.py --logs             # Clean logs only
    python cleanup.py --dry-run          # Show what would be deleted

Author: OmniRoute Research Team
Version: 1.0.0
Last Updated: 2026-05-02
"""

import sys
import os
import shutil
from pathlib import Path
from typing import List, Set
import argparse

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def get_file_size(path: Path) -> int:
    """Get file size in bytes."""
    try:
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        return 0
    except Exception:
        return 0

def format_size(size: int) -> str:
    """Format size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def find_files_to_clean() -> dict:
    """Find all files that can be cleaned."""
    files = {
        'tokens': [],
        'cache': [],
        'logs': [],
        'temp': [],
        'pycache': []
    }
    
    # Token files
    for pattern in ['tokens.json', 'tokens_*.json', '*.tokens.json', 'session_*.json']:
        files['tokens'].extend(Path('.').glob(pattern))
    
    # Cache files
    for pattern in ['.cache', '*.cache', '__pycache__', '.pytest_cache', '.mypy_cache']:
        files['cache'].extend(Path('.').glob(pattern))
        files['cache'].extend(Path('.').rglob(pattern))
    
    # Log files
    for pattern in ['*.log', '*.log.*', 'logs']:
        files['logs'].extend(Path('.').glob(pattern))
        files['logs'].extend(Path('.').rglob(pattern))
    
    # Temp files
    for pattern in ['*.tmp', '*.temp', '*.bak', '*.backup', 'tmp', 'temp']:
        files['temp'].extend(Path('.').glob(pattern))
    
    # Python cache
    files['pycache'].extend(Path('.').rglob('__pycache__'))
    files['pycache'].extend(Path('.').rglob('*.pyc'))
    files['pycache'].extend(Path('.').rglob('*.pyo'))
    
    # Remove duplicates and sort
    for category in files:
        files[category] = sorted(set(files[category]))
    
    return files

def delete_file(path: Path, dry_run: bool = False) -> bool:
    """Delete a file or directory."""
    try:
        if dry_run:
            return True
        
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        return True
    except Exception as e:
        print_error(f"Failed to delete {path}: {str(e)}")
        return False

def clean_category(category: str, files: List[Path], dry_run: bool = False) -> tuple:
    """Clean files in a category."""
    if not files:
        return 0, 0
    
    total_size = sum(get_file_size(f) for f in files)
    deleted_count = 0
    
    print_info(f"\nCleaning {category}...")
    for file in files:
        size = get_file_size(file)
        if dry_run:
            print_warning(f"Would delete: {file} ({format_size(size)})")
            deleted_count += 1
        else:
            if delete_file(file):
                print_success(f"Deleted: {file} ({format_size(size)})")
                deleted_count += 1
    
    return deleted_count, total_size

def interactive_clean(files: dict) -> None:
    """Interactive cleanup mode."""
    print_header("Interactive Cleanup Mode")
    print_info("Select categories to clean:")
    print()
    
    categories = {
        '1': ('tokens', 'Token files (tokens.json, session_*.json)'),
        '2': ('cache', 'Cache files (__pycache__, .cache, etc.)'),
        '3': ('logs', 'Log files (*.log)'),
        '4': ('temp', 'Temporary files (*.tmp, *.bak)'),
        '5': ('pycache', 'Python cache files (*.pyc, *.pyo)'),
        'a': ('all', 'All of the above')
    }
    
    for key, (cat, desc) in categories.items():
        if cat == 'all':
            count = sum(len(files[c]) for c in files)
        else:
            count = len(files[cat])
        print(f"  {key}. {desc} ({count} items)")
    
    print()
    choice = input("Enter your choice (1-5, a, or q to quit): ").strip().lower()
    
    if choice == 'q':
        print_info("Cleanup cancelled.")
        return
    
    if choice == 'a':
        categories_to_clean = list(files.keys())
    elif choice in categories and categories[choice][0] != 'all':
        categories_to_clean = [categories[choice][0]]
    else:
        print_error("Invalid choice.")
        return
    
    # Confirm
    total_files = sum(len(files[cat]) for cat in categories_to_clean)
    total_size = sum(sum(get_file_size(f) for f in files[cat]) for cat in categories_to_clean)
    
    print()
    print_warning(f"This will delete {total_files} items ({format_size(total_size)})")
    confirm = input("Are you sure? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print_info("Cleanup cancelled.")
        return
    
    # Clean
    total_deleted = 0
    total_size_deleted = 0
    
    for category in categories_to_clean:
        deleted, size = clean_category(category, files[category])
        total_deleted += deleted
        total_size_deleted += size
    
    print()
    print_success(f"Cleanup complete! Deleted {total_deleted} items ({format_size(total_size_deleted)})")

def main():
    """Main cleanup function."""
    parser = argparse.ArgumentParser(
        description='Clean up temporary files and tokens from Windsurf Authentication Toolkit'
    )
    parser.add_argument('--all', action='store_true', help='Clean everything')
    parser.add_argument('--tokens', action='store_true', help='Clean tokens only')
    parser.add_argument('--cache', action='store_true', help='Clean cache only')
    parser.add_argument('--logs', action='store_true', help='Clean logs only')
    parser.add_argument('--temp', action='store_true', help='Clean temp files only')
    parser.add_argument('--pycache', action='store_true', help='Clean Python cache only')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted')
    
    args = parser.parse_args()
    
    print_header("Windsurf Authentication Toolkit — Cleanup")
    
    # Find files
    print_info("Scanning for files to clean...")
    files = find_files_to_clean()
    
    total_files = sum(len(files[cat]) for cat in files)
    total_size = sum(sum(get_file_size(f) for f in files[cat]) for cat in files)
    
    print_info(f"Found {total_files} items ({format_size(total_size)})")
    
    # Determine what to clean
    if args.all:
        categories_to_clean = list(files.keys())
    elif any([args.tokens, args.cache, args.logs, args.temp, args.pycache]):
        categories_to_clean = []
        if args.tokens:
            categories_to_clean.append('tokens')
        if args.cache:
            categories_to_clean.append('cache')
        if args.logs:
            categories_to_clean.append('logs')
        if args.temp:
            categories_to_clean.append('temp')
        if args.pycache:
            categories_to_clean.append('pycache')
    else:
        # Interactive mode
        interactive_clean(files)
        return
    
    # Clean selected categories
    if args.dry_run:
        print_warning("\nDRY RUN MODE — No files will be deleted")
    
    total_deleted = 0
    total_size_deleted = 0
    
    for category in categories_to_clean:
        deleted, size = clean_category(category, files[category], args.dry_run)
        total_deleted += deleted
        total_size_deleted += size
    
    # Summary
    print_header("Cleanup Summary")
    
    if args.dry_run:
        print_warning(f"Would delete {total_deleted} items ({format_size(total_size_deleted)})")
        print_info("\nRun without --dry-run to actually delete files")
    else:
        print_success(f"Deleted {total_deleted} items ({format_size(total_size_deleted)})")
    
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Cleanup cancelled by user.{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
