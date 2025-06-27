import json
import re
import subprocess
from pathlib import Path
from typing import List, Union, Dict, Any
from . import accumulator

COMMENT_PATTERNS = {
    '.py': ['#'], '.sh': ['#'], '.js': ['//'], '.ts': ['//'], '.java': ['//'], '.c': ['//'], 
    '.cpp': ['//'], '.h': ['//'], '.hpp': ['//'], '.go': ['//'], '.rs': ['//'], '.swift': ['//'],
    '.kt': ['//'], '.php': ['//', '#'], '.rb': ['#'], '.pl': ['#'], '.lua': ['--'], '.sql': ['--']
}

MULTI_LINE_COMMENT_DELIMITERS = {
    '.c': ('/*', '*/'), '.cpp': ('/*', '*/'), '.h': ('/*', '*/'), '.hpp': ('/*', '*/'),
    '.java': ('/*', '*/'), '.js': ('/*', '*/'), '.ts': ('/*', '*/'), '.go': ('/*', '*/'),
    '.cs': ('/*', '*/'), '.swift': ('/*', '*/'), '.php': ('/*', '*/'), '.rs': ('/*', '*/'),
    '.sql': ('/*', '*/'),
    '.py': [('"""', '"""'), ("'''", "'''")]
}

def save_code_to_beecode(relative_path: Path, code_content: str):
    """Saves code to a specific path inside the .beecode.d directory."""
    prefix_dir = "beecode.d"
    project_dir = accumulator.get_project_root()
    
    # Construct the full path for saving the file
    full_save_path = project_dir / prefix_dir / relative_path
    
    # Create the parent directory if it doesn't exist
    full_save_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the code to the file
    full_save_path.write_text(code_content, encoding='utf-8')
    print(f"\n🎉 Successfully Created: {full_save_path}")

def accumulate_code(file_paths: List[Path], scrub_comments: bool) -> str:
    """Accumulates code from multiple files, optionally scrubbing comments."""
    code_accumulation = []
    print(f"📚 Accumulating code from {len(file_paths)} file(s)...")
    
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                code_accumulation.append(f"\n--- FILE: {file_path.as_posix()} ---\n")
                
                if scrub_comments:
                    file_ext = file_path.suffix.lower()
                    
                    # Handle multi-line comments
                    ml_delims = MULTI_LINE_COMMENT_DELIMITERS.get(file_ext)
                    if ml_delims:
                        delimiter_pairs = ml_delims if isinstance(ml_delims, list) else [ml_delims]
                        for start_delim, end_delim in delimiter_pairs:
                            while True:
                                start_idx = content.find(start_delim)
                                if start_idx == -1:
                                    break
                                end_idx = content.find(end_delim, start_idx + len(start_delim))
                                if end_idx == -1:
                                    break 
                                content = content[:start_idx] + content[end_idx + len(end_delim):]

                    # Handle single-line comments
                    sl_markers = COMMENT_PATTERNS.get(file_ext, [])
                    if sl_markers:
                        lines = content.split('\n')
                        uncommented_lines = []
                        for line in lines:
                            stripped_line = line.strip()
                            if any(stripped_line.startswith(marker) for marker in sl_markers):
                                continue
                            uncommented_lines.append(line)
                        content = "\n".join(uncommented_lines)

                code_accumulation.append(content)
        except Exception as e:
            print(f"⚠️ Warning: Could not read file {file_path}: {e}")

    return "".join(code_accumulation)

# def apply_patch(patch_content: str, root: Path) -> subprocess.CompletedProcess:
#     """Applies a git patch to the codebase."""
#     print("Applying patch...")
#     return subprocess.run(
#         ['git', 'apply', '--ignore-whitespace'],
#         input=patch_content, text=True, cwd=root,
#         capture_output=True
#     )

# def revert_patch(root: Path):
#     """Reverts all changes in the git repository."""
#     print("⚠️ Reverting changes...")
#     subprocess.run(['git', 'checkout', '--', '.'], cwd=root, check=True)
#     subprocess.run(['git', 'clean', '-fd'], cwd=root, check=True)