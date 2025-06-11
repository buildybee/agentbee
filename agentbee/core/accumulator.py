import os
import subprocess
from pathlib import Path
from typing import List, Optional

def get_project_root() -> Path:
    """Finds the project root by looking for a .git directory."""
    try:
        # This command asks git for the top-level directory of the current repository.
        result = subprocess.run(           
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("🚨 Error: Not a git repository or git is not installed. Cannot determine project root.")
        # Re-raise the exception to be caught by the main command handler.
        raise

def read_bee_include(root: Path) -> List[str]:
    """Reads patterns from the .beeinclude file in the project root."""
    include_file = root / ".beeinclude"
    if not include_file.exists():
        return []
    with open(include_file, 'r') as f:
        # Read lines, strip whitespace, and ignore empty lines or comments.
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def filter_paths_with_patterns(paths: List[Path], patterns: List[str], root: Path) -> List[Path]:
    """
    Filters a list of file paths to only include those matching the given patterns.
    Note: This uses basic `pathlib.Path.match`. For full .gitignore style, a library
    like 'pathspec' would be needed, but this is sufficient for simple cases.
    """
    if not patterns:
        return paths  # If no patterns are provided, return the original list.
    
    absolute_patterns = [root / p for p in patterns]
    filtered = []
    for path in paths:
        # Check if the path matches any of the provided patterns.
        # Ensure the patterns are relative to the root when matching
        if any(path.match(str((root / p).resolve().relative_to(root.resolve()))) for p in patterns):
            filtered.append(path)
    return filtered

def get_file_paths(root: Path, path_option: Optional[Path]) -> List[Path]:
    """
    Gets a list of file paths to accumulate, using 'git ls-files' by default,
    or scanning a specified path as an override. Also applies .beeinclude filters.
    """
    if path_option:
        # User provided a specific relative path to scan.
        scan_path = root / path_option
        if not scan_path.exists():
            raise FileNotFoundError(f"Provided path '{scan_path}' does not exist.")
        if scan_path.is_file():
            return [scan_path]
        # Recursively find all files in the given directory.
        return [p for p in scan_path.rglob('*') if p.is_file()]

    # Default behavior: use 'git ls-files'.
    try:
        result = subprocess.run(
            ['git', 'ls-files'],
            capture_output=True, text=True, check=True, cwd=root
        )
        # Get a list of relative paths from git and make them absolute.
        paths = [root / p for p in result.stdout.strip().split('\n')]
        
        # Check for and apply filters from a .beeinclude file.
        include_patterns = read_bee_include(root)
        if include_patterns:
            print(f"🔎 Filtering files using .beeinclude patterns...")
            paths = filter_paths_with_patterns(paths, include_patterns, root)

        return paths
    except FileNotFoundError:
        print("🚨 Error: 'git' command not found. Please install git or use the --path option.")
        raise
    except subprocess.CalledProcessError:
        print("🚨 Error: This does not appear to be a git repository. Please use the --path option.")
        raise
